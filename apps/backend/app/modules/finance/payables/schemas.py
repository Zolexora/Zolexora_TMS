import uuid
import datetime
from typing import List, Optional
from decimal import Decimal
from pydantic import BaseModel, Field


class PayableLineCreate(BaseModel):
    description: str
    amount: Decimal
    is_deduction: bool = False


class PayableCreateRequest(BaseModel):
    vendor_id: Optional[uuid.UUID] = None
    driver_id: Optional[uuid.UUID] = None
    duty_id: Optional[uuid.UUID] = None
    reference_number: str
    currency: str = "INR"
    notes: Optional[str] = None
    lines: List[PayableLineCreate]


class PayableLineResponse(BaseModel):
    id: uuid.UUID
    description: str
    amount: Decimal
    is_deduction: bool

    class Config:
        from_attributes = True


class PayableResponse(BaseModel):
    id: uuid.UUID
    organisation_id: uuid.UUID
    vendor_id: Optional[uuid.UUID]
    driver_id: Optional[uuid.UUID]
    duty_id: Optional[uuid.UUID]
    reference_number: str
    subtotal: Decimal
    deductions: Decimal
    advances: Decimal
    grand_total: Decimal
    currency: str
    status: str
    notes: Optional[str]
    created_at: datetime.datetime
    lines: List[PayableLineResponse] = []

    class Config:
        from_attributes = True


class SettlementCreateRequest(BaseModel):
    amount: Decimal
    settlement_date: datetime.date = Field(default_factory=datetime.date.today)
    payment_reference: Optional[str] = None
    notes: Optional[str] = None


class SettlementResponse(BaseModel):
    id: uuid.UUID
    payable_id: uuid.UUID
    amount: Decimal
    settlement_date: datetime.datetime
    payment_reference: Optional[str]
    notes: Optional[str]
    created_at: datetime.datetime

    class Config:
        from_attributes = True
