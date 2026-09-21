import datetime
from decimal import Decimal
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.modules.trips.models import TripStatus


class TripStartRequest(BaseModel):
    start_odometer: Decimal = Field(..., ge=Decimal("0.0"))
    start_location: Dict[str, Any] = Field(default_factory=dict)


class TripCompleteRequest(BaseModel):
    end_odometer: Decimal = Field(..., ge=Decimal("0.0"))
    end_location: Dict[str, Any] = Field(default_factory=dict)
    toll_amount: Decimal = Field(default=Decimal("0.0"), ge=Decimal("0.0"))
    fuel_amount: Decimal = Field(default=Decimal("0.0"), ge=Decimal("0.0"))
    parking_amount: Decimal = Field(default=Decimal("0.0"), ge=Decimal("0.0"))
    waiting_minutes: int = Field(default=0, ge=0)
    pod_attachment_url: Optional[str] = None
    pod_notes: Optional[str] = None
    notes: Optional[str] = None


class TripMilestoneRequest(BaseModel):
    event_type: str = Field(..., min_length=2, max_length=64)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    notes: Optional[str] = None


class TripReceiptAddRequest(BaseModel):
    receipt_type: str = Field(..., description="e.g. fuel, toll, parking, maintenance")
    amount: Decimal = Field(..., ge=Decimal("0.0"))
    receipt_url: str = Field(..., min_length=5)
    notes: Optional[str] = None


class TripEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    trip_id: uuid.UUID
    event_type: str
    timestamp: datetime.datetime
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    notes: Optional[str] = None


class TripResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    trip_number: str
    organisation_id: uuid.UUID
    duty_id: uuid.UUID
    driver_id: uuid.UUID
    vehicle_id: uuid.UUID
    start_odometer: Decimal
    end_odometer: Optional[Decimal] = None
    total_distance_km: Optional[Decimal] = None
    start_timestamp: Optional[datetime.datetime] = None
    end_timestamp: Optional[datetime.datetime] = None
    start_location: Dict[str, Any] = Field(default_factory=dict)
    end_location: Dict[str, Any] = Field(default_factory=dict)
    toll_amount: Decimal
    fuel_amount: Decimal
    parking_amount: Decimal
    waiting_minutes: int
    status: TripStatus
    pod_attachment_url: Optional[str] = None
    pod_notes: Optional[str] = None
    pod_uploaded_at: Optional[datetime.datetime] = None
    operational_receipts: List[Dict[str, Any]] = Field(default_factory=list)
    notes: Optional[str] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime
