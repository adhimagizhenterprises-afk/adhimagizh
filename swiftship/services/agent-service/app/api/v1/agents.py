"""
Agent CRUD and pickup task endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.agent import Agent, AgentStatus, PickupTask
from app.core.auth import require_ops, require_agent, get_current_user

router = APIRouter()


@router.get("/me")
async def get_my_profile(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_agent),
):
    result = await db.execute(select(Agent).where(Agent.user_id == current_user["user_id"]))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent profile not found")
    return agent


@router.get("/")
async def list_agents(
    hub_code: Optional[str] = None,
    status: Optional[AgentStatus] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_ops),
):
    query = select(Agent).where(Agent.is_active == True)
    if hub_code:
        query = query.where(Agent.hub_code == hub_code)
    if status:
        query = query.where(Agent.status == status)
    result = await db.execute(query)
    return result.scalars().all()


# ─── Pickups router (also in this file for brevity) ───────────────────────────
pickup_router = APIRouter()


@pickup_router.get("/my-tasks")
async def get_pickup_tasks(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_agent),
):
    agent_result = await db.execute(
        select(Agent).where(Agent.user_id == current_user["user_id"])
    )
    agent = agent_result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    result = await db.execute(
        select(PickupTask).where(
            PickupTask.agent_id == agent.id,
            PickupTask.status.in_(["ASSIGNED", "EN_ROUTE", "REACHED"]),
        )
    )
    return result.scalars().all()


@pickup_router.post("/{awb_number}/complete")
async def complete_pickup(
    awb_number: str,
    weight_kg: float,
    package_count: int = 1,
    remarks: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_agent),
):
    """Mark pickup as completed — package handed over to agent."""
    from datetime import datetime
    import uuid
    from app.core.kafka_producer import kafka_producer
    from shared.events.schemas import ShipmentStatusEvent, EventType

    agent_result = await db.execute(
        select(Agent).where(Agent.user_id == current_user["user_id"])
    )
    agent = agent_result.scalar_one_or_none()

    task_result = await db.execute(
        select(PickupTask).where(
            PickupTask.awb_number == awb_number,
            PickupTask.agent_id == agent.id,
        )
    )
    task = task_result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Pickup task not found")

    task.status = "PICKED_UP"
    task.picked_up_at = datetime.utcnow()
    task.weight_kg = weight_kg
    task.package_count = package_count
    task.remarks = remarks
    agent.total_pickups = (agent.total_pickups or 0) + 1
    await db.commit()

    await kafka_producer.publish(
        topic="shipment.picked_up",
        event=ShipmentStatusEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.SHIPMENT_PICKED_UP,
            timestamp=datetime.utcnow(),
            service_name="agent-service",
            awb_number=awb_number,
            status="PICKED_UP",
            location=task.pickup_city,
            agent_id=str(agent.id),
        ).model_dump(),
        key=awb_number,
    )

    return {"message": "Pickup completed", "awb_number": awb_number}
