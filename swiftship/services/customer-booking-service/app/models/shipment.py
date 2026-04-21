"""
SQLAlchemy models for Customer Booking Service
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, Enum, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.base import Base


class ServiceType(str, PyEnum):
    EXPRESS = "EXPRESS"         # Next day delivery
    PRIORITY = "PRIORITY"       # 2-day delivery
    STANDARD = "STANDARD"       # 3-5 day delivery
    ECONOMY = "ECONOMY"         # 5-7 day delivery


class PaymentMode(str, PyEnum):
    PREPAID = "PREPAID"
    COD = "COD"                 # Cash on Delivery
    CREDIT = "CREDIT"           # Account credit


class ShipmentStatus(str, PyEnum):
    BOOKING_CREATED = "BOOKING_CREATED"
    PICKUP_SCHEDULED = "PICKUP_SCHEDULED"
    PICKED_UP = "PICKED_UP"
    IN_TRANSIT = "IN_TRANSIT"
    AT_HUB = "AT_HUB"
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
    DELIVERED = "DELIVERED"
    DELIVERY_ATTEMPTED = "DELIVERY_ATTEMPTED"
    RTO_INITIATED = "RTO_INITIATED"
    RTO_DELIVERED = "RTO_DELIVERED"
    CANCELLED = "CANCELLED"
    LOST = "LOST"


class Shipment(Base):
    __tablename__ = "shipments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    awb_number = Column(String(20), unique=True, nullable=False, index=True)
    customer_id = Column(String, nullable=False, index=True)

    # Sender details
    sender_name = Column(String(100), nullable=False)
    sender_phone = Column(String(15), nullable=False)
    sender_email = Column(String(100))
    sender_address_line1 = Column(String(200), nullable=False)
    sender_address_line2 = Column(String(200))
    sender_city = Column(String(50), nullable=False)
    sender_state = Column(String(50), nullable=False)
    sender_pincode = Column(String(10), nullable=False)

    # Receiver details
    receiver_name = Column(String(100), nullable=False)
    receiver_phone = Column(String(15), nullable=False)
    receiver_email = Column(String(100))
    receiver_address_line1 = Column(String(200), nullable=False)
    receiver_address_line2 = Column(String(200))
    receiver_city = Column(String(50), nullable=False)
    receiver_state = Column(String(50), nullable=False)
    receiver_pincode = Column(String(10), nullable=False)

    # Package details
    weight_kg = Column(Float, nullable=False)
    length_cm = Column(Float)
    width_cm = Column(Float)
    height_cm = Column(Float)
    volumetric_weight_kg = Column(Float)
    chargeable_weight_kg = Column(Float)
    declared_value = Column(Float, default=0)
    contents_description = Column(String(200))
    is_fragile = Column(Boolean, default=False)
    is_dangerous_goods = Column(Boolean, default=False)

    # Service and pricing
    service_type = Column(Enum(ServiceType, native_enum=False), nullable=False)
    payment_mode = Column(Enum(PaymentMode, native_enum=False), nullable=False)
    cod_amount = Column(Float, default=0)
    freight_charge = Column(Float, nullable=False)
    fuel_surcharge = Column(Float, default=0)
    docket_charge = Column(Float, default=0)
    gst_amount = Column(Float, default=0)
    total_charge = Column(Float, nullable=False)
    zone = Column(String(2))  # A, B, C, D, E

    # Status
    status = Column(Enum(ShipmentStatus, native_enum=False), default=ShipmentStatus.BOOKING_CREATED)
    pickup_date = Column(DateTime)
    expected_delivery_date = Column(DateTime)

    # Operations
    origin_hub_code = Column(String(10))
    destination_hub_code = Column(String(10))
    assigned_agent_id = Column(String, index=True)

    # Label
    label_url = Column(String(500))
    label_generated_at = Column(DateTime)

    # Metadata
    reference_number = Column(String(100))  # Customer's own order ID
    instructions = Column(Text)
    extra_data = Column(JSONB, default={})

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    scan_events = relationship("ScanEvent", back_populates="shipment", lazy="dynamic")


class ScanEvent(Base):
    __tablename__ = "scan_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shipment_id = Column(UUID(as_uuid=True), ForeignKey("shipments.id"), nullable=False)
    awb_number = Column(String(20), nullable=False, index=True)
    status = Column(String(50), nullable=False)
    location = Column(String(200))
    hub_code = Column(String(10))
    remarks = Column(Text)
    scanned_by = Column(String)  # Agent ID or ops user ID
    scanned_at = Column(DateTime, default=datetime.utcnow)

    shipment = relationship("Shipment", back_populates="scan_events")


class SavedAddress(Base):
    __tablename__ = "saved_addresses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(String, nullable=False, index=True)
    label = Column(String(50))  # "Home", "Office", "Warehouse"
    name = Column(String(100), nullable=False)
    phone = Column(String(15), nullable=False)
    email = Column(String(100))
    address_line1 = Column(String(200), nullable=False)
    address_line2 = Column(String(200))
    city = Column(String(50), nullable=False)
    state = Column(String(50), nullable=False)
    pincode = Column(String(10), nullable=False)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
