import datetime
import uuid
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.modules.vendors.models import VendorType, VendorStatus


class VendorBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=160)
    vendor_type: VendorType = Field(default=VendorType.FLEET_SUPPLIER)
    contact_person: Optional[str] = Field(None, max_length=120)
    email: Optional[str] = Field(None, max_length=160)
    phone: Optional[str] = Field(None, max_length=32)
    address: Optional[str] = None
    gstin: Optional[str] = Field(None, max_length=15)
    pan: Optional[str] = Field(None, max_length=10)
    bank_account_name: Optional[str] = Field(None, max_length=120)
    bank_account_number: Optional[str] = Field(None, max_length=64)
    bank_ifsc: Optional[str] = Field(None, max_length=20)
    bank_name: Optional[str] = Field(None, max_length=120)


class VendorCreate(VendorBase):
    pass


class VendorUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=160)
    vendor_type: Optional[VendorType] = None
    contact_person: Optional[str] = Field(None, max_length=120)
    email: Optional[str] = Field(None, max_length=160)
    phone: Optional[str] = Field(None, max_length=32)
    address: Optional[str] = None
    gstin: Optional[str] = Field(None, max_length=15)
    pan: Optional[str] = Field(None, max_length=10)
    bank_account_name: Optional[str] = Field(None, max_length=120)
    bank_account_number: Optional[str] = Field(None, max_length=64)
    bank_ifsc: Optional[str] = Field(None, max_length=20)
    bank_name: Optional[str] = Field(None, max_length=120)
    status: Optional[VendorStatus] = None


class VendorResponse(VendorBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organisation_id: uuid.UUID
    status: VendorStatus
    created_at: datetime.datetime
    updated_at: datetime.datetime
