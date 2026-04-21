"""
BookingService — core business logic for shipment creation
"""
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shipment import Shipment, ShipmentStatus
from app.schemas.booking import BookingCreateRequest
from app.services.pricing_service import PricingService
from app.services.label_service import LabelService
from shared.utils.awb import generate_awb, get_chargeable_weight, calculate_volumetric_weight


class BookingService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.pricing = PricingService()
        self.label = LabelService()

    async def create_booking(
        self, request: BookingCreateRequest, customer_id: str
    ) -> Shipment:
        """
        Full booking creation flow:
        1. Generate AWB
        2. Calculate volumetric weight
        3. Price the shipment
        4. Persist to DB
        5. Trigger label generation (async)
        """
        # Step 1: AWB
        awb = generate_awb(prefix="SS")

        # Step 2: Weights
        vol_weight = 0.0
        if request.length_cm and request.width_cm and request.height_cm:
            vol_weight = calculate_volumetric_weight(
                request.length_cm, request.width_cm, request.height_cm
            )
        chargeable = get_chargeable_weight(request.weight_kg, vol_weight)

        # Step 3: Pricing
        price = await self.pricing.calculate(
            sender_pincode=request.sender_pincode,
            receiver_pincode=request.receiver_pincode,
            chargeable_weight_kg=chargeable,
            service_type=request.service_type,
            payment_mode=request.payment_mode,
            cod_amount=request.cod_amount or 0,
            declared_value=request.declared_value or 0,
        )

        # Step 4: Expected delivery
        edd = self._compute_edd(request.pickup_date, request.service_type)

        # Step 5: Create DB record
        shipment = Shipment(
            awb_number=awb,
            customer_id=customer_id,
            # Sender
            sender_name=request.sender_name,
            sender_phone=request.sender_phone,
            sender_email=request.sender_email,
            sender_address_line1=request.sender_address_line1,
            sender_address_line2=request.sender_address_line2,
            sender_city=request.sender_city,
            sender_state=request.sender_state,
            sender_pincode=request.sender_pincode,
            # Receiver
            receiver_name=request.receiver_name,
            receiver_phone=request.receiver_phone,
            receiver_email=request.receiver_email,
            receiver_address_line1=request.receiver_address_line1,
            receiver_address_line2=request.receiver_address_line2,
            receiver_city=request.receiver_city,
            receiver_state=request.receiver_state,
            receiver_pincode=request.receiver_pincode,
            # Package
            weight_kg=request.weight_kg,
            length_cm=request.length_cm,
            width_cm=request.width_cm,
            height_cm=request.height_cm,
            volumetric_weight_kg=vol_weight,
            chargeable_weight_kg=chargeable,
            declared_value=request.declared_value or 0,
            contents_description=request.contents_description,
            is_fragile=request.is_fragile or False,
            # Service
            service_type=request.service_type,
            payment_mode=request.payment_mode,
            cod_amount=request.cod_amount or 0,
            # Pricing
            freight_charge=price["freight_charge"],
            fuel_surcharge=price["fuel_surcharge"],
            docket_charge=price["docket_charge"],
            gst_amount=price["gst_amount"],
            total_charge=price["total_charge"],
            zone=price["zone"],
            # Dates
            pickup_date=datetime.strptime(request.pickup_date, "%Y-%m-%d") if isinstance(request.pickup_date, str) else request.pickup_date,
            expected_delivery_date=edd,
            # Misc
            reference_number=request.reference_number,
            instructions=request.instructions,
            status=ShipmentStatus.BOOKING_CREATED,
        )

        self.db.add(shipment)
        await self.db.commit()
        await self.db.refresh(shipment)

        # Async label generation (non-blocking)
        # In production this would be a Celery task or background job
        # await self.label.generate_async(shipment)

        return shipment

    def _compute_edd(self, pickup_date: str, service_type: str) -> datetime:
        """Compute Expected Delivery Date from pickup date and service type."""
        SERVICE_DAYS = {
            "EXPRESS": 1,
            "PRIORITY": 2,
            "STANDARD": 4,
            "ECONOMY": 6,
        }
        if isinstance(pickup_date, str):
            base = datetime.strptime(pickup_date, "%Y-%m-%d")
        else:
            base = pickup_date
        days = SERVICE_DAYS.get(service_type, 4)
        # Skip Sundays
        edd = base
        added = 0
        while added < days:
            edd += timedelta(days=1)
            if edd.weekday() != 6:  # 6 = Sunday
                added += 1
        return edd
