"""
Payment API endpoints
"""
import hashlib
import hmac
import uuid
from datetime import datetime

import razorpay
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.payment import Payment, PaymentStatus
from app.schemas.payment import (
    CreateOrderRequest, CreateOrderResponse,
    VerifyPaymentRequest, PaymentResponse,
)
from app.core.auth import get_current_user
from app.core.config import settings
from app.core.kafka_producer import kafka_producer
from shared.events.schemas import PaymentEvent, EventType

router = APIRouter()


def get_razorpay_client():
    return razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )


@router.post("/create-order", response_model=CreateOrderResponse)
async def create_payment_order(
    request: CreateOrderRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Create a Razorpay order for prepaid booking.
    Returns order_id to the frontend for Razorpay checkout.
    """
    client = get_razorpay_client()

    rz_order = client.order.create({
        "amount": int(request.amount * 100),  # Razorpay uses paise
        "currency": "INR",
        "receipt": request.awb_number,
        "notes": {
            "awb_number": request.awb_number,
            "customer_id": current_user["user_id"],
        },
    })

    # Persist pending payment record
    payment = Payment(
        awb_number=request.awb_number,
        customer_id=current_user["user_id"],
        amount=request.amount,
        currency="INR",
        payment_mode="PREPAID",
        razorpay_order_id=rz_order["id"],
        status=PaymentStatus.PENDING,
    )
    db.add(payment)
    await db.commit()

    return CreateOrderResponse(
        order_id=rz_order["id"],
        amount=request.amount,
        currency="INR",
        key_id=settings.RAZORPAY_KEY_ID,
        awb_number=request.awb_number,
    )


@router.post("/verify", response_model=PaymentResponse)
async def verify_payment(
    request: VerifyPaymentRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Verify Razorpay payment signature after successful checkout.
    """
    # Signature verification
    expected_sig = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode(),
        f"{request.razorpay_order_id}|{request.razorpay_payment_id}".encode(),
        hashlib.sha256,
    ).hexdigest()

    if expected_sig != request.razorpay_signature:
        raise HTTPException(status_code=400, detail="Payment signature verification failed")

    # Update payment record
    result = await db.execute(
        select(Payment).where(Payment.razorpay_order_id == request.razorpay_order_id)
    )
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment record not found")

    payment.razorpay_payment_id = request.razorpay_payment_id
    payment.razorpay_signature = request.razorpay_signature
    payment.status = PaymentStatus.CAPTURED
    payment.paid_at = datetime.utcnow()
    await db.commit()

    # Publish payment confirmed event
    background_tasks.add_task(
        kafka_producer.publish,
        topic="payment.confirmed",
        event=PaymentEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.PAYMENT_CONFIRMED,
            timestamp=datetime.utcnow(),
            service_name="payment-service",
            awb_number=payment.awb_number,
            payment_id=str(payment.id),
            amount=payment.amount,
            payment_mode="PREPAID",
            razorpay_order_id=payment.razorpay_order_id,
            razorpay_payment_id=payment.razorpay_payment_id,
        ).model_dump(),
    )

    return payment


@router.post("/webhook/razorpay")
async def razorpay_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Razorpay webhook endpoint.
    Handles payment.captured, payment.failed, refund events.
    """
    body = await request.body()
    sig = request.headers.get("x-razorpay-signature", "")

    expected = hmac.new(
        settings.RAZORPAY_WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()

    if expected != sig:
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    payload = await request.json()
    event = payload.get("event")

    if event == "payment.captured":
        payment_entity = payload["payload"]["payment"]["entity"]
        order_id = payment_entity.get("order_id")

        result = await db.execute(
            select(Payment).where(Payment.razorpay_order_id == order_id)
        )
        payment = result.scalar_one_or_none()
        if payment and payment.status == PaymentStatus.PENDING:
            payment.status = PaymentStatus.CAPTURED
            payment.razorpay_payment_id = payment_entity["id"]
            payment.paid_at = datetime.utcnow()
            await db.commit()

    return {"status": "ok"}
