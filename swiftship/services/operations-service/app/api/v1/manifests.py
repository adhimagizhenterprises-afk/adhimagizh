"""
Manifests API — create, seal, dispatch, receive manifests
"""
from typing import List, Optional
from datetime import datetime
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.session import get_db
from app.models.operations import Manifest, ManifestStatus, ManifestType
from app.core.auth import require_ops
from shared.utils.awb import generate_manifest_number

router = APIRouter()


@router.post("/", status_code=201)
async def create_manifest(
    manifest_type: ManifestType,
    origin_hub_code: str,
    destination_hub_code: Optional[str] = None,
    agent_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_ops),
):
    """Create a new empty manifest (DRAFT state)."""
    manifest_number = generate_manifest_number(origin_hub_code)
    manifest = Manifest(
        manifest_number=manifest_number,
        manifest_type=manifest_type,
        origin_hub_code=origin_hub_code,
        destination_hub_code=destination_hub_code,
        agent_id=agent_id,
        status=ManifestStatus.DRAFT,
        created_by=current_user["user_id"],
    )
    db.add(manifest)
    await db.commit()
    await db.refresh(manifest)
    return manifest


@router.post("/{manifest_number}/add-shipment")
async def add_shipment_to_manifest(
    manifest_number: str,
    awb_number: str,
    weight_kg: float,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_ops),
):
    """Scan / add a shipment AWB to an open manifest."""
    result = await db.execute(
        select(Manifest).where(
            Manifest.manifest_number == manifest_number,
            Manifest.status == ManifestStatus.DRAFT,
        )
    )
    manifest = result.scalar_one_or_none()
    if not manifest:
        raise HTTPException(status_code=404, detail="Manifest not found or not in DRAFT state")

    awbs = list(manifest.shipment_awbs or [])
    if awb_number in awbs:
        raise HTTPException(status_code=400, detail=f"{awb_number} already in manifest")

    awbs.append(awb_number)
    manifest.shipment_awbs = awbs
    manifest.total_shipments = len(awbs)
    manifest.total_weight_kg = (manifest.total_weight_kg or 0) + weight_kg
    await db.commit()

    return {
        "manifest_number": manifest_number,
        "awb_number": awb_number,
        "total_shipments": manifest.total_shipments,
        "total_weight_kg": manifest.total_weight_kg,
    }


@router.post("/{manifest_number}/seal")
async def seal_manifest(
    manifest_number: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_ops),
):
    """Seal a manifest — no more shipments can be added."""
    result = await db.execute(
        select(Manifest).where(Manifest.manifest_number == manifest_number)
    )
    manifest = result.scalar_one_or_none()
    if not manifest:
        raise HTTPException(status_code=404, detail="Manifest not found")
    if manifest.status != ManifestStatus.DRAFT:
        raise HTTPException(status_code=400, detail=f"Cannot seal manifest in {manifest.status} state")
    if manifest.total_shipments == 0:
        raise HTTPException(status_code=400, detail="Cannot seal empty manifest")

    manifest.status = ManifestStatus.SEALED
    await db.commit()
    return {"manifest_number": manifest_number, "status": "SEALED", "total_shipments": manifest.total_shipments}


@router.post("/{manifest_number}/dispatch")
async def dispatch_manifest(
    manifest_number: str,
    vehicle_number: str,
    driver_name: str,
    driver_phone: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_ops),
):
    """Dispatch a sealed manifest with vehicle and driver details."""
    result = await db.execute(
        select(Manifest).where(Manifest.manifest_number == manifest_number)
    )
    manifest = result.scalar_one_or_none()
    if not manifest:
        raise HTTPException(status_code=404, detail="Manifest not found")
    if manifest.status != ManifestStatus.SEALED:
        raise HTTPException(status_code=400, detail="Only SEALED manifests can be dispatched")

    manifest.status = ManifestStatus.DISPATCHED
    manifest.vehicle_number = vehicle_number
    manifest.driver_name = driver_name
    manifest.driver_phone = driver_phone
    manifest.dispatched_at = datetime.utcnow()
    await db.commit()

    return {
        "manifest_number": manifest_number,
        "status": "DISPATCHED",
        "vehicle_number": vehicle_number,
        "driver_name": driver_name,
        "dispatched_at": manifest.dispatched_at,
    }


@router.post("/{manifest_number}/receive")
async def receive_manifest(
    manifest_number: str,
    received_count: int,
    discrepancy_awbs: Optional[List[str]] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_ops),
):
    """Mark manifest as received at destination hub."""
    result = await db.execute(
        select(Manifest).where(Manifest.manifest_number == manifest_number)
    )
    manifest = result.scalar_one_or_none()
    if not manifest:
        raise HTTPException(status_code=404, detail="Manifest not found")
    if manifest.status != ManifestStatus.DISPATCHED:
        raise HTTPException(status_code=400, detail="Only DISPATCHED manifests can be received")

    manifest.status = ManifestStatus.RECEIVED
    manifest.received_at = datetime.utcnow()
    await db.commit()

    return {
        "manifest_number": manifest_number,
        "status": "RECEIVED",
        "expected_shipments": manifest.total_shipments,
        "received_count": received_count,
        "discrepancy": manifest.total_shipments - received_count,
        "discrepancy_awbs": discrepancy_awbs or [],
    }


@router.get("/")
async def list_manifests(
    status: Optional[ManifestStatus] = None,
    hub_code: Optional[str] = None,
    manifest_type: Optional[ManifestType] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_ops),
):
    """List manifests with optional filters."""
    query = select(Manifest)
    if status:
        query = query.where(Manifest.status == status)
    if hub_code:
        query = query.where(
            (Manifest.origin_hub_code == hub_code) | (Manifest.destination_hub_code == hub_code)
        )
    if manifest_type:
        query = query.where(Manifest.manifest_type == manifest_type)

    query = query.order_by(Manifest.created_at.desc())
    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar()

    result = await db.execute(query.offset((page - 1) * page_size).limit(page_size))
    return {
        "items": result.scalars().all(),
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{manifest_number}")
async def get_manifest(
    manifest_number: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_ops),
):
    result = await db.execute(
        select(Manifest).where(Manifest.manifest_number == manifest_number)
    )
    manifest = result.scalar_one_or_none()
    if not manifest:
        raise HTTPException(status_code=404, detail="Manifest not found")
    return manifest
