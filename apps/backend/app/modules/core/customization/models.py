import uuid
import enum
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.db.base import Base

class ApplicationType(str, enum.Enum):
    STANDARD = "STANDARD"
    CONFIGURED = "CONFIGURED"
    EXTENDED = "EXTENDED"
    CUSTOM = "CUSTOM"

class ApplicationStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    DEPRECATED = "DEPRECATED"
    ARCHIVED = "ARCHIVED"

class ConfigType(str, enum.Enum):
    NAVIGATION = "NAVIGATION"
    THEME = "THEME"
    TERMINOLOGY = "TERMINOLOGY"
    NUMBERING = "NUMBERING"
    NOTIFICATIONS = "NOTIFICATIONS"
    DOCUMENT_TEMPLATES = "DOCUMENT_TEMPLATES"
    EXTENSIONS = "EXTENSIONS"
    CUSTOM_REFS = "CUSTOM_REFS"

class OrganisationApplication(Base):
    __tablename__ = "organisation_applications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organisation_id = Column(UUID(as_uuid=True), ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True)
    application_type = Column(Enum(ApplicationType), nullable=False, default=ApplicationType.STANDARD)
    application_name = Column(String, nullable=False, default="Zolexora TMS")
    application_version = Column(String, nullable=False, default="1.0.0")
    status = Column(Enum(ApplicationStatus), nullable=False, default=ApplicationStatus.ACTIVE)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class ApplicationModule(Base):
    __tablename__ = "application_modules"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("organisation_applications.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    module_code = Column(String, nullable=False)
    is_enabled = Column(Boolean, nullable=False, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class ApplicationConfiguration(Base):
    __tablename__ = "application_configurations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("organisation_applications.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    config_type = Column(Enum(ConfigType), nullable=False)
    config_data = Column(JSONB, nullable=False, default={})
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class ApplicationWorkflow(Base):
    __tablename__ = "application_workflows"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("organisation_applications.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    entity_type = Column(String, nullable=False)
    workflow_name = Column(String, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    definition_json = Column(JSONB, nullable=False, default={})
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class ApplicationRule(Base):
    __tablename__ = "application_rules"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("organisation_applications.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    entity_type = Column(String, nullable=False)
    rule_name = Column(String, nullable=False)
    conditions_json = Column(JSONB, nullable=False, default={})
    actions_json = Column(JSONB, nullable=False, default={})
    priority = Column(Integer, nullable=False, default=100)
    is_active = Column(Boolean, nullable=False, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class ApplicationForm(Base):
    __tablename__ = "application_forms"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("organisation_applications.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    entity_type = Column(String, nullable=False)
    form_name = Column(String, nullable=False)
    fields_config_json = Column(JSONB, nullable=False, default={})
    sections_json = Column(JSONB, nullable=False, default={})
    is_active = Column(Boolean, nullable=False, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class ApplicationReport(Base):
    __tablename__ = "application_reports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("organisation_applications.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    report_name = Column(String, nullable=False)
    entity_source = Column(String, nullable=False)
    report_definition_json = Column(JSONB, nullable=False, default={})
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class ApplicationApproval(Base):
    __tablename__ = "application_approvals"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("organisation_applications.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    entity_type = Column(String, nullable=False)
    approval_chain_json = Column(JSONB, nullable=False, default={})
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
