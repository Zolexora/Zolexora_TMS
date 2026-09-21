"""
Prompt 07: Role & Permission service layer
==========================================

Handles:
- Role CRUD (org-scoped, versioned)
- Platform template read (immutable)
- Role assignment
- User permission overrides
- Effective permission resolution (the authoritative resolver)
"""

import uuid
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.core.platform.capabilities import TMS_CAPABILITY_REGISTRY
from app.modules.core.audit.models import AuditLog
from app.modules.identity.roles.models import (
    OrganisationRole,
    OrganisationRoleVersion,
    OrganisationRolePermission,
    PlatformRoleTemplate,
    PlatformRoleTemplatePermission,
    RoleAssignment,
    UserPermissionOverride,
    RoleStatus,
    RoleSource,
    OverrideType,
)
from app.modules.identity.organisations.membership_models import OrganisationMember
from app.modules.identity.roles.schemas import (
    RoleCreateRequest,
    RoleUpdateRequest,
    AssignRoleRequest,
    OverrideCreateRequest,
    EffectivePermissionsResponse,
    RolePermissionResponse,
    RoleResponse,
    MemberWithRoleResponse,
)


# ---------------------------------------------------------------------------
# Capability registry helpers
# ---------------------------------------------------------------------------

def _build_capability_set() -> set[str]:
    """Returns all valid capability strings as 'module.page.action'."""
    caps = set()
    for mod in TMS_CAPABILITY_REGISTRY.modules:
        for page in mod.pages:
            for action in page.actions:
                caps.add(f"{mod.code}.{page.code}.{action.code}")
    return caps


VALID_CAPABILITIES: set[str] = _build_capability_set()


def _validate_capabilities(perms: list) -> None:
    """Raise 400 if any permission references an unknown capability."""
    for p in perms:
        cap = f"{p.module_code}.{p.page_code}.{p.action_code}"
        if cap not in VALID_CAPABILITIES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown capability: '{cap}'. Check the capability registry.",
            )


# ---------------------------------------------------------------------------
# Platform Templates (read-only for organizations)
# ---------------------------------------------------------------------------

