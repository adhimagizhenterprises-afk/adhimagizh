"""
Shared Kafka event schemas for SwiftShip microservices.
All services import these to ensure event contract consistency.
"""
from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, UUID4


class EventType(str, Enum):
    BOOKING_CREATED = "booking.created"
    BOOKING_CANCELLED = "booking.cancelled"
    PICKUP_SCHEDULED = "pickup.scheduled"
    SHIPMENT_PICKED_UP = "shipment.picked_up"
    SHIPMENT_IN_TRANSIT = "shipment.in_transit"
    SHIPMENT_AT_HUB = "shipment.at_hub"
    SHIPMENT_OUT_FOR_DELIVERY = "shipment.out_for_delivery"
    SHIPMENT_DELIVERED = "shipment.delivered"
    SHIPMENT_EXCEPTION = "shipment.exception"
    SHIPMENT_RTO_INITIATED = "shipment.rto_initiated"
    SHIPMENT_RETURNED = "shipment.returned"
    PAYMENT_CONFIRMED = "payment.confirmed"
    PAYMENT_FAILED = "payment.failed"
    COD_COLLECTED = "payment.cod_collected"
    POD_CAPTURED = "pod.captured"
    AGENT_ASSIGNED = "agent.assigned"
    AGENT_LOCATION_UPDATED = "agent.location_updated"


class BaseEvent(BaseModel):
    event_id: str
    event_type: EventType
    timestamp: datetime
    service_name: str
    version: str = "1.0"
    metadata: Dict[str, Any] = {}


class BookingCreatedEvent(BaseEvent):
    event_type: EventType = EventType.BOOKING_CREATED
    awb_number: str
    customer_id: str
    sender_name: str
    sender_phone: str
    sender_city: str
    receiver_name: str
    receiver_phone: str
    receiver_city: str
    receiver_pincode: str
    weight_kg: float
    service_type: str  # EXPRESS, STANDARD, ECONOMY
    payment_mode: str  # PREPAID, COD
    amount: float
    pickup_date: str


class ShipmentStatusEvent(BaseEvent):
    awb_number: str
    status: str
    location: str
    hub_code: Optional[str] = None
    remarks: Optional[str] = None
    agent_id: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class DeliveryEvent(BaseEvent):
    event_type: EventType = EventType.SHIPMENT_DELIVERED
    awb_number: str
    agent_id: str
    delivered_to: str  # Name of person who received
    delivery_time: datetime
    pod_image_url: Optional[str] = None
    signature_url: Optional[str] = None
    otp_verified: bool = False


class PaymentEvent(BaseEvent):
    awb_number: str
    payment_id: str
    amount: float
    currency: str = "INR"
    payment_mode: str
    razorpay_order_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None


class AgentLocationEvent(BaseEvent):
    event_type: EventType = EventType.AGENT_LOCATION_UPDATED
    agent_id: str
    latitude: float
    longitude: float
    awb_number: Optional[str] = None  # Current shipment being handled
    accuracy_meters: Optional[float] = None
