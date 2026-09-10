import uuid
import datetime
from typing import List, Optional
from decimal import Decimal
from pydantic import BaseModel, Field


class PaymentAllocationCreate(BaseModel):
    invoice_id: uuid.UUID
    amount_allocated: Decimal


class PaymentCreateRequest(BaseModel):
    customer_id: Optional[uuid.UUID] = None
    provider: str
    provider_transaction_id: Optional[str] = None
    payment_method: Optional[str] = None
    amount: Decimal
    currency: str = "INR"
    payment_date: datetime.date = Field(default_factory=datetime.date.today)
    notes: Optional[str] = None
    allocations: List[PaymentAllocationCreate] = []


class PaymentAllocationResponse(BaseModel):
    id: uuid.UUID
    invoice_id: uuid.UUID
    amount_allocated: Decimal
    
    class Config:
        from_attributes = True


class PaymentResponse(BaseModel):
    id: uuid.UUID
    organisation_id: uuid.UUID
    customer_id: Optional[uuid.UUID]
    provider: str
    provider_transaction_id: Optional[str]
    payment_method: Optional[str]
    amount: Decimal
    unallocated_amount: Decimal
    currency: str
    payment_date: datetime.datetime
    status: str
    notes: Optional[str]
    allocations: List[PaymentAllocationResponse] = []
    
    class Config:
        from_attributes = True
