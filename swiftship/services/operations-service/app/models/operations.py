"""
Operations Service Models
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, Enum, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from app.db.base import Base


class HubType(str, PyEnum):
    ORIGIN_HUB = "ORIGIN_HUB"
    TRANSIT_HUB = "TRANSIT_HUB"
    DESTINATION_HUB = "DESTINATION_HUB"
    GATEWAY_HUB = "GATEWAY_HUB"


class ManifestType(str, PyEnum):
    PICKUP = "PICKUP"           # Pickup manifest (agent → hub)
    FORWARD = "FORWARD"         # Hub-to-hub forward
    DELIVERY = "DELIVERY"       # Hub → agent delivery run
    RTO = "RTO"                 # Return to origin


class ManifestStatus(str, PyEnum):
    DRAFT = "DRAFT"
    SEALED = "SEALED"
    DISPATCHED = "DISPATCHED"
    RECEIVED = "RECEIVED"
    CLOSED = "CLOSED"


class RouteStatus(str, PyEnum):
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class Hub(Base):
    __tablename__ = "hubs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hub_code = Column(String(10), unique=True, nullable=False, index=True)
    hub_name = Column(String(100), nullable=False)
    hub_type = Column(Enum(HubType, native_enum=False), nullable=False)
    city = Column(String(50), nullable=False)
    state = Column(String(50), nullable=False)
    pincode = Column(String(10), nullable=False)
    address = Column(Text)
    latitude = Column(Float)
    longitude = Column(Float)
    phone = Column(String(15))
    email = Column(String(100))
    is_active = Column(Boolean, default=True)
    serviceable_pincodes = Column(JSONB, default=[])  # List of pincodes served
    created_at = Column(DateTime, default=datetime.utcnow)


class Manifest(Base):
    __tablename__ = "manifests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    manifest_number = Column(String(30), unique=True, nullable=False, index=True)
    manifest_type = Column(Enum(ManifestType, native_enum=False), nullable=False)
    status = Column(Enum(ManifestStatus, native_enum=False), default=ManifestStatus.DRAFT)

    origin_hub_code = Column(String(10), ForeignKey("hubs.hub_code"), nullable=False)
    destination_hub_code = Column(String(10), ForeignKey("hubs.hub_code"))
    agent_id = Column(String)  # For pickup/delivery manifests

    total_shipments = Column(Integer, default=0)
    total_weight_kg = Column(Float, default=0)
    shipment_awbs = Column(JSONB, default=[])  # List of AWB numbers

    vehicle_number = Column(String(20))
    driver_name = Column(String(100))
    driver_phone = Column(String(15))
    docket_number = Column(String(30))

    dispatched_at = Column(DateTime)
    received_at = Column(DateTime)
    created_by = Column(String, nullable=False)  # Ops user ID
    notes = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DeliveryRoute(Base):
    __tablename__ = "delivery_routes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    route_code = Column(String(20), unique=True, nullable=False)
    hub_code = Column(String(10), nullable=False, index=True)
    agent_id = Column(String, nullable=False, index=True)
    status = Column(Enum(RouteStatus, native_enum=False), default=RouteStatus.PLANNED)

    shipment_awbs = Column(JSONB, default=[])          # Ordered list of AWBs
    optimized_sequence = Column(JSONB, default=[])     # Route-optimized sequence
    total_shipments = Column(Integer, default=0)
    delivered_count = Column(Integer, default=0)
    attempted_count = Column(Integer, default=0)

    route_date = Column(DateTime, nullable=False)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    total_distance_km = Column(Float)

    created_at = Column(DateTime, default=datetime.utcnow)


class Exception(Base):
    """Shipment exceptions — undelivered, damage, lost, etc."""
    __tablename__ = "shipment_exceptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    awb_number = Column(String(20), nullable=False, index=True)
    exception_type = Column(String(50), nullable=False)
    # Types: DELIVERY_ATTEMPT_FAILED, DAMAGED, LOST, ADDRESS_INCORRECT,
    #        REFUSED_BY_CONSIGNEE, HELD_AT_CUSTOMS, NATURAL_CALAMITY
    description = Column(Text)
    hub_code = Column(String(10))
    reported_by = Column(String)
    assigned_to = Column(String)  # Ops user handling this
    status = Column(String(20), default="OPEN")  # OPEN, IN_PROGRESS, RESOLVED
    resolution = Column(Text)
    image_urls = Column(JSONB, default=[])
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)
