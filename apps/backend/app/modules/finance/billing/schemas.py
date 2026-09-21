from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Any
import uuid
import datetime
from decimal import Decimal
from .models import RateRuleType

class RateCardRuleBase(BaseModel):
    rule_type: RateRuleType
    name: str
    base_amount: Decimal = Decimal("0.0")
    quantity_included: Decimal = Decimal("0.0")
    rate_per_unit: Decimal = Decimal("0.0")
    is_percentage: bool = False
    percentage_value: Decimal = Decimal("0.0")
    sequence: int = 10
    conditions: dict = Field(default_factory=dict)

class RateCardRuleCreate(RateCardRuleBase):
    pass

class RateCardRuleResponse(RateCardRuleBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID

class RateCardVersionBase(BaseModel):
    version_number: int
    is_immutable: bool = True
    effective_from: datetime.datetime
    effective_to: Optional[datetime.datetime] = None

class RateCardVersionCreate(RateCardVersionBase):
    rules: List[RateCardRuleCreate]

class RateCardVersionResponse(RateCardVersionBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    rules: List[RateCardRuleResponse]

class RateCardBase(BaseModel):
    name: str
    customer_id: Optional[uuid.UUID] = None
    booking_type: str = "ADHOC"
    vehicle_type: str = "SEDAN"
    is_active: bool = True
    active: bool = True # keep for compat

class RateCardCreate(RateCardBase):
    initial_version: Optional[RateCardVersionCreate] = None

class RateCardResponse(RateCardBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organisation_id: uuid.UUID
    versions: List[RateCardVersionResponse] = []
    created_at: datetime.datetime
    updated_at: datetime.datetime
