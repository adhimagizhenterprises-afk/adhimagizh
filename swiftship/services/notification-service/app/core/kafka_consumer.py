"""
Notification Kafka Consumer
Listens to all shipment event topics and dispatches notifications.
"""
import json
import logging
import asyncio
from aiokafka import AIOKafkaConsumer

from app.core.config import settings
from app.services.sms_service import SMSService
from app.services.email_service import EmailService
from app.services.push_service import PushService
from app.db.session import AsyncSessionLocal
from app.models.notification import NotificationLog, NotificationStatus

logger = logging.getLogger(__name__)


NOTIFICATION_TEMPLATES = {
    "booking.created": {
        "sms": "Hi {sender_name}, your shipment with AWB {awb_number} has been booked! Pickup scheduled for {pickup_date}. Track: swiftship.in/track/{awb_number}",
        "email_subject": "Booking Confirmed — AWB {awb_number}",
        "push_title": "Booking Confirmed!",
        "push_body": "AWB {awb_number} booked. Pickup on {pickup_date}.",
    },
    "shipment.picked_up": {
        "sms": "Your shipment {awb_number} has been picked up and is on its way. Track: swiftship.in/track/{awb_number}",
        "email_subject": "Shipment Picked Up — AWB {awb_number}",
        "push_title": "Shipment Picked Up",
        "push_body": "AWB {awb_number} is now in transit.",
    },
    "shipment.out_for_delivery": {
        "sms": "Hi {receiver_name}, your shipment {awb_number} is out for delivery today. Agent: {agent_phone}. OTP: {otp}",
        "email_subject": "Out for Delivery — AWB {awb_number}",
        "push_title": "Out for Delivery!",
        "push_body": "Your package arrives today. Keep your phone handy.",
    },
    "shipment.delivered": {
        "sms": "Your shipment {awb_number} has been delivered to {delivered_to}. Thank you for using SwiftShip!",
        "email_subject": "Delivered! — AWB {awb_number}",
        "push_title": "Package Delivered",
        "push_body": "AWB {awb_number} delivered to {delivered_to}.",
    },
    "shipment.exception": {
        "sms": "Delivery update for {awb_number}: {remarks}. We will retry. Track: swiftship.in/track/{awb_number}",
        "email_subject": "Delivery Update — AWB {awb_number}",
        "push_title": "Delivery Update",
        "push_body": "{remarks}",
    },
    "shipment.rto_initiated": {
        "sms": "Your shipment {awb_number} is being returned to the sender. Reason: {remarks}.",
        "email_subject": "Shipment Returned — AWB {awb_number}",
        "push_title": "Shipment Returned",
        "push_body": "AWB {awb_number} is being returned to sender.",
    },
}

TOPICS = [
    "booking.created",
    "shipment.picked_up",
    "shipment.in_transit",
    "shipment.out_for_delivery",
    "shipment.delivered",
    "shipment.exception",
    "shipment.rto_initiated",
    "payment.confirmed",
]


class NotificationKafkaConsumer:
    def __init__(self):
        self.sms = SMSService()
        self.email = EmailService()
        self.push = PushService()

    async def start(self):
        consumer = None
        for attempt in range(1, 11):
            try:
                consumer = AIOKafkaConsumer(
                    *TOPICS,
                    bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                    group_id="notification-service-group",
                    auto_offset_reset="earliest",
                    value_deserializer=lambda v: json.loads(v.decode("utf-8")),
                )
                await consumer.start()
                logger.info(f"Consuming topics: {TOPICS}")
                break
            except Exception as e:
                logger.warning(f"Kafka consumer connection attempt {attempt}/10 failed: {e}")
                consumer = None
                if attempt < 10:
                    await asyncio.sleep(5)
        if consumer is None:
            logger.error("Could not connect to Kafka after 10 attempts — notification consumer not running")
            return
        try:
            async for message in consumer:
                await self._handle_event(message.topic, message.value)
        except asyncio.CancelledError:
            logger.info("Consumer cancelled")
        finally:
            await consumer.stop()

    async def _handle_event(self, topic: str, event: dict):
        """Process an event and dispatch appropriate notifications."""
        try:
            template = NOTIFICATION_TEMPLATES.get(topic)
            if not template:
                return

            awb = event.get("awb_number", "")
            logger.info(f"Processing {topic} for AWB: {awb}")

            # Resolve recipient details from event
            sender_phone = event.get("sender_phone")
            receiver_phone = event.get("receiver_phone")
            sender_name = event.get("sender_name", "Customer")
            receiver_name = event.get("receiver_name", "Receiver")

            # Format messages
            sms_body = template["sms"].format(**{**event, "sender_name": sender_name, "receiver_name": receiver_name})
            push_body = template["push_body"].format(**event)

            # Dispatch based on topic (sender vs receiver notifications)
            if topic == "booking.created" and sender_phone:
                await self.sms.send(sender_phone, sms_body)
                await self._log_notification(awb, "SMS", sender_phone, "booking.created", sms_body)

            elif topic in ["shipment.out_for_delivery", "shipment.delivered"] and receiver_phone:
                await self.sms.send(receiver_phone, sms_body)
                await self._log_notification(awb, "SMS", receiver_phone, topic, sms_body)

            elif topic == "shipment.exception":
                if sender_phone:
                    await self.sms.send(sender_phone, sms_body)

        except Exception as e:
            logger.error(f"Failed to process notification for {topic}: {e}")

    async def _log_notification(self, awb: str, channel: str, recipient: str, event_type: str, body: str):
        """Persist notification log to DB."""
        async with AsyncSessionLocal() as db:
            log = NotificationLog(
                awb_number=awb,
                channel=channel,
                recipient=recipient,
                event_type=event_type,
                message_body=body,
                status=NotificationStatus.SENT,
            )
            db.add(log)
            await db.commit()
