from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class DeliveryTaskResponse(BaseModel):
    id: str
    awb_number: str
    status: str
    receiver_name: Optional[str]
    receiver_phone: Optional[str]
    delivery_address: Optional[str]
    delivery_city: Optional[str]
    is_cod: bool
    cod_amount: float
    sequence_number: Optional[int]
    scheduled_date: Optional[datetime]

    model_config = {"from_attributes": True}


class DeliveryAttemptRequest(BaseModel):
    result: str
    remarks: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class PODSubmitRequest(BaseModel):
    delivered_to: str
    receiver_relation: str
    otp_entered: str
    cod_collected: bool = False
    cod_amount: float = 0
    cod_method: str = "CASH"


class PODResponse(BaseModel):
    id: str
    awb_number: str
    delivered_to: str
    photo_url: Optional[str]
    signature_url: Optional[str]
    otp_verified: bool
    delivered_at: Optional[datetime]

    model_config = {"from_attributes": True}
