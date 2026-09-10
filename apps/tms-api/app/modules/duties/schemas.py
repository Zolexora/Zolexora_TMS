import datetime
import uuid
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.modules.duties.models import DutyAssignmentStatus, DutyStatus


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
    actual_start_time: Optional[datetime.datetime] = None
    actual_end_time: Optional[datetime.datetime] = None
    status: DutyStatus
    dispatched_at: Optional[datetime.datetime] = None
    dispatched_by_user_id: Optional[uuid.UUID] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime
