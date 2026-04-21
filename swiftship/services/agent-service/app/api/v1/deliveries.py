"""
Delivery & POD API endpoints for agents
"""
from typing import List, Optional
from datetime import datetime
import uuid
import base64

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.db.session import get_db
from app.models.agent import DeliveryTask, ProofOfDelivery, Agent
from app.schemas.delivery import (
    DeliveryTaskResponse,
    DeliveryAttemptRequest,
    PODSubmitRequest,
    PODResponse,
)
from app.core.auth import get_current_user, require_role
from app.core.kafka_producer import kafka_producer
from app.services.storage_service import StorageService
from app.services.otp_service import OTPService
from shared.events.schemas import DeliveryEvent, ShipmentStatusEvent, EventType

router = APIRouter()


@router.get("/my-tasks", response_model=List[DeliveryTaskResponse])
async def get_my_delivery_tasks(
    date: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get all delivery tasks assigned to the current agent for a given date."""
    agent_result = await db.execute(
        select(Agent).where(Agent.user_id == current_user["user_id"])
    )
    agent = agent_result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent profile not found")

    query = select(DeliveryTask).where(
        DeliveryTask.agent_id == agent.id,
        DeliveryTask.status.in_(["ASSIGNED", "EN_ROUTE", "REACHED", "ATTEMPTED"]),
    ).order_by(DeliveryTask.sequence_number)

    result = await db.execute(query)
    return result.scalars().all()


@router.post("/{awb_number}/start")
async def start_delivery(
    awb_number: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Mark agent as en-route to delivery address."""
    task = await _get_agent_task(awb_number, current_user["user_id"], db)
    task.status = "EN_ROUTE"
    await db.commit()

    await kafka_producer.publish(
        topic="shipment.events",
        event=ShipmentStatusEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.SHIPMENT_OUT_FOR_DELIVERY,
            timestamp=datetime.utcnow(),
            service_name="agent-service",
            awb_number=awb_number,
            status="OUT_FOR_DELIVERY",
            location=f"En route - {task.delivery_city}",
            agent_id=str(task.agent_id),
        ).model_dump(),
    )
    return {"message": "Delivery started", "awb_number": awb_number}


@router.post("/{awb_number}/reached")
async def mark_reached(
    awb_number: str,
    latitude: float = Form(...),
    longitude: float = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Mark agent as reached the delivery address. Triggers OTP to receiver."""
    task = await _get_agent_task(awb_number, current_user["user_id"], db)
    task.status = "REACHED"
    task.delivery_latitude = latitude
    task.delivery_longitude = longitude

    # Generate and send OTP to receiver
    otp_service = OTPService()
    otp = await otp_service.generate_and_send(
        phone=task.receiver_phone,
        awb_number=awb_number,
    )
    task.otp = otp

    await db.commit()
    return {"message": "Reached marked, OTP sent to receiver", "awb_number": awb_number}


@router.post("/{awb_number}/attempt")
async def record_delivery_attempt(
    awb_number: str,
    request: DeliveryAttemptRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Record a delivery attempt (failed or otherwise)."""
    task = await _get_agent_task(awb_number, current_user["user_id"], db)
    task.attempt_count += 1
    task.last_attempt_result = request.result
    task.last_attempt_at = datetime.utcnow()
    task.status = "ATTEMPTED"

    if task.attempt_count >= 3:
        # Auto-initiate RTO after 3 failed attempts
        task.status = "RTO"
        background_tasks.add_task(
            kafka_producer.publish,
            topic="shipment.events",
            event=ShipmentStatusEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.SHIPMENT_RTO_INITIATED,
                timestamp=datetime.utcnow(),
                service_name="agent-service",
                awb_number=awb_number,
                status="RTO_INITIATED",
                location=task.delivery_city,
                remarks=f"Max attempts reached: {request.result}",
                agent_id=str(task.agent_id),
            ).model_dump(),
        )
    else:
        background_tasks.add_task(
            kafka_producer.publish,
            topic="shipment.events",
            event=ShipmentStatusEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.SHIPMENT_EXCEPTION,
                timestamp=datetime.utcnow(),
                service_name="agent-service",
                awb_number=awb_number,
                status="DELIVERY_ATTEMPTED",
                location=task.delivery_city,
                remarks=f"Attempt {task.attempt_count}: {request.result}",
                agent_id=str(task.agent_id),
            ).model_dump(),
        )

    await db.commit()
    return {
        "message": "Attempt recorded",
        "awb_number": awb_number,
        "attempt_number": task.attempt_count,
        "rto_initiated": task.status == "RTO",
    }


