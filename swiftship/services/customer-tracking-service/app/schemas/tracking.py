from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class TrackingEventResponse(BaseModel):
    status: str
    location: Optional[str]
    hub_code: Optional[str]
    remarks: Optional[str]
    event_time: datetime

    model_config = {"from_attributes": True}


class TrackingResponse(BaseModel):
    awb_number: str
    current_status: str
    current_location: Optional[str]
    origin: Optional[str]
    destination: Optional[str]
    expected_delivery: Optional[datetime]
    last_updated: Optional[datetime]
    events: List[TrackingEventResponse]


class TrackingSearchResult(BaseModel):
    awb_number: str
    status: str
    origin: Optional[str]
    destination: Optional[str]
    receiver_name: Optional[str]
    score: float
