"""
Customer Booking Service — SwiftShip
Handles: shipment creation, pricing, AWB generation, pickup scheduling
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.api.v1 import bookings, pricing, addresses, labels
from app.core.config import settings
from app.core.kafka_producer import kafka_producer
from app.db.session import engine
from app.db.base import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await kafka_producer.start()
    yield
    # Shutdown
    await kafka_producer.stop()
    await engine.dispose()


app = FastAPI(
    title="SwiftShip — Customer Booking Service",
    description="Shipment booking, pricing, AWB generation",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(bookings.router, prefix="/api/v1/bookings", tags=["Bookings"])
app.include_router(pricing.router, prefix="/api/v1/pricing", tags=["Pricing"])
app.include_router(addresses.router, prefix="/api/v1/addresses", tags=["Addresses"])
app.include_router(labels.router, prefix="/api/v1/labels", tags=["Labels"])


@app.get("/health")
async def health():
    return {"status": "ok", "service": "customer-booking-service", "version": "1.0.0"}
