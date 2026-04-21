from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.db.session import get_db
from app.models.payment import Invoice
from app.core.auth import get_current_user

router = APIRouter()


@router.get("/")
async def list_invoices(
    customer_id: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    query = select(Invoice)
    if customer_id:
        query = query.where(Invoice.customer_id == customer_id)
    else:
        query = query.where(Invoice.customer_id == current_user["user_id"])
    result = await db.execute(query.offset((page - 1) * page_size).limit(page_size))
    return result.scalars().all()


@router.get("/{invoice_number}")
async def get_invoice(
    invoice_number: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(select(Invoice).where(Invoice.invoice_number == invoice_number))
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice
