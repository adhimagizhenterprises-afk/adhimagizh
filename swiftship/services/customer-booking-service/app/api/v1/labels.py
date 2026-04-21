"""
Shipping Labels API — v1 endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.shipment import Shipment
from app.core.auth import get_current_user

router = APIRouter()


@router.get("/{awb_number}")
async def get_label(
    awb_number: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get the shipping label URL for a booking."""
    result = await db.execute(select(Shipment).where(Shipment.awb_number == awb_number))
    shipment = result.scalar_one_or_none()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    if not shipment.label_url:
        raise HTTPException(status_code=404, detail="Label not yet generated for this shipment")
    return {
        "awb_number": awb_number,
        "label_url": shipment.label_url,
        "generated_at": shipment.label_generated_at,
    }
