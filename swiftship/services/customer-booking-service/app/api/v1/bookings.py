"""
Booking API — v1 endpoints
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.session import get_db
from app.models.shipment import Shipment, ShipmentStatus
from app.schemas.booking import (
    BookingCreateRequest,
    BookingResponse,
    BulkBookingRequest,
    BookingListResponse,
    CancelBookingRequest,
)
from app.services.booking_service import BookingService
from app.services.pricing_service import PricingService
from app.core.auth import get_current_user, require_roles
from app.core.kafka_producer import kafka_producer
from shared.events.schemas import BookingCreatedEvent, EventType
from shared.utils.awb import generate_awb

router = APIRouter()


@router.post("/", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    request: BookingCreateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Create a new shipment booking.
    Generates AWB, calculates charges, schedules pickup.
    """
    service = BookingService(db)
    booking = await service.create_booking(request, current_user["user_id"])

    # Publish event to Kafka (async, non-blocking)
    background_tasks.add_task(
        kafka_producer.publish,
        topic="booking.created",
        event=BookingCreatedEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.BOOKING_CREATED,
            timestamp=datetime.utcnow(),
            service_name="customer-booking-service",
            awb_number=booking.awb_number,
            customer_id=current_user["user_id"],
            sender_name=booking.sender_name,
            sender_phone=booking.sender_phone,
            sender_city=booking.sender_city,
            receiver_name=booking.receiver_name,
            receiver_phone=booking.receiver_phone,
            receiver_city=booking.receiver_city,
            receiver_pincode=booking.receiver_pincode,
            weight_kg=booking.chargeable_weight_kg,
            service_type=booking.service_type,
            payment_mode=booking.payment_mode,
            amount=booking.total_charge,
            pickup_date=str(booking.pickup_date),
        ).model_dump(),
    )
    return booking


@router.get("/", response_model=BookingListResponse)
async def list_bookings(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List all bookings for the current customer."""
    query = select(Shipment).where(Shipment.customer_id == current_user["user_id"])

    if status:
        query = query.where(Shipment.status == status)
    if from_date:
        query = query.where(Shipment.created_at >= from_date)
    if to_date:
        query = query.where(Shipment.created_at <= to_date)

    query = query.order_by(Shipment.created_at.desc())
    count_query = select(func.count()).select_from(query.subquery())

    total = (await db.execute(count_query)).scalar()
    result = await db.execute(query.offset((page - 1) * page_size).limit(page_size))
    shipments = result.scalars().all()

    return BookingListResponse(
        items=shipments,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.get("/{awb_number}", response_model=BookingResponse)
async def get_booking(
    awb_number: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get booking details by AWB number."""
    result = await db.execute(
        select(Shipment).where(Shipment.awb_number == awb_number)
    )
    shipment = result.scalar_one_or_none()
    if not shipment:
        raise HTTPException(status_code=404, detail=f"Shipment {awb_number} not found")
    return shipment


@router.post("/{awb_number}/cancel")
async def cancel_booking(
    awb_number: str,
    request: CancelBookingRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Cancel a booking. Only allowed before pickup."""
    result = await db.execute(
        select(Shipment).where(
            Shipment.awb_number == awb_number,
            Shipment.customer_id == current_user["user_id"],
        )
    )
    shipment = result.scalar_one_or_none()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    if shipment.status not in [ShipmentStatus.BOOKING_CREATED, ShipmentStatus.PICKUP_SCHEDULED]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel shipment in status: {shipment.status}",
        )

    shipment.status = ShipmentStatus.CANCELLED
    shipment.updated_at = datetime.utcnow()
    await db.commit()
    return {"message": "Booking cancelled successfully", "awb_number": awb_number}


@router.post("/bulk", response_model=List[BookingResponse])
async def bulk_create_bookings(
    request: BulkBookingRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Create multiple bookings at once (max 100)."""
    if len(request.bookings) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 bookings per request")

    service = BookingService(db)
    bookings = []
    for booking_req in request.bookings:
        booking = await service.create_booking(booking_req, current_user["user_id"])
        bookings.append(booking)

    return bookings


@router.get("/{awb_number}/label")
async def get_shipping_label(
    awb_number: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get the shipping label PDF URL for a booking."""
    result = await db.execute(select(Shipment).where(Shipment.awb_number == awb_number))
    shipment = result.scalar_one_or_none()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    if not shipment.label_url:
        raise HTTPException(status_code=404, detail="Label not yet generated")
    return {"label_url": shipment.label_url, "awb_number": awb_number}
