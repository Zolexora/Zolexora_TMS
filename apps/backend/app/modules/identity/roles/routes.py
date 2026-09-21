"""
Prompt 07: Role & Permission API routes
"""

import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import (
    AuthenticatedUser,
    get_current_user,
    get_current_active_organisation,
)
from app.db.session import get_db
from app.modules.core.platform.capabilities import TMS_CAPABILITY_REGISTRY
from app.modules.identity.roles.schemas import (
    AssignRoleRequest,
    CapabilityRegistryResponse,
    EffectivePermissionsResponse,
    MemberWithRoleResponse,
    OverrideCreateRequest,
    OverrideResponse,
    PlatformTemplateResponse,
    RoleAssignmentResponse,
    RoleCreateRequest,
    RoleResponse,
    RoleUpdateRequest,
)
from app.modules.identity.roles.service import (
    add_permission_override,
    archive_role,
    assign_role_to_member,
    create_role,
    get_platform_template,
    get_role,
    list_members_with_roles,
    list_platform_templates,
    list_roles,
    remove_permission_override,
    resolve_effective_permissions,
    update_role,
)

router = APIRouter(prefix="/api/v1", tags=["Roles & Permissions"])


# ---------------------------------------------------------------------------
# Capability Registry (public within auth'd org context)
# ---------------------------------------------------------------------------

@router.get("/capabilities", response_model=CapabilityRegistryResponse)
async def get_capability_registry(
    _: AuthenticatedUser = Depends(get_current_active_organisation),
):
    """Returns the canonical TMS capability registry (module→page→action)."""
    return TMS_CAPABILITY_REGISTRY


# ---------------------------------------------------------------------------
# Platform Role Templates (read-only for organizations)
# ---------------------------------------------------------------------------

@router.get("/platform-role-templates", response_model=list[PlatformTemplateResponse])
async def list_platform_role_templates(
    _: AuthenticatedUser = Depends(get_current_active_organisation),
    db: AsyncSession = Depends(get_db),
):
    """Lists all active Zolexora platform role templates. Organizations cannot modify these."""
    templates = await list_platform_templates(db)
    return [
        PlatformTemplateResponse(
            id=t.id,
            code=t.code,
            name=t.name,
            description=t.description,
            version=t.version,
            permissions=[
                {"module_code": p.module_code, "page_code": p.page_code, "action_code": p.action_code}
                for p in t.permissions
            ],
        )
        for t in templates
    ]


# ---------------------------------------------------------------------------
# Organisation Roles
# ---------------------------------------------------------------------------

@router.get("/organisations/roles", response_model=list[RoleResponse])
async def list_organisation_roles(
    user: AuthenticatedUser = Depends(get_current_active_organisation),
    db: AsyncSession = Depends(get_db),
):
    return await list_roles(user.organisation_id, db)


@router.post("/organisations/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_organisation_role(
    req: RoleCreateRequest,
    user: AuthenticatedUser = Depends(get_current_active_organisation),
    db: AsyncSession = Depends(get_db),
):
    _require_role_management(user)
    return await create_role(user.organisation_id, user.id, req, db)


@router.get("/organisations/roles/{role_id}", response_model=RoleResponse)
async def get_organisation_role(
    role_id: uuid.UUID,
    user: AuthenticatedUser = Depends(get_current_active_organisation),
    db: AsyncSession = Depends(get_db),
):
    role = await get_role(role_id, user.organisation_id, db)
    # Build response
    current_v = next((v for v in role.versions if v.version_number == role.current_version), None)
    from app.modules.identity.roles.schemas import RolePermissionResponse
    return RoleResponse(
        id=role.id,
        organisation_id=role.organisation_id,
        name=role.name,
        description=role.description,
        source=role.source.value,
        status=role.status.value,
        current_version=role.current_version,
        platform_template_id=role.platform_template_id,
        created_by_user_id=role.created_by_user_id,
        created_at=role.created_at,
        updated_at=role.updated_at,
        current_permissions=[
            RolePermissionResponse(id=p.id, module_code=p.module_code, page_code=p.page_code, action_code=p.action_code)
            for p in (current_v.permissions if current_v else [])
        ],
    )


