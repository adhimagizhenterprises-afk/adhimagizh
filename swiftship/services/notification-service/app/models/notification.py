"""Notification Log model"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, String, DateTime, Enum, Text
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base


class NotificationStatus(str, PyEnum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"
    DELIVERED = "DELIVERED"


class NotificationLog(Base):
    __tablename__ = "notification_logs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    awb_number = Column(String(20), index=True)
    channel = Column(String(20))   # SMS, EMAIL, PUSH
    recipient = Column(String(100))
    event_type = Column(String(50))
    message_body = Column(Text)
    status = Column(Enum(NotificationStatus, native_enum=False), default=NotificationStatus.PENDING)
    error_message = Column(Text)
    sent_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
