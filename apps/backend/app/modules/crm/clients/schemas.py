import uuid
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from decimal import Decimal

class ClientBase(BaseModel):
    name: str
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    billing_address: Optional[str] = None
    gstin: Optional[str] = None
    pan: Optional[str] = None
    payment_terms_days: Optional[int] = 30
    credit_limit: Optional[Decimal] = Decimal('0.0')
    status: Optional[str] = "ACTIVE"
    notes: Optional[str] = None

class ClientCreate(ClientBase):
    pass

class ClientUpdate(BaseModel):
    name: Optional[str] = None
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    billing_address: Optional[str] = None
    gstin: Optional[str] = None
    pan: Optional[str] = None
    payment_terms_days: Optional[int] = None
    credit_limit: Optional[Decimal] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class ClientResponse(ClientBase):
    id: uuid.UUID
    organisation_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class ClientLocationBase(BaseModel):
    name: str
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    status: Optional[str] = "ACTIVE"
    operating_unit_id: Optional[uuid.UUID] = None

class ClientLocationCreate(ClientLocationBase):
    pass

class ClientLocationUpdate(ClientLocationBase):
    name: Optional[str] = None

class ClientLocationResponse(ClientLocationBase):
    id: uuid.UUID
    client_id: uuid.UUID
    organisation_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class ClientOURelationshipRequest(BaseModel):
    operating_unit_id: uuid.UUID
    status: Optional[str] = "ACTIVE"

class ClientOURelationshipResponse(BaseModel):
    id: uuid.UUID
    client_id: uuid.UUID
    operating_unit_id: uuid.UUID
    status: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class ClientLocationTransferRequest(BaseModel):
    new_operating_unit_id: uuid.UUID
    reason: Optional[str] = None

class ClientLocationOUHistoryResponse(BaseModel):
    id: uuid.UUID
    client_location_id: uuid.UUID
    previous_operating_unit_id: Optional[uuid.UUID]
    new_operating_unit_id: Optional[uuid.UUID]
    actor_id: Optional[uuid.UUID]
    reason: Optional[str]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