async def list_platform_templates(db: AsyncSession) -> list[PlatformRoleTemplate]:
    stmt = (
        select(PlatformRoleTemplate)
        .where(PlatformRoleTemplate.is_active == True)
        .options(selectinload(PlatformRoleTemplate.permissions))
        .order_by(PlatformRoleTemplate.name)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_platform_template(template_id: uuid.UUID, db: AsyncSession) -> PlatformRoleTemplate:
    stmt = (
        select(PlatformRoleTemplate)
        .where(PlatformRoleTemplate.id == template_id)
        .options(selectinload(PlatformRoleTemplate.permissions))
    )
    result = await db.execute(stmt)
    tpl = result.scalar_one_or_none()
    if not tpl:
        raise HTTPException(status_code=404, detail="Platform template not found.")
    return tpl


# ---------------------------------------------------------------------------
# Organisation Roles
# ---------------------------------------------------------------------------

async def list_roles(org_id: uuid.UUID, db: AsyncSession) -> list[RoleResponse]:
    stmt = (
        select(OrganisationRole)
        .where(OrganisationRole.organisation_id == org_id)
        .options(
            selectinload(OrganisationRole.versions).selectinload(
                OrganisationRoleVersion.permissions
            )
        )
        .order_by(OrganisationRole.created_at)
    )
    result = await db.execute(stmt)
    roles = result.scalars().all()

    # Get member counts per role
    count_stmt = (
        select(RoleAssignment.role_id, func.count(RoleAssignment.id))
        .where(RoleAssignment.organisation_id == org_id, RoleAssignment.is_active == True)
        .group_by(RoleAssignment.role_id)
    )
    count_result = await db.execute(count_stmt)
    member_counts = dict(count_result.all())

    out = []
    for role in roles:
        # Find current version
        current_v = next(
            (v for v in role.versions if v.version_number == role.current_version), None
        )
        out.append(RoleResponse(
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
            member_count=member_counts.get(role.id, 0),
        ))
    return out


async def get_role(role_id: uuid.UUID, org_id: uuid.UUID, db: AsyncSession) -> OrganisationRole:
    stmt = (
        select(OrganisationRole)
        .where(OrganisationRole.id == role_id, OrganisationRole.organisation_id == org_id)
        .options(
            selectinload(OrganisationRole.versions).selectinload(OrganisationRoleVersion.permissions)
        )
    )
    result = await db.execute(stmt)
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found in this organisation.")
    return role


async def create_role(
    org_id: uuid.UUID,
    actor_id: uuid.UUID,
    req: RoleCreateRequest,
    db: AsyncSession,
) -> OrganisationRole:
    # Validate capabilities
    _validate_capabilities(req.permissions)

    # Check duplicate name within org
    dup_stmt = select(OrganisationRole).where(
        OrganisationRole.organisation_id == org_id,
        OrganisationRole.name == req.name,
    )
    dup = await db.execute(dup_stmt)
    if dup.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"A role named '{req.name}' already exists in this organisation.")

    # Determine source
    source = RoleSource.CUSTOM
    platform_template_id = None
    base_permissions = req.permissions

    if req.platform_template_id:
        tpl = await get_platform_template(req.platform_template_id, db)
        source = RoleSource.FROM_PLATFORM
        platform_template_id = tpl.id
        # Merge: template permissions + any explicitly provided permissions
        if not req.permissions:
            base_permissions = [
                type('P', (), {'module_code': p.module_code, 'page_code': p.page_code, 'action_code': p.action_code})()
                for p in tpl.permissions
            ]

    role = OrganisationRole(
        id=uuid.uuid4(),
        organisation_id=org_id,
        name=req.name,
        description=req.description,
        source=source,
        status=RoleStatus.ACTIVE,
        platform_template_id=platform_template_id,
        created_by_user_id=actor_id,
        current_version=1,
    )
    db.add(role)
    await db.flush()  # get role.id

    # Create version 1
    version = OrganisationRoleVersion(
        id=uuid.uuid4(),
        role_id=role.id,
        version_number=1,
        change_note=req.change_note or "Initial version",
        created_by_user_id=actor_id,
    )
    db.add(version)
    await db.flush()

    # Add permissions
    seen = set()
    for p in base_permissions:
        cap = f"{p.module_code}.{p.page_code}.{p.action_code}"
        if cap in seen:
            continue
        seen.add(cap)
        db.add(OrganisationRolePermission(
            id=uuid.uuid4(),
            version_id=version.id,
            module_code=p.module_code,
            page_code=p.page_code,
            action_code=p.action_code,
        ))

    await _audit(db, org_id, actor_id, "ROLE_CREATED", "organisation_role", role.id,
                 {"name": role.name, "source": source.value})
    await db.commit()
    return await get_role(role.id, org_id, db)


async def update_role(
    role_id: uuid.UUID,
    org_id: uuid.UUID,
    actor_id: uuid.UUID,
    req: RoleUpdateRequest,
    db: AsyncSession,
) -> OrganisationRole:
    role = await get_role(role_id, org_id, db)

    if role.status == RoleStatus.ARCHIVED:
        raise HTTPException(status_code=409, detail="Cannot edit an archived role.")

    if req.name is not None and req.name != role.name:
        dup_stmt = select(OrganisationRole).where(
            OrganisationRole.organisation_id == org_id,
            OrganisationRole.name == req.name,
            OrganisationRole.id != role_id,
        )
        if (await db.execute(dup_stmt)).scalar_one_or_none():
            raise HTTPException(status_code=409, detail=f"A role named '{req.name}' already exists.")
        role.name = req.name

    if req.description is not None:
        role.description = req.description

    if req.permissions is not None:
        _validate_capabilities(req.permissions)
        # Create new version
        new_version_num = role.current_version + 1
        new_version = OrganisationRoleVersion(
            id=uuid.uuid4(),
            role_id=role.id,
            version_number=new_version_num,
            change_note=req.change_note or f"Updated permissions (v{new_version_num})",
            created_by_user_id=actor_id,
        )
        db.add(new_version)
        await db.flush()

        seen = set()
        for p in req.permissions:
            cap = f"{p.module_code}.{p.page_code}.{p.action_code}"
            if cap in seen:
                continue
            seen.add(cap)
            db.add(OrganisationRolePermission(
                id=uuid.uuid4(),
                version_id=new_version.id,
                module_code=p.module_code,
                page_code=p.page_code,
                action_code=p.action_code,
            ))

        role.current_version = new_version_num

        await _audit(db, org_id, actor_id, "ROLE_VERSION_CREATED", "organisation_role", role.id,
                     {"version": new_version_num, "permission_count": len(set(seen))})

    await _audit(db, org_id, actor_id, "ROLE_UPDATED", "organisation_role", role.id,
                 {"name": role.name})
    await db.commit()
    return await get_role(role.id, org_id, db)


