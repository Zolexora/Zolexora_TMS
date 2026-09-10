import datetime
from decimal import Decimal
import uuid
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.modules.vehicles.models import (
    VehicleBodyType,
    VehicleOwnershipType,
    FuelType,
    VehicleOperationalStatus,
)


class VehicleBase(BaseModel):
    vendor_id: Optional[uuid.UUID] = None
    registration_number: str = Field(..., min_length=4, max_length=32)
    vehicle_type: VehicleBodyType = Field(default=VehicleBodyType.TRUCK)
    ownership_type: VehicleOwnershipType = Field(default=VehicleOwnershipType.OWNED)
    make: Optional[str] = Field(None, max_length=64)
    model: Optional[str] = Field(None, max_length=64)
    year: Optional[int] = Field(None, ge=1970, le=2050)
    fuel_type: FuelType = Field(default=FuelType.DIESEL)
    payload_capacity_kg: Optional[Decimal] = Field(None, ge=Decimal("0.0"))
    volume_cft: Optional[Decimal] = Field(None, ge=Decimal("0.0"))
    odometer_km: Decimal = Field(default=Decimal("0.0"), ge=Decimal("0.0"))
    fastag_id: Optional[str] = Field(None, max_length=64)
    gps_device_id: Optional[str] = Field(None, max_length=64)
    rc_number: Optional[str] = Field(None, max_length=64)
    rc_expiry: Optional[datetime.date] = None
    fitness_expiry: Optional[datetime.date] = None
    permit_expiry: Optional[datetime.date] = None
    insurance_expiry: Optional[datetime.date] = None
    puc_expiry: Optional[datetime.date] = None
    documents: dict = Field(default_factory=dict)


class VehicleCreate(VehicleBase):
    pass


class VehicleUpdate(BaseModel):
    vendor_id: Optional[uuid.UUID] = None
    registration_number: Optional[str] = Field(None, min_length=4, max_length=32)
    vehicle_type: Optional[VehicleBodyType] = None
    ownership_type: Optional[VehicleOwnershipType] = None
    make: Optional[str] = Field(None, max_length=64)
    model: Optional[str] = Field(None, max_length=64)
    year: Optional[int] = Field(None, ge=1970, le=2050)
    fuel_type: Optional[FuelType] = None
    payload_capacity_kg: Optional[Decimal] = Field(None, ge=Decimal("0.0"))
    volume_cft: Optional[Decimal] = Field(None, ge=Decimal("0.0"))
    odometer_km: Optional[Decimal] = Field(None, ge=Decimal("0.0"))
    fastag_id: Optional[str] = Field(None, max_length=64)
    gps_device_id: Optional[str] = Field(None, max_length=64)
    rc_number: Optional[str] = Field(None, max_length=64)
    rc_expiry: Optional[datetime.date] = None
    fitness_expiry: Optional[datetime.date] = None
    permit_expiry: Optional[datetime.date] = None
    insurance_expiry: Optional[datetime.date] = None
    puc_expiry: Optional[datetime.date] = None
    status: Optional[VehicleOperationalStatus] = None
    documents: Optional[dict] = None


class VehicleResponse(VehicleBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organisation_id: uuid.UUID
    status: VehicleOperationalStatus
    created_at: datetime.datetime
    updated_at: datetime.datetime
