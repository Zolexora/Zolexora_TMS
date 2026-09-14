import logging
import uuid
from fastapi import HTTPException, status
from sqlalchemy import select

from app.modules.platform.models import (
    TenantDatabaseRegistry,
    TenantMongodbRegistry,
    OrganisationDatabaseAssignment,
    OrganisationMongodbAssignment,
    OrganisationStorageAssignment,
    RegistryStatus,
)
from sqlalchemy import update

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.organisations.models import Organisation, OrganisationStatus
from app.modules.organisations.membership_models import OrganisationMember, MemberStatus
from app.modules.roles.models import Role
from app.modules.organisations.schemas import (
    MemberInviteRequest,
    MemberResponse,
    OnboardingRequest,
    OnboardingResponse,
    OrganisationResponse,
)

logger = logging.getLogger(__name__)


async def complete_onboarding(
    user_id: uuid.UUID,
    req: OnboardingRequest,
    db: AsyncSession,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> OnboardingResponse:
    # 1. Check if user is already an active member of an organisation
    stmt = (
        select(OrganisationMember)
        .where(
            OrganisationMember.user_id == user_id,
            OrganisationMember.status == MemberStatus.ACTIVE,
        )
        .order_by(OrganisationMember.created_at.asc())
    )
    res = await db.execute(stmt)
    existing_membership = res.scalars().first()

    if existing_membership:
        org_stmt = select(Organisation).where(Organisation.id == existing_membership.organisation_id)
        org_res = await db.execute(org_stmt)
        org = org_res.scalars().first()
        if org:
            return OnboardingResponse(
                organisation=OrganisationResponse.model_validate(org),
                role_code=existing_membership.role.code if existing_membership.role else "COMMANDER",
                message="User already has an active workspace",
            )

    # 2. Query Commander role
    role_stmt = select(Role).where(Role.code == "COMMANDER")
    role_res = await db.execute(role_stmt)
    commander_role = role_res.scalars().first()
    if not commander_role:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Commander role definition is missing from database",
        )

    org_id = uuid.uuid4()
    
    # 2.5 INFRASTRUCTURE ASSIGNMENT
    # Find an AVAILABLE D1 database
    d1_stmt = (
        select(TenantDatabaseRegistry)
        .where(TenantDatabaseRegistry.status == RegistryStatus.AVAILABLE)
        .with_for_update(skip_locked=True)
        .limit(1)
    )
    d1_res = await db.execute(d1_stmt)
    d1_db = d1_res.scalars().first()
    if not d1_db:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No D1 tenant databases are currently available for provisioning.",
        )
        
    # Find an AVAILABLE MongoDB database
    mongo_stmt = (
        select(TenantMongodbRegistry)
        .where(TenantMongodbRegistry.status == RegistryStatus.AVAILABLE)
        .with_for_update(skip_locked=True)
        .limit(1)
    )
    mongo_res = await db.execute(mongo_stmt)
    mongo_db = mongo_res.scalars().first()
    if not mongo_db:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No MongoDB tenant namespaces are currently available for provisioning.",
        )
    
    # Mark them as assigned
    d1_db.status = RegistryStatus.ASSIGNED
    d1_db.assigned_organisation_id = org_id
    
    mongo_db.status = RegistryStatus.ASSIGNED

    # 3. Create Organisation
    org = Organisation(
        id=org_id,
        name=req.name.strip(),
        organisation_type=req.organisation_type.value,
        status=OrganisationStatus.ACTIVE, # In a fully asynchronous flow this would be PROVISIONING
    )
    db.add(org)

    # 4. Assign initial creator as Commander
    member = OrganisationMember(
        id=uuid.uuid4(),
        organisation_id=org_id,
        user_id=user_id,
        role_id=commander_role.id,
        status=MemberStatus.ACTIVE,
    )
    db.add(member)
    
    # 4.5 Create Assignment Records
    d1_assignment = OrganisationDatabaseAssignment(
        id=uuid.uuid4(),
        organisation_id=org_id,
        database_registry_id=d1_db.id,
        assignment_status="ACTIVE",
        provisioning_status="READY"
    )
    db.add(d1_assignment)
    
    mongo_assignment = OrganisationMongodbAssignment(
        id=uuid.uuid4(),
        organisation_id=org_id,
        mongodb_registry_id=mongo_db.id,
        database_name=mongo_db.database_name,
        namespace_prefix=f"zolexora_tenant_{org_id}",
        status="ACTIVE"
    )
    db.add(mongo_assignment)
    
    storage_assignment = OrganisationStorageAssignment(
        id=uuid.uuid4(),
        organisation_id=org_id,
        cloudinary_folder_prefix=f"zolexora/organisations/{org_id}/",
        r2_bucket="tms-documents",
        r2_prefix=f"organisations/{org_id}/"
    )
    db.add(storage_assignment)

    # 5. Audit Log Entry
    # (assuming platform_audit_logs handles itself or we add one later)

    # Atomically commit everything
    await db.commit()
    await db.refresh(org)

    logger.info(f"Organisation '{org.name}' ({org.id}) created by Commander ({user_id})")

    return OnboardingResponse(
        organisation=OrganisationResponse.model_validate(org),
        role_code="COMMANDER",
        message="Organisation workspace initialized successfully with Commander authority",
    )


