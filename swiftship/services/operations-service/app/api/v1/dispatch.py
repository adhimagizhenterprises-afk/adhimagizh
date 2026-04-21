"""
Operations — Dispatch Router
Assign shipments to delivery agents and create route plans.
"""
from typing import List, Optional
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.db.session import get_db
from app.models.operations import DeliveryRoute, RouteStatus
from app.core.auth import require_ops

router = APIRouter()


@router.post("/routes")
async def create_delivery_route(
    hub_code: str,
    agent_id: str,
    awb_numbers: List[str],
    route_date: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_ops),
):
    """Create a delivery route and assign shipments to an agent."""
    route_code = f"RT-{hub_code}-{date.today().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
    route = DeliveryRoute(
        route_code=route_code,
        hub_code=hub_code,
        agent_id=agent_id,
        shipment_awbs=awb_numbers,
        total_shipments=len(awb_numbers),
        route_date=datetime.strptime(route_date, "%Y-%m-%d"),
        status=RouteStatus.PLANNED,
    )
    db.add(route)
    await db.commit()
    await db.refresh(route)
    return route


@router.get("/routes")
async def list_routes(
    hub_code: Optional[str] = None,
    agent_id: Optional[str] = None,
    route_date: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_ops),
):
    query = select(DeliveryRoute)
    if hub_code:
        query = query.where(DeliveryRoute.hub_code == hub_code)
    if agent_id:
        query = query.where(DeliveryRoute.agent_id == agent_id)
    result = await db.execute(query.order_by(DeliveryRoute.created_at.desc()))
    return result.scalars().all()
