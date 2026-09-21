"""
Prompt 07: Role & Permission schemas (request/response)
"""

import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


# ---------------------------------------------------------------------------
# Capability (from registry) — used in permission matrix
# ---------------------------------------------------------------------------

class ActionSchema(BaseModel):
    code: str
    name: str

class PageSchema(BaseModel):
    code: str
    name: str
    actions: list[ActionSchema]

class ModuleSchema(BaseModel):
    code: str
    name: str
    pages: list[PageSchema]

class CapabilityRegistryResponse(BaseModel):
    code: str
    name: str
    modules: list[ModuleSchema]


# ---------------------------------------------------------------------------
# Platform Templates
# ---------------------------------------------------------------------------

class PlatformTemplatePermissionSchema(BaseModel):
    module_code: str
    page_code: str
    action_code: str

class PlatformTemplateResponse(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    description: Optional[str] = None
    version: int
    permissions: list[PlatformTemplatePermissionSchema]
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Role Permissions (within a version)
# ---------------------------------------------------------------------------

class RolePermissionInput(BaseModel):
    module_code: str = Field(..., min_length=1, max_length=100)
    page_code: str = Field(..., min_length=1, max_length=100)
    action_code: str = Field(..., min_length=1, max_length=100)

class RolePermissionResponse(RolePermissionInput):
    id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Role Version
# ---------------------------------------------------------------------------

class RoleVersionResponse(BaseModel):
    id: uuid.UUID
    role_id: uuid.UUID
    version_number: int
    change_note: Optional[str] = None
    created_by_user_id: Optional[uuid.UUID] = None
    created_at: datetime
    permissions: list[RolePermissionResponse]
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Organisation Roles
# ---------------------------------------------------------------------------

class RoleCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    permissions: list[RolePermissionInput] = Field(default_factory=list)
    # Optional: start from a platform template
    platform_template_id: Optional[uuid.UUID] = None
    change_note: Optional[str] = Field(None, max_length=512)


class RoleUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    permissions: Optional[list[RolePermissionInput]] = None
    change_note: Optional[str] = Field(None, max_length=512)


class RoleResponse(BaseModel):
    id: uuid.UUID
    organisation_id: uuid.UUID
    name: str
    description: Optional[str] = None
    source: str
    status: str
    current_version: int
    platform_template_id: Optional[uuid.UUID] = None
    created_by_user_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime
    # Embedded current version permissions
    current_permissions: list[RolePermissionResponse] = Field(default_factory=list)
    # User count (computed)
    member_count: int = 0
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Role Assignment
# ---------------------------------------------------------------------------

class AssignRoleRequest(BaseModel):
    role_id: Optional[uuid.UUID] = None  # null = unassign


class RoleAssignmentResponse(BaseModel):
    id: uuid.UUID
    organisation_id: uuid.UUID
    member_id: uuid.UUID
    role_id: uuid.UUID
    role_version_id: uuid.UUID
    is_active: bool
    assigned_by_user_id: Optional[uuid.UUID] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# User Permission Overrides
# ---------------------------------------------------------------------------

class OverrideCreateRequest(BaseModel):
    override_type: str = Field(..., pattern="^(GRANT|RESTRICT)$")
    module_code: str = Field(..., min_length=1, max_length=100)
    page_code: str = Field(..., min_length=1, max_length=100)
    action_code: str = Field(..., min_length=1, max_length=100)
    reason: Optional[str] = Field(None, max_length=512)


class OverrideResponse(BaseModel):
    id: uuid.UUID
    member_id: uuid.UUID
    override_type: str
    module_code: str
    page_code: str
    action_code: str
    reason: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Effective Permissions (consumed by frontend runtime)
# ---------------------------------------------------------------------------

class EffectivePermission(BaseModel):
    """A flat list of granted module.page.action capability codes."""
    capability: str  # format: "module_code.page_code.action_code"


class EffectivePermissionsResponse(BaseModel):
    user_id: uuid.UUID
    organisation_id: uuid.UUID
    is_commander: bool
    role_id: Optional[uuid.UUID] = None
    role_name: Optional[str] = None
    role_version: Optional[int] = None
    # Flat set of granted capability strings
    permissions: list[str]
    # Structured for UI consumption
    modules: dict[str, dict[str, list[str]]] = Field(
        default_factory=dict,
        description="{ module_code: { page_code: [action_codes] } }"
    )


# ---------------------------------------------------------------------------
# Member with role info (for member management UI)
# ---------------------------------------------------------------------------

class MemberWithRoleResponse(BaseModel):
    member_id: uuid.UUID
    user_id: uuid.UUID
    organisation_id: uuid.UUID
    status: str
    is_commander: bool
    is_creator: bool
    role_id: Optional[uuid.UUID] = None
    role_name: Optional[str] = None
    role_status: Optional[str] = None
    created_at: datetime
