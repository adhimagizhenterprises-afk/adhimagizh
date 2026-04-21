"""
Pydantic schemas for Booking API — request/response models
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, model_validator
import re


class AddressBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    phone: str = Field(..., pattern=r"^[6-9]\d{9}$")
    email: Optional[str] = Field(None, pattern=r"^[\w.-]+@[\w.-]+\.\w{2,}$")
    address_line1: str = Field(..., min_length=5, max_length=200)
    address_line2: Optional[str] = Field(None, max_length=200)
    city: str = Field(..., min_length=2, max_length=50)
    state: str = Field(..., min_length=2, max_length=50)
    pincode: str = Field(..., pattern=r"^\d{6}$")


class BookingCreateRequest(BaseModel):
    # Sender
    sender_name: str = Field(..., min_length=2, max_length=100)
    sender_phone: str = Field(..., pattern=r"^[6-9]\d{9}$")
    sender_email: Optional[str] = None
    sender_address_line1: str = Field(..., min_length=5, max_length=200)
    sender_address_line2: Optional[str] = None
    sender_city: str
    sender_state: str
    sender_pincode: str = Field(..., pattern=r"^\d{6}$")

    # Receiver
    receiver_name: str = Field(..., min_length=2, max_length=100)
    receiver_phone: str = Field(..., pattern=r"^[6-9]\d{9}$")
    receiver_email: Optional[str] = None
    receiver_address_line1: str = Field(..., min_length=5, max_length=200)
    receiver_address_line2: Optional[str] = None
    receiver_city: str
    receiver_state: str
    receiver_pincode: str = Field(..., pattern=r"^\d{6}$")

    # Package
    weight_kg: float = Field(..., gt=0, le=500)
    length_cm: Optional[float] = Field(None, gt=0, le=300)
    width_cm: Optional[float] = Field(None, gt=0, le=300)
    height_cm: Optional[float] = Field(None, gt=0, le=300)
    declared_value: Optional[float] = Field(None, ge=0)
    contents_description: str = Field(..., min_length=3, max_length=200)
    is_fragile: Optional[bool] = False
    is_dangerous_goods: Optional[bool] = False

    # Service
    service_type: str = Field(..., pattern=r"^(EXPRESS|PRIORITY|STANDARD|ECONOMY)$")
    payment_mode: str = Field(..., pattern=r"^(PREPAID|COD|CREDIT)$")
    cod_amount: Optional[float] = Field(None, ge=0)
    pickup_date: str = Field(..., description="YYYY-MM-DD format")
    reference_number: Optional[str] = Field(None, max_length=100)
    instructions: Optional[str] = Field(None, max_length=500)

    @model_validator(mode="after")
    def validate_cod(self):
        if self.payment_mode == "COD" and not self.cod_amount:
            raise ValueError("cod_amount is required when payment_mode is COD")
        if self.payment_mode != "COD" and self.cod_amount:
            self.cod_amount = None
        return self

    @field_validator("pickup_date")
    @classmethod
    def validate_pickup_date(cls, v: str) -> str:
        try:
            dt = datetime.strptime(v, "%Y-%m-%d")
            if dt.date() < datetime.today().date():
                raise ValueError("Pickup date cannot be in the past")
        except ValueError as e:
            raise ValueError(f"Invalid pickup_date: {e}")
        return v


class BookingResponse(BaseModel):
    id: str
    awb_number: str
    status: str
    sender_name: str
    sender_city: str
    sender_pincode: str
    receiver_name: str
    receiver_phone: str
    receiver_city: str
    receiver_pincode: str
    weight_kg: float
    chargeable_weight_kg: float
    service_type: str
    payment_mode: str
    cod_amount: Optional[float]
    freight_charge: float
    fuel_surcharge: float
    gst_amount: float
    total_charge: float
    zone: Optional[str]
    pickup_date: Optional[datetime]
    expected_delivery_date: Optional[datetime]
    label_url: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class BookingListResponse(BaseModel):
    items: List[BookingResponse]
    total: int
    page: int
    page_size: int
    pages: int


class BulkBookingRequest(BaseModel):
    bookings: List[BookingCreateRequest] = Field(..., min_length=1, max_length=100)


class CancelBookingRequest(BaseModel):
    reason: str = Field(..., min_length=5, max_length=500)


class PriceCalculateRequest(BaseModel):
    sender_pincode: str = Field(..., pattern=r"^\d{6}$")
    receiver_pincode: str = Field(..., pattern=r"^\d{6}$")
    weight_kg: float = Field(..., gt=0, le=500)
    length_cm: Optional[float] = None
    width_cm: Optional[float] = None
    height_cm: Optional[float] = None
    service_type: str = Field(default="STANDARD")
    payment_mode: str = Field(default="PREPAID")
    cod_amount: Optional[float] = None
    declared_value: Optional[float] = None


class PriceCalculateResponse(BaseModel):
    zone: str
    chargeable_weight_kg: float
    freight_charge: float
    fuel_surcharge: float
    docket_charge: float
    cod_charge: float
    insurance_charge: float
    gst_amount: float
    total_charge: float
    all_services: dict
