"""
Pricing API — calculate rates and check serviceability
"""
from fastapi import APIRouter, HTTPException
from app.schemas.booking import PriceCalculateRequest, PriceCalculateResponse
from app.services.pricing_service import PricingService
from shared.utils.awb import calculate_volumetric_weight, get_chargeable_weight

router = APIRouter()
pricing_service = PricingService()


@router.post("/calculate", response_model=PriceCalculateResponse)
async def calculate_shipping_price(request: PriceCalculateRequest):
    """
    Calculate shipping charges for given origin, destination, weight and service.
    Public endpoint — no auth needed (used in booking form before login).
    """
    vol_weight = 0.0
    if request.length_cm and request.width_cm and request.height_cm:
        vol_weight = calculate_volumetric_weight(
            request.length_cm, request.width_cm, request.height_cm
        )
    chargeable = get_chargeable_weight(request.weight_kg, vol_weight)

    price = await pricing_service.calculate(
        sender_pincode=request.sender_pincode,
        receiver_pincode=request.receiver_pincode,
        chargeable_weight_kg=chargeable,
        service_type=request.service_type,
        payment_mode=request.payment_mode,
        cod_amount=request.cod_amount or 0,
        declared_value=request.declared_value or 0,
    )
    return price


@router.get("/serviceability/{pincode}")
async def check_serviceability(pincode: str):
    """
    Check if a pincode is serviceable, available service types, and ODA surcharges.
    """
    if len(pincode) != 6 or not pincode.isdigit():
        raise HTTPException(status_code=400, detail="Invalid pincode format")
    return await pricing_service.check_serviceability(pincode)


@router.get("/zones")
async def list_zones():
    """Return zone definitions and base rates."""
    return {
        "zones": {
            "A": {"name": "Same City",        "base_rate_per_kg": 20.0, "min_charge": 50},
            "B": {"name": "Same State",        "base_rate_per_kg": 28.0, "min_charge": 75},
            "C": {"name": "Metro to Metro",    "base_rate_per_kg": 35.0, "min_charge": 100},
            "D": {"name": "Rest of India",     "base_rate_per_kg": 42.0, "min_charge": 120},
            "E": {"name": "Special Zones",     "base_rate_per_kg": 65.0, "min_charge": 180},
        },
        "gst_percent": 18,
        "fuel_surcharge_percent": 18,
        "cod_charge_percent": 1.5,
    }
