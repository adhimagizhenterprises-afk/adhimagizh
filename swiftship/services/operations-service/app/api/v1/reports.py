"""
Reports Router — MIS and operational reports
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.auth import require_ops

router = APIRouter()


@router.get("/summary")
async def daily_summary(
    date: str = Query(default=None, description="YYYY-MM-DD, defaults to today"),
    hub_code: str = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_ops),
):
    """Daily operational summary: booked, picked up, delivered, exceptions."""
    report_date = datetime.strptime(date, "%Y-%m-%d") if date else datetime.utcnow().replace(hour=0, minute=0, second=0)
    # In production: aggregate from booking + tracking DBs via read replicas or data warehouse
    return {
        "date": report_date.strftime("%Y-%m-%d"),
        "hub_code": hub_code or "ALL",
        "booked": 0,
        "picked_up": 0,
        "in_transit": 0,
        "out_for_delivery": 0,
        "delivered": 0,
        "delivery_attempt_failed": 0,
        "rto_initiated": 0,
        "exceptions": 0,
        "delivery_percentage": 0.0,
        "note": "Connect to analytics DB for real data",
    }


@router.get("/performance")
async def agent_performance(
    from_date: str = Query(...),
    to_date: str = Query(...),
    hub_code: str = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_ops),
):
    """Agent-wise delivery performance report."""
    return {
        "from_date": from_date,
        "to_date": to_date,
        "agents": [],
        "note": "Aggregated from agent-service DB",
    }