@router.post("/{awb_number}/deliver", response_model=PODResponse)
async def submit_pod_and_deliver(
    awb_number: str,
    delivered_to: str = Form(...),
    receiver_relation: str = Form(...),
    otp_entered: str = Form(...),
    cod_collected: bool = Form(False),
    cod_amount: float = Form(0),
    cod_method: str = Form("CASH"),
    package_photo: UploadFile = File(...),
    signature_photo: Optional[UploadFile] = File(None),
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Submit Proof of Delivery and mark shipment as delivered.
    Uploads photos to MinIO, publishes Kafka event.
    """
    task = await _get_agent_task(awb_number, current_user["user_id"], db)

    # Verify OTP
    if task.otp and task.otp != otp_entered:
        raise HTTPException(status_code=400, detail="Invalid OTP. Please verify with receiver.")

    # Upload photos to object storage
    storage = StorageService()
    photo_url = await storage.upload_pod_photo(
        awb_number=awb_number,
        file=package_photo,
        photo_type="package",
    )
    signature_url = None
    if signature_photo:
        signature_url = await storage.upload_pod_photo(
            awb_number=awb_number,
            file=signature_photo,
            photo_type="signature",
        )

    # Create POD record
    pod = ProofOfDelivery(
        awb_number=awb_number,
        delivery_task_id=task.id,
        agent_id=task.agent_id,
        delivered_to=delivered_to,
        receiver_relation=receiver_relation,
        delivery_latitude=task.delivery_latitude,
        delivery_longitude=task.delivery_longitude,
        photo_url=photo_url,
        signature_url=signature_url,
        otp_verified=bool(task.otp),
        cod_collected=cod_collected,
        cod_amount=cod_amount,
        cod_collection_method=cod_method,
        delivered_at=datetime.utcnow(),
    )
    db.add(pod)

    # Update delivery task
    task.status = "DELIVERED"
    task.delivered_at = datetime.utcnow()
    task.otp_verified = bool(task.otp)

    await db.commit()
    await db.refresh(pod)

    # Publish delivery event
    if background_tasks:
        background_tasks.add_task(
            kafka_producer.publish,
            topic="shipment.delivered",
            event=DeliveryEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.SHIPMENT_DELIVERED,
                timestamp=datetime.utcnow(),
                service_name="agent-service",
                awb_number=awb_number,
                agent_id=str(task.agent_id),
                delivered_to=delivered_to,
                delivery_time=task.delivered_at,
                pod_image_url=photo_url,
                signature_url=signature_url,
                otp_verified=bool(task.otp),
            ).model_dump(),
        )

    return pod


async def _get_agent_task(awb_number: str, user_id: str, db: AsyncSession) -> DeliveryTask:
    """Helper: fetch delivery task for agent, validate ownership."""
    agent_result = await db.execute(
        select(Agent).where(Agent.user_id == user_id)
    )
    agent = agent_result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent profile not found")

    task_result = await db.execute(
        select(DeliveryTask).where(
            DeliveryTask.awb_number == awb_number,
            DeliveryTask.agent_id == agent.id,
        )
    )
    task = task_result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Delivery task not found or not assigned to you")
    return task
