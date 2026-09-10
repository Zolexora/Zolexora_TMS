import uuid
import datetime
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, Field


class ExpenseCreateRequest(BaseModel):
    duty_id: Optional[uuid.UUID] = None
    trip_id: Optional[uuid.UUID] = None
    vehicle_id: Optional[uuid.UUID] = None
    driver_id: Optional[uuid.UUID] = None
    category: str
    amount: Decimal
    currency: str = "INR"
    expense_date: datetime.date = Field(default_factory=datetime.date.today)
    attachment_url: Optional[str] = None
    notes: Optional[str] = None


class ExpenseResponse(BaseModel):
    id: uuid.UUID
    organisation_id: uuid.UUID
    duty_id: Optional[uuid.UUID]
    trip_id: Optional[uuid.UUID]
    vehicle_id: Optional[uuid.UUID]
    driver_id: Optional[uuid.UUID]
    category: str
    amount: Decimal
    currency: str
    expense_date: datetime.datetime
    attachment_url: Optional[str]
    notes: Optional[str]
    created_at: datetime.datetime
    
    class Config:
        from_attributes = True
