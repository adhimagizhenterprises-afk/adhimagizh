"""
Agent Location API — real-time GPS updates from agent app
"""
from datetime import datetime
import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.db.session import get_db
from app.models.agent import Agent, AgentLocationHistory
from app.core.auth import require_agent
from app.core.kafka_producer import kafka_producer
from shared.events.schemas import AgentLocationEvent, EventType

router = APIRouter()


@router.post("/update")
async def update_location(
    latitude: float,
    longitude: float,
    accuracy_meters: float = None,
    awb_number: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_agent),
):
    """
    Called by agent mobile app every ~30 seconds while on duty.
    Updates agent's current location and publishes to Kafka for live tracking.
    """
    result = await db.execute(
        select(Agent).where(Agent.user_id == current_user["user_id"])
    )
    agent = result.scalar_one_or_none()
    if not agent:
        return {"error": "Agent not found"}

    # Update agent's current position
    agent.current_latitude = latitude
    agent.current_longitude = longitude
    agent.last_location_update = datetime.utcnow()

    # Log to history
    history = AgentLocationHistory(
        agent_id=agent.id,
        latitude=latitude,
        longitude=longitude,
        accuracy_meters=accuracy_meters,
        awb_number=awb_number,
        recorded_at=datetime.utcnow(),
    )
    db.add(history)
    await db.commit()

    # Publish to Kafka (tracking service + customer-facing live map)
    await kafka_producer.publish(
        topic="agent.location.updated",
        event=AgentLocationEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.AGENT_LOCATION_UPDATED,
            timestamp=datetime.utcnow(),
            service_name="agent-service",
            agent_id=str(agent.id),
            latitude=latitude,
            longitude=longitude,
            awb_number=awb_number,
            accuracy_meters=accuracy_meters,
        ).model_dump(),
        key=str(agent.id),  # Partition by agent for ordering
    )

    return {"status": "ok", "recorded_at": datetime.utcnow().isoformat()}
