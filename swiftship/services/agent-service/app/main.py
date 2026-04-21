"""
Agent Service — SwiftShip
Handles: pickup, delivery, POD capture, GPS updates, agent management
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import deliveries, pickups, pod, location, agents
from app.core.config import settings
from app.core.kafka_producer import kafka_producer
from app.db.session import engine
from app.db.base import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await kafka_producer.start()
    yield
    await kafka_producer.stop()
    await engine.dispose()


app = FastAPI(
    title="SwiftShip — Agent Service",
    description="Delivery agent operations: pickup, delivery, POD, GPS",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

app.include_router(agents.router,     prefix="/api/v1/agents",           tags=["Agents"])
app.include_router(pickups.router,    prefix="/api/v1/agents/pickups",   tags=["Pickups"])
app.include_router(deliveries.router, prefix="/api/v1/agents/deliveries",tags=["Deliveries"])
app.include_router(pod.router,        prefix="/api/v1/agents/pod",       tags=["POD"])
app.include_router(location.router,   prefix="/api/v1/agents/location",  tags=["Location"])


@app.get("/health")
async def health():
    return {"status": "ok", "service": "agent-service"}
