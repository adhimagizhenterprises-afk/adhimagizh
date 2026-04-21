"""
User model — user-auth-service
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, String, Boolean, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base


class UserRole(str, PyEnum):
    CUSTOMER = "CUSTOMER"
    AGENT = "AGENT"
    OPS = "OPS"
    ADMIN = "ADMIN"
    ENTERPRISE = "ENTERPRISE"   # B2B API clients


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    phone = Column(String(15), unique=True, nullable=False, index=True)
    password_hash = Column(String(200))
    role = Column(Enum(UserRole, native_enum=False), default=UserRole.CUSTOMER, nullable=False)

    # OAuth
    google_id = Column(String(100), unique=True, nullable=True)
    apple_id = Column(String(100), unique=True, nullable=True)

    # Profile
    profile_photo_url = Column(String(500))
    gstin = Column(String(20))          # For GST invoices (business customers)
    company_name = Column(String(100))

    # State
    is_active = Column(Boolean, default=True)
    is_email_verified = Column(Boolean, default=False)
    is_phone_verified = Column(Boolean, default=False)
    email_verification_token = Column(String(100))
    password_reset_token = Column(String(100))
    password_reset_expires = Column(DateTime)

    # API access (enterprise)
    api_key = Column(String(64), unique=True, nullable=True, index=True)
    api_key_active = Column(Boolean, default=False)

    last_login = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
