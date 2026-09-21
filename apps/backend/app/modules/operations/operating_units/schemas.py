import uuid
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class OperatingUnitBase(BaseModel):
    code: str
    name: str
    status: Optional[str] = "ACTIVE"

class OperatingUnitCreate(OperatingUnitBase):
    pass

class OperatingUnitUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    status: Optional[str] = None

class OperatingUnitResponse(OperatingUnitBase):
    id: uuid.UUID
    organisation_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class OperatingUnitLocationBase(BaseModel):
    code: str
    name: str
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    latitude: Optional[str] = None
    longitude: Optional[str] = None
    status: Optional[str] = "ACTIVE"

class OperatingUnitLocationCreate(OperatingUnitLocationBase):
    pass

class OperatingUnitLocationUpdate(OperatingUnitLocationBase):
    code: Optional[str] = None
    name: Optional[str] = None

class OperatingUnitLocationResponse(OperatingUnitLocationBase):
    id: uuid.UUID
    operating_unit_id: uuid.UUID
    organisation_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
