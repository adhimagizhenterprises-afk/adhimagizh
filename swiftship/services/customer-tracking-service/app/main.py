"""
Customer Tracking Service — SwiftShip
Handles: real-time tracking, scan events, ETA, WebSocket live updates
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List
import json
import asyncio

from app.api.v1 import tracking
from app.core.config import settings
from app.core.kafka_consumer import start_kafka_consumer
from app.db.session import engine
from app.db.base import Base


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, awb_number: str):
        await websocket.accept()
        if awb_number not in self.active_connections:
            self.active_connections[awb_number] = []
        self.active_connections[awb_number].append(websocket)

    def disconnect(self, websocket: WebSocket, awb_number: str):
        if awb_number in self.active_connections:
            self.active_connections[awb_number].remove(websocket)

    async def broadcast_to_awb(self, awb_number: str, message: dict):
        if awb_number in self.active_connections:
            dead = []
            for connection in self.active_connections[awb_number]:
                try:
                    await connection.send_json(message)
                except Exception:
                    dead.append(connection)
            for conn in dead:
                self.active_connections[awb_number].remove(conn)


manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Start Kafka consumer in background
    consumer_task = asyncio.create_task(start_kafka_consumer(manager))
    yield
    consumer_task.cancel()
    await engine.dispose()


app = FastAPI(
    title="SwiftShip — Customer Tracking Service",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tracking.router, prefix="/api/v1/tracking", tags=["Tracking"])


@app.websocket("/ws/tracking/{awb_number}")
async def websocket_tracking(websocket: WebSocket, awb_number: str):
    """WebSocket endpoint for live shipment tracking."""
    await manager.connect(websocket, awb_number)
    try:
        while True:
            # Keep connection alive, send ping every 30s
            await asyncio.sleep(30)
            await websocket.send_json({"type": "ping"})
    except WebSocketDisconnect:
        manager.disconnect(websocket, awb_number)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "customer-tracking-service"}