async def archive_role(
    role_id: uuid.UUID,
    org_id: uuid.UUID,
    actor_id: uuid.UUID,
    db: AsyncSession,
) -> OrganisationRole:
    role = await get_role(role_id, org_id, db)

    if role.status == RoleStatus.ARCHIVED:
        raise HTTPException(status_code=409, detail="Role is already archived.")

    # Check no active assignments reference this role
    assign_stmt = select(func.count(RoleAssignment.id)).where(
        RoleAssignment.role_id == role_id,
        RoleAssignment.is_active == True,
    )
    count = (await db.execute(assign_stmt)).scalar_one()
    if count > 0:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot archive: {count} member(s) are currently assigned this role. Reassign them first.",
        )

    role.status = RoleStatus.ARCHIVED
    await _audit(db, org_id, actor_id, "ROLE_ARCHIVED", "organisation_role", role.id, {"name": role.name})
    await db.commit()
    return role


# ---------------------------------------------------------------------------
# Role Assignment
# ---------------------------------------------------------------------------

async def assign_role_to_member(
    org_id: uuid.UUID,
    member_id: uuid.UUID,
    actor_id: uuid.UUID,
    req: AssignRoleRequest,
    db: AsyncSession,
) -> Optional[RoleAssignment]:
    # Validate member belongs to org
    member_stmt = select(OrganisationMember).where(
        OrganisationMember.id == member_id,
        OrganisationMember.organisation_id == org_id,
    )
    member = (await db.execute(member_stmt)).scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found in this organisation.")

    # Deactivate existing assignment
    existing_stmt = select(RoleAssignment).where(
        RoleAssignment.member_id == member_id,
        RoleAssignment.organisation_id == org_id,
        RoleAssignment.is_active == True,
    )
    existing = (await db.execute(existing_stmt)).scalar_one_or_none()
    if existing:
        existing.is_active = False
        await _audit(db, org_id, actor_id, "ROLE_REMOVED", "role_assignment", existing.id,
                     {"member_id": str(member_id), "role_id": str(existing.role_id)})

    if req.role_id is None:
        # Unassign only
        await db.commit()
        return None

    # Validate role belongs to same org and is active
    role_stmt = select(OrganisationRole).where(
        OrganisationRole.id == req.role_id,
        OrganisationRole.organisation_id == org_id,
    )
    role = (await db.execute(role_stmt)).scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found in this organisation.")
    if role.status == RoleStatus.ARCHIVED:
        raise HTTPException(status_code=409, detail="Cannot assign an archived role.")

    # Get the current version of the role
    version_stmt = select(OrganisationRoleVersion).where(
        OrganisationRoleVersion.role_id == role.id,
        OrganisationRoleVersion.version_number == role.current_version,
    )
    version = (await db.execute(version_stmt)).scalar_one_or_none()
    if not version:
        raise HTTPException(status_code=500, detail="Role version integrity error.")

    assignment = RoleAssignment(
        id=uuid.uuid4(),
        organisation_id=org_id,
        member_id=member_id,
        role_id=role.id,
        role_version_id=version.id,
        assigned_by_user_id=actor_id,
        is_active=True,
    )
    db.add(assignment)
    await _audit(db, org_id, actor_id, "ROLE_ASSIGNED", "role_assignment", assignment.id,
                 {"member_id": str(member_id), "role_id": str(role.id), "version": role.current_version})
    await db.commit()
    return assignment


