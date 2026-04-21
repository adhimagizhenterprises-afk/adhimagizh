from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class CreateOrderRequest(BaseModel):
    awb_number: str
    amount: float


class CreateOrderResponse(BaseModel):
    order_id: str
    amount: float
    currency: str
    key_id: str
    awb_number: str


class VerifyPaymentRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class PaymentResponse(BaseModel):
    id: str
    awb_number: str
    amount: float
    payment_mode: str
    status: str
    razorpay_order_id: Optional[str]
    razorpay_payment_id: Optional[str]
    paid_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}
