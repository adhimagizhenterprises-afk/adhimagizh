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
                    acks="all",
                    enable_idempotence=True,
                )
                await self._producer.start()
                logger.info("Kafka producer started")
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

    async def publish(self, topic: str, event: Dict[str, Any], key: str | None = None):
        if not self._producer:
            return
        try:
            key_bytes = key.encode() if key else None
            await self._producer.send_and_wait(topic, value=event, key=key_bytes)
        except Exception as e:
            logger.error(f"Failed to publish to {topic}: {e}", exc_info=True)


kafka_producer = KafkaProducer()
