import datetime
import uuid
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.modules.drivers.models import DriverType, DriverStatus


class DriverBase(BaseModel):
    vendor_id: Optional[uuid.UUID] = None
    full_name: str = Field(..., min_length=2, max_length=160)
    phone: str = Field(..., min_length=7, max_length=32)
    alternate_phone: Optional[str] = Field(None, max_length=32)
    email: Optional[str] = Field(None, max_length=160)
    license_number: str = Field(..., min_length=4, max_length=64)
    license_type: str = Field(default="HMV", max_length=64)
    license_expiry: Optional[datetime.date] = None
    badge_number: Optional[str] = Field(None, max_length=64)
    aadhaar_last4: Optional[str] = Field(None, min_length=4, max_length=4)
    pan: Optional[str] = Field(None, max_length=10)
    driver_type: DriverType = Field(default=DriverType.PERMANENT)
    avatar_url: Optional[str] = None
    documents: dict = Field(default_factory=dict)


class DriverCreate(DriverBase):
    pass


class DriverUpdate(BaseModel):
    vendor_id: Optional[uuid.UUID] = None
    full_name: Optional[str] = Field(None, min_length=2, max_length=160)
    phone: Optional[str] = Field(None, min_length=7, max_length=32)
    alternate_phone: Optional[str] = Field(None, max_length=32)
    email: Optional[str] = Field(None, max_length=160)
    license_number: Optional[str] = Field(None, min_length=4, max_length=64)
    license_type: Optional[str] = Field(None, max_length=64)
    license_expiry: Optional[datetime.date] = None
    badge_number: Optional[str] = Field(None, max_length=64)
    aadhaar_last4: Optional[str] = Field(None, min_length=4, max_length=4)
    pan: Optional[str] = Field(None, max_length=10)
    driver_type: Optional[DriverType] = None
    status: Optional[DriverStatus] = None
    avatar_url: Optional[str] = None
    documents: Optional[dict] = None


class DriverResponse(DriverBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organisation_id: uuid.UUID
    status: DriverStatus
    created_at: datetime.datetime
    updated_at: datetime.datetime
