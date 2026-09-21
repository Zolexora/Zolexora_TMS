import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Integer, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.base import Base
import enum

class ProviderType(str, enum.Enum):
    D1 = "D1"
    POSTGRESQL = "POSTGRESQL"
    MONGODB = "MONGODB"
    OTHER = "OTHER"

class RegistryStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    PROVISIONING = "PROVISIONING"
    ASSIGNED = "ASSIGNED"
    MIGRATING = "MIGRATING"
    SUSPENDED = "SUSPENDED"
    DECOMMISSIONED = "DECOMMISSIONED"
    PROVISIONING_FAILED = "PROVISIONING_FAILED"


class MigrationStatus(str, enum.Enum):
    NOT_STARTED = "NOT_STARTED"
    VALIDATING_SOURCE = "VALIDATING_SOURCE"
    PROVISIONING_DESTINATION = "PROVISIONING_DESTINATION"
    SCHEMA_PREPARATION = "SCHEMA_PREPARATION"
    DATA_EXPORT = "DATA_EXPORT"
    DATA_TRANSFORMATION = "DATA_TRANSFORMATION"
    DATA_IMPORT = "DATA_IMPORT"
    RECONCILIATION = "RECONCILIATION"
    RUNTIME_VALIDATION = "RUNTIME_VALIDATION"
    PILOT_READY = "PILOT_READY"
    MIGRATION_FAILED = "MIGRATION_FAILED"
    MIGRATION_CANCELLED = "MIGRATION_CANCELLED"

class TenantDatabaseRegistry(Base):
    __tablename__ = "tenant_database_registry"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider = Column(Enum(ProviderType), nullable=False)
    database_identifier = Column(String, nullable=False, unique=True)
    database_name = Column(String, nullable=False)
    region = Column(String, nullable=True)
    status = Column(Enum(RegistryStatus), nullable=False, default=RegistryStatus.AVAILABLE)
    schema_version = Column(Integer, nullable=False, default=0)
    capacity_status = Column(String, nullable=True)
    assigned_organisation_id = Column(UUID(as_uuid=True), ForeignKey("organisations.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class OrganisationDatabaseAssignment(Base):
    __tablename__ = "organisation_database_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organisation_id = Column(UUID(as_uuid=True), ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, unique=True)
    database_registry_id = Column(UUID(as_uuid=True), ForeignKey("tenant_database_registry.id", ondelete="CASCADE"), nullable=False)
    assignment_status = Column(String, nullable=False, default="ACTIVE")
    provisioning_status = Column(String, nullable=False, default="READY")
    schema_version = Column(Integer, nullable=False, default=0)
    last_migration_at = Column(DateTime(timezone=True), nullable=True)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class TenantMongodbRegistry(Base):
    __tablename__ = "tenant_mongodb_registry"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider = Column(Enum(ProviderType), nullable=False, default=ProviderType.MONGODB)
    cluster_identifier = Column(String, nullable=False)
    database_name = Column(String, nullable=False)
    status = Column(Enum(RegistryStatus), nullable=False, default=RegistryStatus.AVAILABLE)
    schema_version = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class OrganisationMongodbAssignment(Base):
    __tablename__ = "organisation_mongodb_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organisation_id = Column(UUID(as_uuid=True), ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, unique=True)
    mongodb_registry_id = Column(UUID(as_uuid=True), ForeignKey("tenant_mongodb_registry.id", ondelete="CASCADE"), nullable=False)
    database_name = Column(String, nullable=False)
    namespace_prefix = Column(String, nullable=False)
    status = Column(String, nullable=False, default="ACTIVE")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class OrganisationStorageAssignment(Base):
    __tablename__ = "organisation_storage_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organisation_id = Column(UUID(as_uuid=True), ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, unique=True)
    cloudinary_folder_prefix = Column(String, nullable=False)
    r2_bucket = Column(String, nullable=False)
    r2_prefix = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class PlatformAuditLog(Base):
    __tablename__ = "platform_audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organisation_id = Column(UUID(as_uuid=True), ForeignKey("organisations.id", ondelete="SET NULL"), nullable=True)
    user_id = Column(UUID(as_uuid=True), nullable=True)
    event_type = Column(String, nullable=False)
    entity_type = Column(String, nullable=True)
    entity_id = Column(String, nullable=True)
    payload = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())



from sqlalchemy.dialects.postgresql import JSONB

class TenantMigrationJob(Base):
    __tablename__ = "tenant_migration_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organisation_id = Column(UUID(as_uuid=True), ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False)
    source_provider = Column(Enum(ProviderType), nullable=False)
    destination_provider = Column(Enum(ProviderType), nullable=False)
    destination_database_identifier = Column(String, nullable=True)
    status = Column(Enum(MigrationStatus), nullable=False, default=MigrationStatus.NOT_STARTED)
    
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    error_summary = Column(Text, nullable=True)
    schema_version = Column(Integer, nullable=True)
    
    # store detailed results as JSON or JSONB
    row_counts = Column(JSONB, nullable=True)
    reconciliation_result = Column(JSONB, nullable=True)
    runtime_validation_result = Column(JSONB, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
