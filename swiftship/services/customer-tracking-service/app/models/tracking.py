"""
Tracking Service Models
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base


class ShipmentTracking(Base):
    """Denormalized tracking summary — fast read for customer-facing API."""
    __tablename__ = "shipment_tracking"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    awb_number = Column(String(20), unique=True, nullable=False, index=True)
    current_status = Column(String(50), nullable=False, default="BOOKING_CREATED")
    current_location = Column(String(200))
    origin_city = Column(String(50))
    destination_city = Column(String(50))
    expected_delivery_date = Column(DateTime)
    is_delayed = Column(Boolean, default=False)
    delay_reason = Column(String(200))
    last_updated = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)


class TrackingEvent(Base):
    """Individual scan event — full history."""
    __tablename__ = "tracking_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    awb_number = Column(String(20), nullable=False, index=True)
    status = Column(String(50), nullable=False)
    location = Column(String(200))
    hub_code = Column(String(10))
    remarks = Column(Text)
    agent_id = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    event_time = Column(DateTime, default=datetime.utcnow, index=True)
    source_service = Column(String(50))  # which microservice generated this event
