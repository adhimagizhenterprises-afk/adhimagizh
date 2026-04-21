"""
Hubs Router — CRUD for hub/branch management
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.operations import Hub, HubType
from app.core.auth import require_ops, require_admin

router = APIRouter()


@router.post("/", status_code=201)
async def create_hub(
    hub_code: str, hub_name: str, hub_type: HubType,
    city: str, state: str, pincode: str,
    latitude: Optional[float] = None, longitude: Optional[float] = None,
    phone: Optional[str] = None, email: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    hub = Hub(
        hub_code=hub_code, hub_name=hub_name, hub_type=hub_type,
        city=city, state=state, pincode=pincode,
        latitude=latitude, longitude=longitude,
        phone=phone, email=email,
    )
    db.add(hub)
    await db.commit()
    await db.refresh(hub)
    return hub


@router.get("/")
async def list_hubs(
    hub_type: Optional[HubType] = None,
    state: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_ops),
):
    query = select(Hub).where(Hub.is_active == True)
    if hub_type:
        query = query.where(Hub.hub_type == hub_type)
    if state:
        query = query.where(Hub.state == state)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{hub_code}")
async def get_hub(
    hub_code: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_ops),
):
    result = await db.execute(select(Hub).where(Hub.hub_code == hub_code))
    hub = result.scalar_one_or_none()
    if not hub:
        raise HTTPException(status_code=404, detail="Hub not found")
    return hub
