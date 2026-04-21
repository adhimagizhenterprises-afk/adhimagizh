"""
Agent Service Models
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, Enum, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.base import Base


class AgentStatus(str, PyEnum):
    AVAILABLE = "AVAILABLE"
    ON_DUTY = "ON_DUTY"
    OFF_DUTY = "OFF_DUTY"
    ON_LEAVE = "ON_LEAVE"
    INACTIVE = "INACTIVE"


class DeliveryAttemptResult(str, PyEnum):
    DELIVERED = "DELIVERED"
    NOT_AT_HOME = "NOT_AT_HOME"
    REFUSED = "REFUSED"
    WRONG_ADDRESS = "WRONG_ADDRESS"
    OFFICE_CLOSED = "OFFICE_CLOSED"
    RESCHEDULED = "RESCHEDULED"
    HELD_BY_AGENT = "HELD_BY_AGENT"


class Agent(Base):
    __tablename__ = "agents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, unique=True, nullable=False, index=True)  # From auth service
    agent_code = Column(String(15), unique=True, nullable=False)       # e.g. SS-CHN-001
    name = Column(String(100), nullable=False)
    phone = Column(String(15), nullable=False)
    email = Column(String(100))
    hub_code = Column(String(10), nullable=False, index=True)
    status = Column(Enum(AgentStatus, native_enum=False), default=AgentStatus.AVAILABLE)
    vehicle_type = Column(String(30))   # BIKE, CYCLE, SCOOTER, VAN
    vehicle_number = Column(String(20))
    profile_photo_url = Column(String(500))

    # Performance metrics (updated daily)
    total_deliveries = Column(Integer, default=0)
    successful_deliveries = Column(Integer, default=0)
    total_pickups = Column(Integer, default=0)
    avg_rating = Column(Float, default=0.0)

    # Current state
    current_latitude = Column(Float)
    current_longitude = Column(Float)
    last_location_update = Column(DateTime)
    current_route_id = Column(String)

    joining_date = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class PickupTask(Base):
    __tablename__ = "pickup_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    awb_number = Column(String(20), nullable=False, unique=True, index=True)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False, index=True)
    hub_code = Column(String(10), nullable=False)

    sender_name = Column(String(100))
    sender_phone = Column(String(15))
    pickup_address = Column(Text)
    pickup_city = Column(String(50))
    pickup_pincode = Column(String(10))
    pickup_latitude = Column(Float)
    pickup_longitude = Column(Float)

    scheduled_date = Column(DateTime)
    picked_up_at = Column(DateTime)
    status = Column(String(30), default="ASSIGNED")
    # ASSIGNED, EN_ROUTE, REACHED, PICKED_UP, FAILED, CANCELLED

    weight_kg = Column(Float)
    package_count = Column(Integer, default=1)
    remarks = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)


class DeliveryTask(Base):
    __tablename__ = "delivery_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    awb_number = Column(String(20), nullable=False, index=True)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False, index=True)
    hub_code = Column(String(10), nullable=False)
    route_id = Column(String, index=True)
    sequence_number = Column(Integer)  # Order in today's route

    receiver_name = Column(String(100))
    receiver_phone = Column(String(15))
    delivery_address = Column(Text)
    delivery_city = Column(String(50))
    delivery_pincode = Column(String(10))
    delivery_latitude = Column(Float)
    delivery_longitude = Column(Float)

    is_cod = Column(Boolean, default=False)
    cod_amount = Column(Float, default=0)

    scheduled_date = Column(DateTime)
    status = Column(String(30), default="ASSIGNED")
    # ASSIGNED, EN_ROUTE, REACHED, DELIVERED, ATTEMPTED, FAILED, RTO

    attempt_count = Column(Integer, default=0)
    last_attempt_result = Column(Enum(DeliveryAttemptResult, native_enum=False))
    last_attempt_at = Column(DateTime)
    delivered_at = Column(DateTime)

    otp = Column(String(6))           # OTP sent to receiver
    otp_verified = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)


class ProofOfDelivery(Base):
    __tablename__ = "proof_of_delivery"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    awb_number = Column(String(20), nullable=False, unique=True, index=True)
    delivery_task_id = Column(UUID(as_uuid=True), ForeignKey("delivery_tasks.id"))
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"))

    delivered_to = Column(String(100), nullable=False)   # Name of receiver
    receiver_relation = Column(String(50))  # SELF, FAMILY, SECURITY, NEIGHBOR
    delivery_latitude = Column(Float)
    delivery_longitude = Column(Float)

    photo_url = Column(String(500))        # Package photo
    signature_url = Column(String(500))    # Receiver signature
    otp_verified = Column(Boolean, default=False)

    cod_collected = Column(Boolean, default=False)
    cod_amount = Column(Float, default=0)
    cod_collection_method = Column(String(20))  # CASH, UPI, CARD

    delivered_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)


class AgentLocationHistory(Base):
    __tablename__ = "agent_location_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    accuracy_meters = Column(Float)
    awb_number = Column(String(20))  # Current shipment being handled
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)
