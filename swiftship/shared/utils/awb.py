"""
AWB (Air Waybill) Number Generator for SwiftShip
Format: SS + YYYYMMDD + 6-digit-sequence + check-digit
Example: SS202412150001271
"""
import random
import hashlib
from datetime import date


def generate_awb(prefix: str = "SS") -> str:
    """Generate a unique AWB number."""
    date_str = date.today().strftime("%Y%m%d")
    seq = str(random.randint(100000, 999999))
    raw = f"{prefix}{date_str}{seq}"
    check = _luhn_check_digit(raw)
    return f"{raw}{check}"


def _luhn_check_digit(number: str) -> str:
    """Generate a Luhn check digit for AWB validation."""
    digits = [int(c) if c.isdigit() else ord(c) % 10 for c in number]
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    total = sum(odd_digits)
    for d in even_digits:
        total += sum(divmod(d * 2, 10))
    return str((10 - (total % 10)) % 10)


def validate_awb(awb: str) -> bool:
    """Validate an AWB number using Luhn check."""
    if len(awb) < 10:
        return False
    check = awb[-1]
    return _luhn_check_digit(awb[:-1]) == check


def generate_manifest_number(hub_code: str) -> str:
    """Generate manifest number: HUB-YYYYMMDD-SEQ."""
    date_str = date.today().strftime("%Y%m%d")
    seq = str(random.randint(1000, 9999))
    return f"MFT-{hub_code}-{date_str}-{seq}"


def generate_bag_number(hub_code: str, destination_code: str) -> str:
    """Generate bag/bag tag number."""
    date_str = date.today().strftime("%Y%m%d")
    seq = str(random.randint(100, 999))
    return f"BAG-{hub_code}-{destination_code}-{date_str}-{seq}"


# Zone matrix (simplified — origin_state → destination_state → zone)
ZONE_MATRIX = {
    "SAME_CITY": "A",
    "SAME_STATE": "B",
    "METRO_TO_METRO": "C",
    "REST_OF_INDIA": "D",
    "SPECIAL_ZONE": "E",  # NE, J&K, Andaman
}

SPECIAL_PINCODES = {
    "J&K": list(range(180000, 195000)),
    "ANDAMAN": list(range(744000, 745000)),
}


def get_weight_slab(weight_kg: float) -> float:
    """Round up weight to nearest 0.5kg slab."""
    slabs = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 5.0, 7.5, 10.0, 15.0, 20.0]
    for slab in slabs:
        if weight_kg <= slab:
            return slab
    return weight_kg  # Above 20kg, actual weight


def calculate_volumetric_weight(length_cm: float, width_cm: float, height_cm: float) -> float:
    """Calculate volumetric weight. Divisor = 5000 (standard courier)."""
    return (length_cm * width_cm * height_cm) / 5000


def get_chargeable_weight(actual_kg: float, vol_kg: float) -> float:
    """Return max of actual and volumetric weight."""
    return max(actual_kg, vol_kg)
