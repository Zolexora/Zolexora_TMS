import datetime
import uuid
import enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class DutyStatus(str, enum.Enum):
    UNASSIGNED = "UNASSIGNED"
    ASSIGNED = "ASSIGNED"
    DRIVER_ACCEPTANCE_PENDING = "DRIVER_ACCEPTANCE_PENDING"
    ACCEPTED = "ACCEPTED"
    DISPATCHED = "DISPATCHED"
    ARRIVED_PICKUP = "ARRIVED_PICKUP"
    IN_TRANSIT = "IN_TRANSIT"
    ARRIVED_DROP = "ARRIVED_DROP"
    DUTY_COMPLETED = "DUTY_COMPLETED"
    CANCELLED = "CANCELLED"

class DutyAssignmentStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"

class DutyBase(BaseModel):
    booking_id: uuid.UUID
    scheduled_start_time: datetime.datetime
    scheduled_end_time: datetime.datetime
    notes: Optional[str] = None

class DutyCreate(DutyBase):
    driver_id: Optional[uuid.UUID] = None
    vehicle_id: Optional[uuid.UUID] = None

class DutyAssignRequest(BaseModel):
    driver_id: uuid.UUID
    vehicle_id: uuid.UUID

class DutyReassignRequest(BaseModel):
    driver_id: Optional[uuid.UUID] = None
    vehicle_id: Optional[uuid.UUID] = None
    reason: str = Field(..., min_length=3)

class DriverActionRequest(BaseModel):
    reason: Optional[str] = None

class DutyAssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    duty_id: uuid.UUID
    driver_id: uuid.UUID
    vehicle_id: uuid.UUID
    assigned_by_user_id: uuid.UUID
    status: DutyAssignmentStatus
    assigned_at: datetime.datetime
    accepted_at: Optional[datetime.datetime] = None
    rejected_at: Optional[datetime.datetime] = None
    rejection_reason: Optional[str] = None

class DutyResponse(DutyBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    duty_number: str
    organisation_id: uuid.UUID
    driver_id: Optional[uuid.UUID] = None
    vehicle_id: Optional[uuid.UUID] = None
    start_time: Optional[datetime.datetime] = None
    end_time: Optional[datetime.datetime] = None
    start_km: Optional[float] = None
    end_km: Optional[float] = None
    status: DutyStatus
    created_at: datetime.datetime
    updated_at: datetime.datetime

