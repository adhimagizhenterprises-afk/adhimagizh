"""
POD (Proof of Delivery) retrieval endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.agent import ProofOfDelivery
from app.core.auth import get_current_user

router = APIRouter()


@router.get("/{awb_number}")
async def get_pod(
    awb_number: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Retrieve POD details for a delivered shipment."""
    result = await db.execute(
        select(ProofOfDelivery).where(ProofOfDelivery.awb_number == awb_number)
    )
    pod = result.scalar_one_or_none()
    if not pod:
        raise HTTPException(status_code=404, detail="POD not found")
    return {
        "awb_number": awb_number,
        "delivered_to": pod.delivered_to,
        "receiver_relation": pod.receiver_relation,
        "delivery_latitude": pod.delivery_latitude,
        "delivery_longitude": pod.delivery_longitude,
        "photo_url": pod.photo_url,
        "signature_url": pod.signature_url,
        "otp_verified": pod.otp_verified,
        "cod_collected": pod.cod_collected,
        "cod_amount": pod.cod_amount,
        "delivered_at": pod.delivered_at,
    }
