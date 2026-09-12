from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional
import uuid
import datetime
from .models import ComplianceCategory, ComplianceEntityType, ComplianceStatus

class ComplianceIssue(BaseModel):
    code: str
    category: ComplianceCategory
    severity: str  # "BLOCK" or "WARNING"
    entity_type: ComplianceEntityType
    entity_id: uuid.UUID
    requirement_id: uuid.UUID
    message: str
    document_id: Optional[str] = None
    expires_at: Optional[datetime.date] = None

class ComplianceEvaluation(BaseModel):
    status: str  # "PASS", "WARNING", "BLOCK"
    evaluated_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))
    blocking_issues: List[ComplianceIssue] = Field(default_factory=list)
    warnings: List[ComplianceIssue] = Field(default_factory=list)
    valid_requirements: List[uuid.UUID] = Field(default_factory=list)
    missing_requirements: List[uuid.UUID] = Field(default_factory=list)
    expired_requirements: List[uuid.UUID] = Field(default_factory=list)
    verification_required: List[uuid.UUID] = Field(default_factory=list)
    rule_versions: List[uuid.UUID] = Field(default_factory=list)

class ComplianceRequirementBase(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    category: ComplianceCategory
    entity_type: ComplianceEntityType
    document_type: Optional[str] = None
    mandatory: bool = True
    blocking: bool = True
    verification_required: bool = False
    validity_period_days: Optional[int] = None
    active: bool = True
    source_reference: Optional[str] = None
    notes: Optional[str] = None
    conditions: Optional[dict] = None

class ComplianceRequirementCreate(ComplianceRequirementBase):
    pass

class ComplianceRequirementUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    mandatory: Optional[bool] = None
    blocking: Optional[bool] = None
    verification_required: Optional[bool] = None
    validity_period_days: Optional[int] = None
    active: Optional[bool] = None
    source_reference: Optional[str] = None
    notes: Optional[str] = None
    conditions: Optional[dict] = None

class ComplianceRequirementResponse(ComplianceRequirementBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organisation_id: Optional[uuid.UUID]
    created_at: datetime.datetime
    updated_at: datetime.datetime

class ComplianceRecordBase(BaseModel):
    requirement_id: uuid.UUID
    entity_type: ComplianceEntityType
    entity_id: uuid.UUID
    status: ComplianceStatus
    document_number: Optional[str] = None
    document_url: Optional[str] = None
    original_filename: Optional[str] = None
    mime_type: Optional[str] = None
    issued_date: Optional[datetime.date] = None
    expiry_date: Optional[datetime.date] = None
    metadata_: Optional[dict] = Field(None, alias="metadata")

class ComplianceRecordCreate(ComplianceRecordBase):
    pass

class ComplianceRecordUpdate(BaseModel):
    status: Optional[ComplianceStatus] = None
    document_number: Optional[str] = None
    document_url: Optional[str] = None
    original_filename: Optional[str] = None
    mime_type: Optional[str] = None
    issued_date: Optional[datetime.date] = None
    expiry_date: Optional[datetime.date] = None
    metadata_: Optional[dict] = Field(None, alias="metadata")

class ComplianceRecordResponse(ComplianceRecordBase):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    id: uuid.UUID
    organisation_id: uuid.UUID
    verified_at: Optional[datetime.datetime] = None
    verified_by: Optional[uuid.UUID] = None
    verification_method: Optional[str] = None
    rejection_reason: Optional[str] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

class ComplianceWaiveRequest(BaseModel):
    reason: str
    valid_until: datetime.date
