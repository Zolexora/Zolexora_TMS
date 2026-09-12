import enum
import uuid
import datetime
from sqlalchemy import Date, Enum, ForeignKey, String, Boolean, UniqueConstraint, Integer
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin

class ComplianceCategory(str, enum.Enum):
    STATUTORY = "STATUTORY"
    CONTRACTUAL = "CONTRACTUAL"
    INTERNAL = "INTERNAL"
    SAFETY = "SAFETY"

class ComplianceEntityType(str, enum.Enum):
    ORGANISATION = "ORGANISATION"
    VEHICLE = "VEHICLE"
    DRIVER = "DRIVER"
    VENDOR = "VENDOR"
    CUSTOMER = "CUSTOMER"
    SERVICE = "SERVICE"
    ROUTE = "ROUTE"
    DUTY = "DUTY"

class ComplianceStatus(str, enum.Enum):
    MISSING = "MISSING"
    PENDING = "PENDING"
    VERIFICATION_REQUIRED = "VERIFICATION_REQUIRED"
    VALID = "VALID"
    EXPIRING_SOON = "EXPIRING_SOON"
    EXPIRED = "EXPIRED"
    REJECTED = "REJECTED"
    WAIVED = "WAIVED"

class ComplianceVerificationAction(str, enum.Enum):
    VERIFY = "VERIFY"
    REJECT = "REJECT"
    WAIVE = "WAIVE"

class ComplianceRequirement(Base, TimestampMixin):
    __tablename__ = "compliance_requirements"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organisation_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("organisations.id", ondelete="CASCADE"), nullable=True, index=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(String(512), nullable=True)
    category: Mapped[ComplianceCategory] = mapped_column(Enum(ComplianceCategory, name="compliance_category"), nullable=False)
    entity_type: Mapped[ComplianceEntityType] = mapped_column(Enum(ComplianceEntityType, name="compliance_entity_type"), nullable=False)
    document_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    mandatory: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    blocking: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    verification_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    validity_period_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    source_reference: Mapped[str | None] = mapped_column(String(256), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(512), nullable=True)
    # Configurable conditions (e.g. {"state": "UP", "service_type": "ETS", "ownership_type": "ATTACHED"})
    conditions: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        UniqueConstraint("organisation_id", "code", name="uq_comp_req_org_code"),
    )

class ComplianceRecord(Base, TimestampMixin):
    __tablename__ = "compliance_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organisation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True)
    requirement_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("compliance_requirements.id", ondelete="RESTRICT"), nullable=False, index=True)
    entity_type: Mapped[ComplianceEntityType] = mapped_column(Enum(ComplianceEntityType, name="compliance_entity_type", create_type=False), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    
    status: Mapped[ComplianceStatus] = mapped_column(Enum(ComplianceStatus, name="compliance_status"), default=ComplianceStatus.MISSING, nullable=False, index=True)
    document_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    document_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    original_filename: Mapped[str | None] = mapped_column(String(256), nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    
    issued_date: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[datetime.date | None] = mapped_column(Date, nullable=True, index=True)
    
    verified_at: Mapped[datetime.datetime | None] = mapped_column(nullable=True)
    verified_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="SET NULL"), nullable=True)
    verification_method: Mapped[str | None] = mapped_column(String(128), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(String(512), nullable=True)
    
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    requirement = relationship("ComplianceRequirement", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("organisation_id", "requirement_id", "entity_type", "entity_id", name="uq_comp_record_entity_req"),
    )

class ComplianceVerification(Base, TimestampMixin):
    __tablename__ = "compliance_verifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organisation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True)
    compliance_record_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("compliance_records.id", ondelete="CASCADE"), nullable=False, index=True)
    action: Mapped[ComplianceVerificationAction] = mapped_column(Enum(ComplianceVerificationAction, name="compliance_verification_action"), nullable=False)
    previous_status: Mapped[ComplianceStatus] = mapped_column(Enum(ComplianceStatus, name="compliance_status", create_type=False), nullable=False)
    new_status: Mapped[ComplianceStatus] = mapped_column(Enum(ComplianceStatus, name="compliance_status", create_type=False), nullable=False)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="SET NULL"), nullable=True)
    comments: Mapped[str | None] = mapped_column(String(512), nullable=True)
