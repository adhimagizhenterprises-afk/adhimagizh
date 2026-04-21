"""
Notification Service — SwiftShip
Consumes Kafka events and dispatches SMS, email, push notifications.
"""
from contextlib import asynccontextmanager
import asyncio
import logging
from fastapi import FastAPI

from app.core.kafka_consumer import NotificationKafkaConsumer
from app.core.config import settings
from app.db.session import engine
from app.db.base import Base
from app.api.v1 import notifications

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    consumer = NotificationKafkaConsumer()
    consumer_task = asyncio.create_task(consumer.start())
    logger.info("Notification Kafka consumer started")
    yield
    consumer_task.cancel()
    await engine.dispose()


app = FastAPI(
    title="SwiftShip — Notification Service",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["Notifications"])


@app.get("/health")
async def health():
    return {"status": "ok", "service": "notification-service"}
