"""
PricingService — zone-based courier pricing engine
Supports: weight slabs, zone matrix, service type multipliers,
          fuel surcharge, GST, COD charges, declared value insurance
"""
from app.core.config import settings
from shared.utils.awb import get_weight_slab, ZONE_MATRIX

# ─── Zone rate matrix (₹ per kg per zone) ────────────────────────────────────
ZONE_BASE_RATES = {
    "A": 20.0,   # Same city
    "B": 28.0,   # Same state
    "C": 35.0,   # Metro-to-metro
    "D": 42.0,   # Rest of India
    "E": 65.0,   # Special zones (NE, J&K, Andaman)
}

# Minimum charge per zone (₹)
ZONE_MINIMUM_CHARGE = {
    "A": 50,
    "B": 75,
    "C": 100,
    "D": 120,
    "E": 180,
}

# Pincode → state mapping (simplified; production uses full DB table)
PINCODE_STATE_MAP = {
    "1": "Delhi", "2": "Uttar Pradesh", "3": "Rajasthan",
    "4": "Maharashtra/Gujarat", "5": "Andhra Pradesh/Telangana/Karnataka",
    "6": "Tamil Nadu/Kerala", "7": "West Bengal/NE",
    "8": "Odisha/Bihar", "9": "Punjab/HP/J&K",
}

METRO_PINCODES = {"110", "400", "600", "700", "560", "500"}  # Delhi, Mumbai, Chennai, Kolkata, Bengaluru, Hyderabad


class PricingService:

    def _get_zone(self, sender_pin: str, receiver_pin: str) -> str:
        """Determine shipping zone from sender and receiver pincodes."""
        if sender_pin[:3] == receiver_pin[:3]:
            return "A"   # Same city
        if sender_pin[0] == receiver_pin[0]:
            return "B"   # Same state (rough approximation)
        sender_metro = any(sender_pin.startswith(m) for m in METRO_PINCODES)
        receiver_metro = any(receiver_pin.startswith(m) for m in METRO_PINCODES)
        if sender_metro and receiver_metro:
            return "C"   # Metro to metro
        # Special zones (Assam 785xxx, Manipur 795xxx, J&K 180xxx, etc.)
        special_prefixes = ("785", "795", "796", "797", "798", "180", "181", "182", "744")
        if any(receiver_pin.startswith(p) for p in special_prefixes):
            return "E"
        return "D"       # Rest of India

    async def calculate(
        self,
        sender_pincode: str,
        receiver_pincode: str,
        chargeable_weight_kg: float,
        service_type: str,
        payment_mode: str,
        cod_amount: float = 0,
        declared_value: float = 0,
    ) -> dict:
        """
        Full pricing calculation returning itemised charges.
        All amounts in INR.
        """
        zone = self._get_zone(sender_pincode, receiver_pincode)
        slab = get_weight_slab(chargeable_weight_kg)
        base_rate = ZONE_BASE_RATES[zone]
        multiplier = settings.SERVICE_MULTIPLIERS.get(service_type, 1.0)

        # Freight charge = base_rate × weight × service_multiplier
        freight = max(
            base_rate * slab * multiplier,
            ZONE_MINIMUM_CHARGE[zone] * multiplier,
        )
        freight = round(freight, 2)

        # Fuel surcharge (% of freight)
        fuel_surcharge = round(freight * settings.FUEL_SURCHARGE_PCT / 100, 2)

        # Docket charge (flat)
        docket = settings.DOCKET_CHARGE

        # COD handling charge
        cod_charge = 0.0
        if payment_mode == "COD" and cod_amount > 0:
            cod_charge = round(max(cod_amount * settings.COD_CHARGE_PCT / 100, 30), 2)

        # Declared value insurance (0.5% of declared value, min ₹25)
        insurance = 0.0
        if declared_value > 0:
            insurance = round(max(declared_value * 0.005, 25), 2)

        # Subtotal before GST
        subtotal = freight + fuel_surcharge + docket + cod_charge + insurance

        # GST (18%)
        gst = round(subtotal * settings.GST_PCT / 100, 2)

        total = round(subtotal + gst, 2)

        return {
            "zone": zone,
            "chargeable_weight_kg": slab,
            "freight_charge": freight,
            "fuel_surcharge": fuel_surcharge,
            "docket_charge": docket,
            "cod_charge": cod_charge,
            "insurance_charge": insurance,
            "subtotal": subtotal,
            "gst_amount": gst,
            "total_charge": total,
            # Quotes for all service types (for comparison display)
            "all_services": self._quote_all_services(zone, slab),
        }

    def _quote_all_services(self, zone: str, slab: float) -> dict:
        """Return quick quotes for all service types at the given zone/weight."""
        base = ZONE_BASE_RATES[zone]
        quotes = {}
        for svc, mult in settings.SERVICE_MULTIPLIERS.items():
            freight = round(max(base * slab * mult, ZONE_MINIMUM_CHARGE[zone] * mult), 2)
            fuel = round(freight * settings.FUEL_SURCHARGE_PCT / 100, 2)
            sub = freight + fuel + settings.DOCKET_CHARGE
            gst = round(sub * settings.GST_PCT / 100, 2)
            quotes[svc] = {
                "freight": freight,
                "total": round(sub + gst, 2),
            }
        return quotes

    async def check_serviceability(self, pincode: str) -> dict:
        """Check if a pincode is serviceable and available service types."""
        # In production: query serviceability DB / partner API
        non_serviceable = ["999999", "000000"]
        oda_pincodes = ["110099", "400099"]  # Out-of-delivery-area

        serviceable = pincode not in non_serviceable
        is_oda = pincode in oda_pincodes

        return {
            "pincode": pincode,
            "serviceable": serviceable,
            "is_oda": is_oda,
            "oda_surcharge": 50 if is_oda else 0,
            "available_services": ["STANDARD", "ECONOMY"] if is_oda else ["EXPRESS", "PRIORITY", "STANDARD", "ECONOMY"],
            "cod_available": not is_oda,
            "estimated_transit_days": {
                "EXPRESS": 1, "PRIORITY": 2, "STANDARD": 4, "ECONOMY": 6,
            },
        }
