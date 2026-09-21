"""
Prompt 07: Organization Role & Permission Models
================================================

Architecture:
- OrganisationRole        : org-scoped role (CUSTOM | ORG_TEMPLATE)
- OrganisationRoleVersion : immutable snapshot of permissions at a point in time
- OrganisationRolePermission: capability grant within a version (module.page.action)
- PlatformRoleTemplate    : Zolexora-defined global template (IMMUTABLE by orgs)
- PlatformRoleTemplatePermission: permissions on a platform template
- RoleAssignment          : links a member to a role version
- UserPermissionOverride  : per-member additions (+) or restrictions (-) on top of role

Commander is NOT a role. Commander authority is stored on OrganisationMember.is_commander.
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, DateTime, Enum, ForeignKey, Integer,
    String, Text, UniqueConstraint, Index,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class RoleStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class RoleSource(str, enum.Enum):
    """
    CUSTOM          - Created directly by the organisation from scratch.
    ORG_TEMPLATE    - An organisation-owned template (can spawn new roles).
    FROM_PLATFORM   - Copied from a Zolexora platform template.
    """
    CUSTOM = "CUSTOM"
    ORG_TEMPLATE = "ORG_TEMPLATE"
    FROM_PLATFORM = "FROM_PLATFORM"


class OverrideType(str, enum.Enum):
    GRANT = "GRANT"       # adds a permission the role doesn't have
    RESTRICT = "RESTRICT" # removes a permission the role grants


# ---------------------------------------------------------------------------
# Platform-level (Zolexora) Role Templates — IMMUTABLE by organizations
# ---------------------------------------------------------------------------

class PlatformRoleTemplate(Base, TimestampMixin):
    """
    Zolexora-defined role templates. Organizations can COPY these but never edit them.
    """
    __tablename__ = "platform_role_templates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    permissions: Mapped[list["PlatformRoleTemplatePermission"]] = relationship(
        "PlatformRoleTemplatePermission", back_populates="template", cascade="all, delete-orphan"
    )


class PlatformRoleTemplatePermission(Base):
    """Capability grants within a Zolexora platform role template."""
    __tablename__ = "platform_role_template_permissions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("platform_role_templates.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    # Capability reference: module_code.page_code.action_code
    module_code: Mapped[str] = mapped_column(String(100), nullable=False)
    page_code: Mapped[str] = mapped_column(String(100), nullable=False)
    action_code: Mapped[str] = mapped_column(String(100), nullable=False)

    template: Mapped["PlatformRoleTemplate"] = relationship(
        "PlatformRoleTemplate", back_populates="permissions"
    )

    __table_args__ = (
        UniqueConstraint(
            "template_id", "module_code", "page_code", "action_code",
            name="uq_platform_tpl_permission",
        ),
    )


# ---------------------------------------------------------------------------
# Organization Roles
# ---------------------------------------------------------------------------

class OrganisationRole(Base, TimestampMixin):
    """
    An organization-scoped role. Commander is NOT a role.
    Each version snapshot lives in OrganisationRoleVersion.
    """
    __tablename__ = "organisation_roles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organisation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organisations.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[RoleSource] = mapped_column(
        Enum(RoleSource, name="role_source"), nullable=False, default=RoleSource.CUSTOM
    )
    status: Mapped[RoleStatus] = mapped_column(
        Enum(RoleStatus, name="role_status"), nullable=False, default=RoleStatus.ACTIVE
    )
    # If copied from a platform template, records which one
    platform_template_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("platform_role_templates.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    # Current active version number (denormalized for quick lookup)
    current_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    versions: Mapped[list["OrganisationRoleVersion"]] = relationship(
        "OrganisationRoleVersion", back_populates="role",
        cascade="all, delete-orphan", order_by="OrganisationRoleVersion.version_number"
    )
    assignments: Mapped[list["RoleAssignment"]] = relationship(
        "RoleAssignment", back_populates="role"
    )

    __table_args__ = (
        # Role names must be unique within an organization
        UniqueConstraint("organisation_id", "name", name="uq_org_role_name"),
        Index("ix_org_roles_org_status", "organisation_id", "status"),
    )


class OrganisationRoleVersion(Base):
    """
    Immutable snapshot of a role's permissions at a point in time.
    Each permission change creates a new version. Old versions are preserved for audit.
    """
    __tablename__ = "organisation_role_versions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organisation_roles.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    change_note: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    role: Mapped["OrganisationRole"] = relationship(
        "OrganisationRole", back_populates="versions"
    )
    permissions: Mapped[list["OrganisationRolePermission"]] = relationship(
        "OrganisationRolePermission", back_populates="version",
        cascade="all, delete-orphan"
    )
    # Assignments using this exact version
    assignments: Mapped[list["RoleAssignment"]] = relationship(
        "RoleAssignment", back_populates="role_version"
    )

    __table_args__ = (
        UniqueConstraint("role_id", "version_number", name="uq_role_version"),
    )


class OrganisationRolePermission(Base):
    """Capability grants within a role version (module.page.action)."""
    __tablename__ = "organisation_role_permissions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organisation_role_versions.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    module_code: Mapped[str] = mapped_column(String(100), nullable=False)
    page_code: Mapped[str] = mapped_column(String(100), nullable=False)
    action_code: Mapped[str] = mapped_column(String(100), nullable=False)

    version: Mapped["OrganisationRoleVersion"] = relationship(
        "OrganisationRoleVersion", back_populates="permissions"
    )

    __table_args__ = (
        UniqueConstraint(
            "version_id", "module_code", "page_code", "action_code",
            name="uq_role_version_permission",
        ),
        Index("ix_role_perm_version", "version_id"),
    )


# ---------------------------------------------------------------------------
# Role Assignments — links a member to a specific role version
# ---------------------------------------------------------------------------

class RoleAssignment(Base, TimestampMixin):
    """
    Assigns an OrganisationMember to a Role (at a specific version).
    
    Design: One active assignment per member per org (single-role model for Phase 7).
    The version_id records which version the user was pinned to at assignment time.
    When a new role version is published, the Commander can choose to advance assignments.
    """
    __tablename__ = "role_assignments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organisation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organisations.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organisation_members.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organisation_roles.id", ondelete="RESTRICT"),
        nullable=False,
    )
    # Tracks the version the user is currently pinned to
    role_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organisation_role_versions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    assigned_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    role: Mapped["OrganisationRole"] = relationship("OrganisationRole", back_populates="assignments")
    role_version: Mapped["OrganisationRoleVersion"] = relationship(
        "OrganisationRoleVersion", back_populates="assignments"
    )

    __table_args__ = (
        # Only one active assignment per member per org
        UniqueConstraint("organisation_id", "member_id", name="uq_active_role_assignment"),
        Index("ix_role_assignment_member", "member_id"),
    )


# ---------------------------------------------------------------------------
# User Permission Overrides
# ---------------------------------------------------------------------------

class UserPermissionOverride(Base, TimestampMixin):
    """
    Per-member permission additions (GRANT) or restrictions (RESTRICT)
    that layer on top of the role's effective permissions.
    
    Effective Permissions = Role Permissions + GRANTs - RESTRICTs
    """
    __tablename__ = "user_permission_overrides"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organisation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organisations.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organisation_members.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    override_type: Mapped[OverrideType] = mapped_column(
        Enum(OverrideType, name="override_type"), nullable=False
    )
    module_code: Mapped[str] = mapped_column(String(100), nullable=False)
    page_code: Mapped[str] = mapped_column(String(100), nullable=False)
    action_code: Mapped[str] = mapped_column(String(100), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(512), nullable=True)
    granted_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    __table_args__ = (
        UniqueConstraint(
            "organisation_id", "member_id", "override_type", "module_code", "page_code", "action_code",
            name="uq_user_perm_override",
        ),
        Index("ix_user_override_member", "member_id"),
    )