# ---------------------------------------------------------------------------
# Permission Overrides
# ---------------------------------------------------------------------------

async def add_permission_override(
    org_id: uuid.UUID,
    member_id: uuid.UUID,
    actor_id: uuid.UUID,
    req: OverrideCreateRequest,
    db: AsyncSession,
) -> UserPermissionOverride:
    cap = f"{req.module_code}.{req.page_code}.{req.action_code}"
    if cap not in VALID_CAPABILITIES:
        raise HTTPException(status_code=400, detail=f"Unknown capability: '{cap}'.")

    # Validate member in org
    member_stmt = select(OrganisationMember).where(
        OrganisationMember.id == member_id,
        OrganisationMember.organisation_id == org_id,
    )
    if not (await db.execute(member_stmt)).scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Member not found in this organisation.")

    # Check duplicate
    dup_stmt = select(UserPermissionOverride).where(
        UserPermissionOverride.member_id == member_id,
        UserPermissionOverride.override_type == req.override_type,
        UserPermissionOverride.module_code == req.module_code,
        UserPermissionOverride.page_code == req.page_code,
        UserPermissionOverride.action_code == req.action_code,
    )
    if (await db.execute(dup_stmt)).scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Override already exists.")

    override = UserPermissionOverride(
        id=uuid.uuid4(),
        organisation_id=org_id,
        member_id=member_id,
        override_type=OverrideType(req.override_type),
        module_code=req.module_code,
        page_code=req.page_code,
        action_code=req.action_code,
        reason=req.reason,
        granted_by_user_id=actor_id,
    )
    db.add(override)
    await _audit(db, org_id, actor_id, "PERMISSION_OVERRIDE_ADDED", "user_permission_override", override.id,
                 {"member_id": str(member_id), "type": req.override_type, "capability": cap})
    await db.commit()
    return override


async def remove_permission_override(
    override_id: uuid.UUID,
    org_id: uuid.UUID,
    actor_id: uuid.UUID,
    db: AsyncSession,
) -> None:
    stmt = select(UserPermissionOverride).where(
        UserPermissionOverride.id == override_id,
        UserPermissionOverride.organisation_id == org_id,
    )
    override = (await db.execute(stmt)).scalar_one_or_none()
    if not override:
        raise HTTPException(status_code=404, detail="Override not found.")

    await _audit(db, org_id, actor_id, "PERMISSION_OVERRIDE_REMOVED", "user_permission_override", override.id,
                 {"member_id": str(override.member_id), "type": override.override_type.value})
    await db.delete(override)
    await db.commit()


# ---------------------------------------------------------------------------
# Effective Permission Resolver — THE authoritative source
# ---------------------------------------------------------------------------

