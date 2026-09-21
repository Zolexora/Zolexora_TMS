import logging
import uuid
from fastapi import HTTPException, status
from sqlalchemy import select

from app.modules.core.platform.models import (
    TenantDatabaseRegistry,
    TenantMongodbRegistry,
    OrganisationDatabaseAssignment,
    OrganisationMongodbAssignment,
    OrganisationStorageAssignment,
    RegistryStatus,
)
from sqlalchemy import update

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.organisations.models import Organisation, OrganisationStatus
from app.modules.identity.organisations.membership_models import OrganisationMember, MemberStatus
from app.modules.identity.roles.models import Role
from app.modules.identity.organisations.schemas import (
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
                role_code="CREATOR" if existing_membership.is_creator else "MEMBER",
                message="User already has an active workspace",
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
    await db.flush()

    # 4. Assign initial creator
    member = OrganisationMember(
        id=uuid.uuid4(),
        organisation_id=org_id,
        user_id=user_id,
        status=MemberStatus.ACTIVE,
        is_creator=True,
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

    # 5. Create Default Customization Definition
    from app.modules.core.customization.models import OrganisationApplication, ApplicationType, ApplicationStatus
    app_def = OrganisationApplication(
        id=uuid.uuid4(),
        organisation_id=org_id,
        application_type=ApplicationType.STANDARD,
        application_name=f"{req.name.strip()} TMS",
        application_version="1.0.0",
        status=ApplicationStatus.ACTIVE
    )
    db.add(app_def)

    # 6. Audit Log Entry
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
        select(OrganisationMember)
        .where(OrganisationMember.organisation_id == org_id)
        .order_by(OrganisationMember.created_at.asc())
    )
    res = await db.execute(stmt)
    rows = res.scalars().all()

    members = []
    for member in rows:
        members.append(
            MemberResponse(
                id=member.id,
                organisation_id=member.organisation_id,
                user_id=member.user_id,
                status=member.status,
                created_at=member.created_at,
                is_creator=member.is_creator,
            )
        )
    return members


async def invite_member(
    org_id: uuid.UUID,
    actor_id: uuid.UUID,
    req: MemberInviteRequest,
    db: AsyncSession,
) -> MemberResponse:
    import datetime, secrets
    from app.modules.identity.organisations.membership_models import OrganisationInvitation
    
    # Check if user already invited
    existing_invite_stmt = select(OrganisationInvitation).where(
        OrganisationInvitation.organisation_id == org_id,
        OrganisationInvitation.email == req.email,
        OrganisationInvitation.status == "PENDING"
    )
    existing = (await db.execute(existing_invite_stmt)).scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail="User already invited")
        
    token = secrets.token_urlsafe(32)
    expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)
    
    invitation = OrganisationInvitation(
        id=uuid.uuid4(),
        organisation_id=org_id,
        email=req.email,
        token=token,
        status="PENDING",
        expires_at=expires_at,
        created_by=actor_id
    )
    db.add(invitation)
    await db.commit()
    await db.refresh(invitation)

    return {"message": "Invitation sent successfully", "invitation_id": invitation.id}
