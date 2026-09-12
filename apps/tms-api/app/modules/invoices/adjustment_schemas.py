from pydantic import BaseModel
import uuid
import datetime
from decimal import Decimal
from typing import List, Optional
from app.modules.invoices.models import NoteType, NoteStatus

class AdjustmentNoteLineSchema(BaseModel):
    description: str
    amount: Decimal

class AdjustmentNoteTaxLineSchema(BaseModel):
    tax_name: str
    tax_amount: Decimal

class AdjustmentNoteCreateRequest(BaseModel):
    customer_id: uuid.UUID
    invoice_id: uuid.UUID
    note_type: NoteType
    note_date: datetime.date
    reason: str
    lines: List[AdjustmentNoteLineSchema]
    tax_lines: List[AdjustmentNoteTaxLineSchema] = []

class AdjustmentNoteResponse(BaseModel):
    id: uuid.UUID
    organisation_id: uuid.UUID
    customer_id: uuid.UUID
    invoice_id: uuid.UUID
    note_type: NoteType
    note_number: str
    note_date: datetime.date
    reason: str
    subtotal: Decimal
    tax_amount: Decimal
    grand_total: Decimal
    currency: str
    status: NoteStatus
    pdf_url: Optional[str]
    created_at: datetime.datetime
