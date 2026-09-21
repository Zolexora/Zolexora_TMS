import datetime
import uuid
from typing import List, Optional
from decimal import Decimal
from pydantic import BaseModel, Field


class InvoiceCreateRequest(BaseModel):
    customer_id: uuid.UUID
    billing_record_ids: List[uuid.UUID]
    invoice_date: datetime.date = Field(default_factory=datetime.date.today)
    due_date: datetime.date
    notes: Optional[str] = None
    terms: Optional[str] = None


class InvoiceResponse(BaseModel):
    id: uuid.UUID
    invoice_number: str
    organisation_id: uuid.UUID
    customer_id: uuid.UUID
    invoice_date: datetime.date
    due_date: datetime.date
    subtotal: Decimal
    discount_amount: Decimal
    taxable_amount: Decimal
    tax_amount: Decimal
    grand_total: Decimal
    amount_paid: Decimal
    amount_due: Decimal
    currency: str
    status: str
    notes: Optional[str]
    terms: Optional[str]
    
    class Config:
        from_attributes = True
