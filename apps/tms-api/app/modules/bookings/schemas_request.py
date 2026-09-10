import datetime
from decimal import Decimal
import uuid
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.modules.bookings.models_request import (
    BookingRequestStatus,
    BookingServiceType,
    BookingType,
)


class BookingRequestBase(BaseModel):
    customer_id: uuid.UUID
    booking_type: BookingType = Field(default=BookingType.SPOT)
    service_type: BookingServiceType = Field(default=BookingServiceType.CARGO)
    pickup_address: str = Field(..., min_length=3)
    pickup_lat: Optional[float] = None
    pickup_lng: Optional[float] = None
    drop_address: str = Field(..., min_length=3)
    drop_lat: Optional[float] = None
    drop_lng: Optional[float] = None
    pickup_datetime: datetime.datetime
    expected_completion_datetime: Optional[datetime.datetime] = None
    passenger_info: Dict[str, Any] = Field(default_factory=dict)
    cargo_info: Dict[str, Any] = Field(default_factory=dict)
    vehicle_requirements: Dict[str, Any] = Field(default_factory=dict)
    special_instructions: Optional[str] = None
    source: str = Field(default="MANUAL")
    estimated_pricing: Optional[Decimal] = None


class BookingRequestCreate(BookingRequestBase):
    pass


class BookingRequestUpdate(BaseModel):
    pickup_address: Optional[str] = None
    pickup_lat: Optional[float] = None
    pickup_lng: Optional[float] = None
    drop_address: Optional[str] = None
    drop_lat: Optional[float] = None
    drop_lng: Optional[float] = None
    pickup_datetime: Optional[datetime.datetime] = None
    expected_completion_datetime: Optional[datetime.datetime] = None
    passenger_info: Optional[Dict[str, Any]] = None
    cargo_info: Optional[Dict[str, Any]] = None
    vehicle_requirements: Optional[Dict[str, Any]] = None
    special_instructions: Optional[str] = None
    estimated_pricing: Optional[Decimal] = None


class BookingRequestResponse(BookingRequestBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    request_number: str
    organisation_id: uuid.UUID
    status: BookingRequestStatus
    created_by_user_id: Optional[uuid.UUID] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime
