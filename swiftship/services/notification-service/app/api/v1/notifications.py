"""Notifications API — query notification history"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.db.session import get_db
from app.models.notification import NotificationLog

router = APIRouter()


@router.get("/")
async def list_notifications(
    awb_number: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20),
    db: AsyncSession = Depends(get_db),
):
    query = select(NotificationLog).order_by(NotificationLog.created_at.desc())
    if awb_number:
        query = query.where(NotificationLog.awb_number == awb_number)
    result = await db.execute(query.offset((page - 1) * page_size).limit(page_size))
    return result.scalars().all()
