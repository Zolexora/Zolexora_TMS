import datetime
from decimal import Decimal
import uuid
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.modules.customers.models import CustomerStatus


class CustomerBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=160)
    contact_person: Optional[str] = Field(None, max_length=120)
    email: Optional[str] = Field(None, max_length=160)
    phone: Optional[str] = Field(None, max_length=32)
    billing_address: Optional[str] = None
    gstin: Optional[str] = Field(None, max_length=15)
    pan: Optional[str] = Field(None, max_length=10)
    payment_terms_days: int = Field(default=30, ge=0, le=365)
    credit_limit: Decimal = Field(default=Decimal("0.0"), ge=Decimal("0.0"))
    notes: Optional[str] = None


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=160)
    contact_person: Optional[str] = Field(None, max_length=120)
    email: Optional[str] = Field(None, max_length=160)
    phone: Optional[str] = Field(None, max_length=32)
    billing_address: Optional[str] = None
    gstin: Optional[str] = Field(None, max_length=15)
    pan: Optional[str] = Field(None, max_length=10)
    payment_terms_days: Optional[int] = Field(None, ge=0, le=365)
    credit_limit: Optional[Decimal] = Field(None, ge=Decimal("0.0"))
    status: Optional[CustomerStatus] = None
    notes: Optional[str] = None


class CustomerResponse(CustomerBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organisation_id: uuid.UUID
    status: CustomerStatus
    created_at: datetime.datetime
    updated_at: datetime.datetime