async def get_organisation_by_id(
    org_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> OrganisationResponse:
    # Tenant Isolation: verify caller is an active member
    mem_stmt = select(OrganisationMember).where(
        OrganisationMember.organisation_id == org_id,
        OrganisationMember.user_id == user_id,
        OrganisationMember.status == MemberStatus.ACTIVE,
    )
    mem_res = await db.execute(mem_stmt)
    membership = mem_res.scalars().first()
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You do not belong to this organisation",
        )

    org_stmt = select(Organisation).where(Organisation.id == org_id)
    org_res = await db.execute(org_stmt)
    org = org_res.scalars().first()
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organisation not found",
        )

    return OrganisationResponse.model_validate(org)


async def list_organisation_members(
    org_id: uuid.UUID,
    db: AsyncSession,
) -> list[MemberResponse]:
    stmt = (
        select(OrganisationMember, Role)
        .join(Role, Role.id == OrganisationMember.role_id)
        .where(OrganisationMember.organisation_id == org_id)
        .order_by(OrganisationMember.created_at.asc())
    )
    res = await db.execute(stmt)
    rows = res.all()

    members = []
    for member, role in rows:
        members.append(
            MemberResponse(
                id=member.id,
                organisation_id=member.organisation_id,
                user_id=member.user_id,
                role_code=role.code,
                role_name=role.name,
                status=member.status,
                created_at=member.created_at,
            )
        )
    return members


async def invite_member(
    org_id: uuid.UUID,
    actor_id: uuid.UUID,
    req: MemberInviteRequest,
    db: AsyncSession,
) -> MemberResponse:
    # Find role
    role_stmt = select(Role).where(Role.code == req.role_code)
    role_res = await db.execute(role_stmt)
    target_role = role_res.scalars().first()
    if not target_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role '{req.role_code}' does not exist",
        )

    # In a real invite flow, we create an invitation token or placeholder user
    invited_user_id = uuid.uuid4()
    member = OrganisationMember(
        id=uuid.uuid4(),
        organisation_id=org_id,
        user_id=invited_user_id,
        role_id=target_role.id,
        status=MemberStatus.INVITED,
    )
    db.add(member)


    await db.commit()
    await db.refresh(member)

    return MemberResponse(
        id=member.id,
        organisation_id=member.organisation_id,
        user_id=member.user_id,
        role_code=target_role.code,
        role_name=target_role.name,
        status=member.status,
        created_at=member.created_at,
    )
