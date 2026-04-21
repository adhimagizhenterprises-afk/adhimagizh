"""
Exceptions Router — handle shipment exceptions
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.session import get_db
from app.models.operations import Exception as ShipmentException
from app.core.auth import require_ops

router = APIRouter()


@router.get("/")
async def list_exceptions(
    status: Optional[str] = Query(None, description="OPEN, IN_PROGRESS, RESOLVED"),
    exception_type: Optional[str] = Query(None),
    hub_code: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_ops),
):
    """List all shipment exceptions with filters."""
    query = select(ShipmentException)
    if status:
        query = query.where(ShipmentException.status == status)
    if exception_type:
        query = query.where(ShipmentException.exception_type == exception_type)
    if hub_code:
        query = query.where(ShipmentException.hub_code == hub_code)

    query = query.order_by(ShipmentException.created_at.desc())
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar()
    result = await db.execute(query.offset((page - 1) * page_size).limit(page_size))

    return {
        "items": result.scalars().all(),
        "total": total,
        "page": page,
    }


@router.post("/{exception_id}/resolve")
async def resolve_exception(
    exception_id: str,
    resolution: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_ops),
):
    result = await db.execute(
        select(ShipmentException).where(ShipmentException.id == exception_id)
    )
    exc = result.scalar_one_or_none()
    if not exc:
        raise HTTPException(status_code=404, detail="Exception not found")

    from datetime import datetime
    exc.status = "RESOLVED"
    exc.resolution = resolution
    exc.resolved_at = datetime.utcnow()
    exc.assigned_to = current_user["user_id"]
    await db.commit()
    return {"message": "Exception resolved", "id": exception_id}
