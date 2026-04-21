"""
Tracking Kafka Consumer
Listens to all shipment events and keeps ShipmentTracking table current.
Also broadcasts live updates via WebSocket manager.
"""
import json
import asyncio
import logging
from datetime import datetime
from aiokafka import AIOKafkaConsumer
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.tracking import ShipmentTracking, TrackingEvent

logger = logging.getLogger(__name__)

TOPICS = [
    "booking.created",
    "shipment.picked_up",
    "shipment.in_transit",
    "shipment.at_hub",
    "shipment.out_for_delivery",
    "shipment.delivered",
    "shipment.exception",
    "shipment.rto_initiated",
    "shipment.returned",
    "pod.captured",
]

# Event type → friendly status label
EVENT_STATUS_MAP = {
    "booking.created":          "BOOKING_CREATED",
    "pickup.scheduled":         "PICKUP_SCHEDULED",
    "shipment.picked_up":       "PICKED_UP",
    "shipment.in_transit":      "IN_TRANSIT",
    "shipment.at_hub":          "AT_HUB",
    "shipment.out_for_delivery":"OUT_FOR_DELIVERY",
    "shipment.delivered":       "DELIVERED",
    "shipment.exception":       "DELIVERY_ATTEMPTED",
    "shipment.rto_initiated":   "RTO_INITIATED",
    "shipment.returned":        "RTO_DELIVERED",
}


async def start_kafka_consumer(ws_manager):
    """
    Background task: consume shipment events and update tracking state.
    ws_manager is the WebSocket ConnectionManager from main.py.
    """
    from app.core.config import settings

    consumer = AIOKafkaConsumer(
        *TOPICS,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id="tracking-service-group",
        auto_offset_reset="earliest",
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    )
    await consumer.start()
    logger.info(f"Tracking consumer started, topics: {TOPICS}")

    try:
        async for message in consumer:
            await _process_event(message.topic, message.value, ws_manager)
    except asyncio.CancelledError:
        logger.info("Tracking consumer cancelled")
    finally:
        await consumer.stop()


async def _process_event(topic: str, event: dict, ws_manager):
    awb = event.get("awb_number")
    if not awb:
        return

    new_status = EVENT_STATUS_MAP.get(topic, "UNKNOWN")
    location = event.get("location", event.get("current_location", ""))
    hub_code = event.get("hub_code")
    remarks = event.get("remarks")
    agent_id = event.get("agent_id")
    lat = event.get("latitude")
    lng = event.get("longitude")

    async with AsyncSessionLocal() as db:
        # Upsert ShipmentTracking
        result = await db.execute(
            select(ShipmentTracking).where(ShipmentTracking.awb_number == awb)
        )
        tracking = result.scalar_one_or_none()

        if not tracking:
            tracking = ShipmentTracking(
                awb_number=awb,
                origin_city=event.get("sender_city"),
                destination_city=event.get("receiver_city"),
                expected_delivery_date=event.get("expected_delivery_date"),
            )
            db.add(tracking)

        tracking.current_status = new_status
        tracking.current_location = location
        tracking.last_updated = datetime.utcnow()

        # Add scan event
        scan = TrackingEvent(
            awb_number=awb,
            status=new_status,
            location=location,
            hub_code=hub_code,
            remarks=remarks,
            agent_id=agent_id,
            latitude=lat,
            longitude=lng,
            event_time=datetime.utcnow(),
            source_service=event.get("service_name", topic),
        )
        db.add(scan)
        await db.commit()

    # Broadcast live update to any connected WebSocket clients
    ws_payload = {
        "type": "status_update",
        "awb_number": awb,
        "status": new_status,
        "location": location,
        "remarks": remarks,
        "timestamp": datetime.utcnow().isoformat(),
        "event": {
            "status": new_status,
            "location": location,
            "hub_code": hub_code,
            "remarks": remarks,
            "event_time": datetime.utcnow().isoformat(),
        },
    }
    await ws_manager.broadcast_to_awb(awb, ws_payload)
    logger.info(f"Tracking updated: {awb} → {new_status}")