@router.patch("/organisations/roles/{role_id}", response_model=RoleResponse)
async def update_organisation_role(
    role_id: uuid.UUID,
    req: RoleUpdateRequest,
    user: AuthenticatedUser = Depends(get_current_active_organisation),
    db: AsyncSession = Depends(get_db),
):
    _require_role_management(user)
    return await update_role(role_id, user.organisation_id, user.id, req, db)


@router.post("/organisations/roles/{role_id}/archive", status_code=status.HTTP_200_OK)
async def archive_organisation_role(
    role_id: uuid.UUID,
    user: AuthenticatedUser = Depends(get_current_active_organisation),
    db: AsyncSession = Depends(get_db),
):
    _require_role_management(user)
    await archive_role(role_id, user.organisation_id, user.id, db)
    return {"message": "Role archived successfully."}


# ---------------------------------------------------------------------------
# Member Role Assignment
# ---------------------------------------------------------------------------

@router.get("/organisations/members-with-roles", response_model=list[MemberWithRoleResponse])
async def list_members_roles(
    user: AuthenticatedUser = Depends(get_current_active_organisation),
    db: AsyncSession = Depends(get_db),
):
    return await list_members_with_roles(user.organisation_id, db)


@router.put("/organisations/members/{member_id}/role")
async def assign_member_role(
    member_id: uuid.UUID,
    req: AssignRoleRequest,
    user: AuthenticatedUser = Depends(get_current_active_organisation),
    db: AsyncSession = Depends(get_db),
):
    _require_role_management(user)
    result = await assign_role_to_member(user.organisation_id, member_id, user.id, req, db)
    if result is None:
        return {"message": "Role unassigned successfully."}
    return {"message": "Role assigned successfully.", "assignment_id": str(result.id)}


# ---------------------------------------------------------------------------
# Permission Overrides
# ---------------------------------------------------------------------------

@router.post("/organisations/members/{member_id}/permission-overrides", status_code=status.HTTP_201_CREATED)
async def add_member_override(
    member_id: uuid.UUID,
    req: OverrideCreateRequest,
    user: AuthenticatedUser = Depends(get_current_active_organisation),
    db: AsyncSession = Depends(get_db),
):
    _require_role_management(user)
    override = await add_permission_override(user.organisation_id, member_id, user.id, req, db)
    return OverrideResponse(
        id=override.id,
        member_id=override.member_id,
        override_type=override.override_type.value,
        module_code=override.module_code,
        page_code=override.page_code,
        action_code=override.action_code,
        reason=override.reason,
    )


@router.delete("/organisations/permission-overrides/{override_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member_override(
    override_id: uuid.UUID,
    user: AuthenticatedUser = Depends(get_current_active_organisation),
    db: AsyncSession = Depends(get_db),
):
    _require_role_management(user)
    await remove_permission_override(override_id, user.organisation_id, user.id, db)


# ---------------------------------------------------------------------------
# Effective Permissions endpoint (consumed by frontend runtime)
# ---------------------------------------------------------------------------

@router.get("/organisations/me/effective-permissions", response_model=EffectivePermissionsResponse)
async def get_effective_permissions(
    user: AuthenticatedUser = Depends(get_current_active_organisation),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns the complete effective permission set for the current user.
    Commander gets all capabilities. Others get role + overrides applied.
    Frontend runtime should consume this to drive navigation and action availability.
    """
    return await resolve_effective_permissions(user.organisation_id, user.id, db)


# ---------------------------------------------------------------------------
# Authorization guard helper
# ---------------------------------------------------------------------------

def _require_role_management(user: AuthenticatedUser) -> None:
    """Commander can always manage roles. Others need 'users.manage' permission (future)."""
    from fastapi import HTTPException
    if not user.is_commander and not user.has_permission("users.manage"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the Commander or users with 'users.manage' permission can manage roles.",
        )