async def resolve_effective_permissions(
    org_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> EffectivePermissionsResponse:
    """
    Resolves the complete effective permission set for a user in an org.
    
    Algorithm:
    1. Get member record (verify membership + commander flag)
    2. If Commander: all capabilities granted (Commander bypasses RBAC)
    3. Else: get active role assignment → role version → permissions
    4. Apply user overrides: + GRANTs, - RESTRICTs
    5. Return structured + flat permission set
    """
    # 1. Get member
    member_stmt = select(OrganisationMember).where(
        OrganisationMember.organisation_id == org_id,
        OrganisationMember.user_id == user_id,
    )
    member = (await db.execute(member_stmt)).scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=403, detail="User is not a member of this organisation.")

    # 2. Commander shortcut — full access to all TMS capabilities
    if member.is_commander:
        all_caps = sorted(VALID_CAPABILITIES)
        structured = _build_structured(all_caps)
        return EffectivePermissionsResponse(
            user_id=user_id,
            organisation_id=org_id,
            is_commander=True,
            permissions=all_caps,
            modules=structured,
        )

    # 3. Role assignment
    assign_stmt = (
        select(RoleAssignment)
        .where(
            RoleAssignment.organisation_id == org_id,
            RoleAssignment.member_id == member.id,
            RoleAssignment.is_active == True,
        )
        .options(selectinload(RoleAssignment.role_version).selectinload(OrganisationRoleVersion.permissions))
        .options(selectinload(RoleAssignment.role))
    )
    assignment = (await db.execute(assign_stmt)).scalar_one_or_none()

    role_id = None
    role_name = None
    role_version = None
    granted_caps: set[str] = set()

    if assignment:
        role_id = assignment.role_id
        role_name = assignment.role.name if assignment.role else None
        role_version = assignment.role_version.version_number if assignment.role_version else None
        for p in (assignment.role_version.permissions if assignment.role_version else []):
            granted_caps.add(f"{p.module_code}.{p.page_code}.{p.action_code}")

    # 4. Apply user overrides
    override_stmt = select(UserPermissionOverride).where(
        UserPermissionOverride.organisation_id == org_id,
        UserPermissionOverride.member_id == member.id,
    )
    overrides = (await db.execute(override_stmt)).scalars().all()

    for ov in overrides:
        cap = f"{ov.module_code}.{ov.page_code}.{ov.action_code}"
        if ov.override_type == OverrideType.GRANT:
            granted_caps.add(cap)
        elif ov.override_type == OverrideType.RESTRICT:
            granted_caps.discard(cap)

    # Filter to only valid capabilities (in case registry changed)
    final_caps = sorted(granted_caps & VALID_CAPABILITIES)
    structured = _build_structured(final_caps)

    return EffectivePermissionsResponse(
        user_id=user_id,
        organisation_id=org_id,
        is_commander=False,
        role_id=role_id,
        role_name=role_name,
        role_version=role_version,
        permissions=final_caps,
        modules=structured,
    )


def _build_structured(flat_caps: list[str]) -> dict[str, dict[str, list[str]]]:
    """Convert flat 'module.page.action' list to nested dict."""
    result: dict[str, dict[str, list[str]]] = {}
    for cap in flat_caps:
        parts = cap.split(".")
        if len(parts) != 3:
            continue
        mod, page, action = parts
        result.setdefault(mod, {}).setdefault(page, []).append(action)
    return result


# ---------------------------------------------------------------------------
# Member listing with role info
# ---------------------------------------------------------------------------

async def list_members_with_roles(org_id: uuid.UUID, db: AsyncSession) -> list[MemberWithRoleResponse]:
    member_stmt = select(OrganisationMember).where(OrganisationMember.organisation_id == org_id)
    members = (await db.execute(member_stmt)).scalars().all()

    # Get all active assignments for this org
    assign_stmt = (
        select(RoleAssignment)
        .where(RoleAssignment.organisation_id == org_id, RoleAssignment.is_active == True)
        .options(selectinload(RoleAssignment.role))
    )
    assignments = (await db.execute(assign_stmt)).scalars().all()
    assign_map = {a.member_id: a for a in assignments}

    out = []
    for m in members:
        assignment = assign_map.get(m.id)
        out.append(MemberWithRoleResponse(
            member_id=m.id,
            user_id=m.user_id,
            organisation_id=m.organisation_id,
            status=m.status.value,
            is_commander=m.is_commander,
            is_creator=m.is_creator,
            role_id=assignment.role_id if assignment else None,
            role_name=assignment.role.name if assignment and assignment.role else None,
            role_status=assignment.role.status.value if assignment and assignment.role else None,
            created_at=m.created_at,
        ))
    return out


# ---------------------------------------------------------------------------
# Audit helper
# ---------------------------------------------------------------------------

async def _audit(
    db: AsyncSession,
    org_id: uuid.UUID,
    actor_id: uuid.UUID,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID,
    meta: dict,
) -> None:
    db.add(AuditLog(
        id=uuid.uuid4(),
        organisation_id=org_id,
        actor_user_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        metadata_=meta,
    ))
