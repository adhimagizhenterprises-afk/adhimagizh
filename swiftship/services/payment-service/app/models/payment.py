"""
Payment Service Models
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, Enum, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.base import Base


class PaymentStatus(str, PyEnum):
    PENDING = "PENDING"
    INITIATED = "INITIATED"
    CAPTURED = "CAPTURED"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"
    PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED"


class CODStatus(str, PyEnum):
    PENDING = "PENDING"            # Awaiting delivery
    COLLECTED = "COLLECTED"        # Agent collected cash
    DEPOSITED = "DEPOSITED"        # Deposited at hub
    REMITTED = "REMITTED"          # Transferred to merchant
    FAILED = "FAILED"              # COD collection failed


class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payment_id = Column(String(50), unique=True, index=True)   # SwiftShip internal ID
    awb_number = Column(String(20), nullable=False, index=True)
    customer_id = Column(String, nullable=False, index=True)

    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="INR")
    payment_mode = Column(String(20), nullable=False)          # PREPAID, COD, CREDIT
    status = Column(Enum(PaymentStatus, native_enum=False), default=PaymentStatus.PENDING)

    # Razorpay fields
    razorpay_order_id = Column(String(50))
    razorpay_payment_id = Column(String(50))
    razorpay_signature = Column(String(200))

    # UPI/Card fields
    payment_method = Column(String(20))    # UPI, CARD, NETBANKING, WALLET
    payment_gateway_response = Column(JSONB, default={})

    description = Column(Text)
    failure_reason = Column(String(200))

    paid_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)


class CODTransaction(Base):
    __tablename__ = "cod_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    awb_number = Column(String(20), unique=True, nullable=False, index=True)
    customer_id = Column(String, nullable=False, index=True)
    agent_id = Column(String, index=True)

    cod_amount = Column(Float, nullable=False)
    status = Column(Enum(CODStatus, native_enum=False), default=CODStatus.PENDING)
    collection_mode = Column(String(20))    # CASH, UPI, CARD
    upi_reference = Column(String(50))

    collected_at = Column(DateTime)
    deposited_at = Column(DateTime)
    remitted_at = Column(DateTime)
    remittance_reference = Column(String(50))

    hub_code = Column(String(10))
    remarks = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_number = Column(String(30), unique=True, nullable=False, index=True)
    customer_id = Column(String, nullable=False, index=True)
    billing_period_start = Column(DateTime, nullable=False)
    billing_period_end = Column(DateTime, nullable=False)

    subtotal = Column(Float, nullable=False)
    discount = Column(Float, default=0)
    taxable_amount = Column(Float, nullable=False)
    gst_rate = Column(Float, default=18.0)
    gst_amount = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    currency = Column(String(3), default="INR")

    status = Column(String(20), default="DRAFT")   # DRAFT, ISSUED, PAID, OVERDUE
    due_date = Column(DateTime)
    paid_at = Column(DateTime)

    pdf_url = Column(String(500))
    line_items = Column(JSONB, default=[])          # List of AWBs with charges

    created_at = Column(DateTime, default=datetime.utcnow)
