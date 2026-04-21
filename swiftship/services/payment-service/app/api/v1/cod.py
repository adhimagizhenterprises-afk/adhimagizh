from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.db.session import get_db
from app.models.payment import CODTransaction, CODStatus
from app.core.auth import get_current_user

router = APIRouter()


@router.get("/")
async def list_cod_transactions(
    status: Optional[CODStatus] = None,
    agent_id: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    query = select(CODTransaction)
    if status:
        query = query.where(CODTransaction.status == status)
    if agent_id:
        query = query.where(CODTransaction.agent_id == agent_id)
    result = await db.execute(query.offset((page - 1) * page_size).limit(page_size))
    return result.scalars().all()


@router.post("/{awb_number}/collect")
async def mark_cod_collected(
    awb_number: str,
    collection_mode: str = "CASH",
    upi_reference: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    from datetime import datetime
    result = await db.execute(select(CODTransaction).where(CODTransaction.awb_number == awb_number))
    cod = result.scalar_one_or_none()
    if not cod:
        raise HTTPException(status_code=404, detail="COD record not found")
    cod.status = CODStatus.COLLECTED
    cod.collection_mode = collection_mode
    cod.upi_reference = upi_reference
    cod.collected_at = datetime.utcnow()
    await db.commit()
    return {"awb_number": awb_number, "status": "COLLECTED"}
