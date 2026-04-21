"""
Saved Addresses API — v1 endpoints
"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.shipment import SavedAddress
from app.core.auth import get_current_user

router = APIRouter()


@router.get("/", response_model=List[dict])
async def list_addresses(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List all saved addresses for the current customer."""
    result = await db.execute(
        select(SavedAddress).where(SavedAddress.customer_id == current_user["user_id"])
    )
    addresses = result.scalars().all()
    return [
        {
            "id": str(addr.id),
            "label": addr.label,
            "name": addr.name,
            "phone": addr.phone,
            "email": addr.email,
            "address_line1": addr.address_line1,
            "address_line2": addr.address_line2,
            "city": addr.city,
            "state": addr.state,
            "pincode": addr.pincode,
            "is_default": addr.is_default,
        }
        for addr in addresses
    ]


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_address(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Save a new address for the current customer."""
    address = SavedAddress(
        customer_id=current_user["user_id"],
        label=payload.get("label"),
        name=payload["name"],
        phone=payload["phone"],
        email=payload.get("email"),
        address_line1=payload["address_line1"],
        address_line2=payload.get("address_line2"),
        city=payload["city"],
        state=payload["state"],
        pincode=payload["pincode"],
        is_default=payload.get("is_default", False),
    )
    db.add(address)
    await db.commit()
    await db.refresh(address)
    return {"id": str(address.id), "message": "Address saved"}


@router.put("/{address_id}")
async def update_address(
    address_id: UUID,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Update a saved address."""
    result = await db.execute(
        select(SavedAddress).where(
            SavedAddress.id == address_id,
            SavedAddress.customer_id == current_user["user_id"],
        )
    )
    address = result.scalar_one_or_none()
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")

    for field in ["label", "name", "phone", "email", "address_line1", "address_line2",
                  "city", "state", "pincode", "is_default"]:
        if field in payload:
            setattr(address, field, payload[field])

    await db.commit()
    return {"message": "Address updated"}


@router.delete("/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_address(
    address_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Delete a saved address."""
    result = await db.execute(
        select(SavedAddress).where(
            SavedAddress.id == address_id,
            SavedAddress.customer_id == current_user["user_id"],
        )
    )
    address = result.scalar_one_or_none()
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")

    await db.delete(address)
    await db.commit()
