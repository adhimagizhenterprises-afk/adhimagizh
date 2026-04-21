"""
Async Kafka Producer — wraps aiokafka for easy event publishing
"""
import asyncio
import json
import logging
from typing import Any, Dict
from aiokafka import AIOKafkaProducer
from app.core.config import settings

logger = logging.getLogger(__name__)


class KafkaProducer:
    def __init__(self):
        self._producer: AIOKafkaProducer | None = None

    async def start(self):
        for attempt in range(1, 11):
            try:
                self._producer = AIOKafkaProducer(
                    bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                    value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
                    acks="all",           # Wait for all replicas
                    enable_idempotence=True,
                    compression_type="gzip",
                    max_batch_size=16384,
                    linger_ms=5,          # Small batching window for throughput
                )
                await self._producer.start()
                logger.info(f"Kafka producer started — servers: {settings.KAFKA_BOOTSTRAP_SERVERS}")
                return
            except Exception as e:
                logger.warning(f"Kafka connection attempt {attempt}/10 failed: {e}")
                self._producer = None
                if attempt < 10:
                    await asyncio.sleep(5)
        logger.error("Could not connect to Kafka after 10 attempts — running without Kafka")

    async def stop(self):
        if self._producer:
            await self._producer.stop()
            logger.info("Kafka producer stopped")

    async def publish(self, topic: str, event: Dict[str, Any], key: str | None = None):
        """
        Publish an event dict to a Kafka topic.
        key (optional) — used for partition routing (e.g. AWB number ensures
        all events for a shipment go to same partition → ordered).
        """
        if not self._producer:
            logger.error("Kafka producer not started")
            return

        try:
            key_bytes = key.encode() if key else None
            await self._producer.send_and_wait(topic, value=event, key=key_bytes)
            logger.debug(f"Published to {topic}: {event.get('event_type', '?')}")
        except Exception as e:
            logger.error(f"Failed to publish to {topic}: {e}", exc_info=True)
            # Don't re-raise — Kafka failures should not break the main request flow
            # In production: implement dead-letter queue or retry logic here


kafka_producer = KafkaProducer()
