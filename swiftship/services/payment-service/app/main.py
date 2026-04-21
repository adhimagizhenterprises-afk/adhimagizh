"""
Payment Service — SwiftShip
Handles: Razorpay integration, COD management, invoices, remittance
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import payments, cod, invoices, webhooks
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
    title="SwiftShip — Payment Service",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

app.include_router(payments.router,  prefix="/api/v1/payments",          tags=["Payments"])
app.include_router(cod.router,       prefix="/api/v1/payments/cod",      tags=["COD"])
app.include_router(invoices.router,  prefix="/api/v1/payments/invoices", tags=["Invoices"])
app.include_router(webhooks.router,  prefix="/api/v1/payments/webhooks", tags=["Webhooks"])


@app.get("/health")
async def health():
    return {"status": "ok", "service": "payment-service"}
