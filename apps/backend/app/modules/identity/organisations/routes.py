from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import (
    AuthenticatedIdentity,
    get_current_identity,
    AuthenticatedUser,
    get_current_user,
    require_permission,
)
from app.db.session import get_db
from app.modules.identity.organisations.schemas import (
    InvitationResponse,
    MemberInviteRequest,
    MemberResponse,
    OnboardingRequest,
    OnboardingResponse,
    OrganisationResponse,
    CommanderTransferRequest,
)
from app.modules.identity.organisations.service import (
    complete_onboarding,
    get_organisation_by_id,
    invite_member,
    list_organisation_members,
    transfer_commander,
)

router = APIRouter(prefix="/api/v1", tags=["Organisations & Onboarding"])


@router.post("/onboarding", response_model=OnboardingResponse, status_code=status.HTTP_201_CREATED)
async def create_organisation_and_commander(
    request: Request,
    req: OnboardingRequest,
    user: AuthenticatedIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
):
    ip_addr = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")
    return await complete_onboarding(
        user_id=user.id,
        req=req,
        db=db,
        ip_address=ip_addr,
        user_agent=user_agent,
    )


@router.get("/organisations/me", response_model=OrganisationResponse)
async def get_my_organisation(
    user: AuthenticatedIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
):
    return await get_organisation_by_id(
        org_id=user.organisation_id,
        user_id=user.id,
        db=db,
    )


@router.get("/organisations/members", response_model=list[MemberResponse])
async def get_members(
    user: AuthenticatedUser = Depends(require_permission("users.manage")),
    db: AsyncSession = Depends(get_db),
):
    return await list_organisation_members(org_id=user.organisation_id, db=db)


@router.post("/organisations/members/invite")
async def invite_new_member(
    req: MemberInviteRequest,
    user: AuthenticatedUser = Depends(require_permission("users.manage")),
    db: AsyncSession = Depends(get_db),
):
    return await invite_member(
        org_id=user.organisation_id,
        actor_id=user.id,
        req=req,
        db=db,
    )

@router.post("/organisations/commander/transfer")
async def transfer_commander_route(
    req: CommanderTransferRequest,
    user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not user.is_commander:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the Commander can transfer Commander authority."
        )
    return await transfer_commander(
        org_id=user.organisation_id,
        current_commander_id=user.id,
        req=req,
        db=db,
    )

@router.delete("/organisations/members/{user_id}")
async def remove_member(
    user_id: str,
    user: AuthenticatedUser = Depends(require_permission("users.manage")),
    db: AsyncSession = Depends(get_db),
):
    from fastapi import HTTPException
    import uuid
    target_id = uuid.UUID(user_id)
    
    # Self-protection logic
    if target_id == user.id and user.is_commander:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Commander cannot remove their own membership. Transfer Commander authority first."
        )
        
    # In a full implementation, we'd delete or suspend the user here.
    # For now we'll just throw 501 Not Implemented because the rest of it belongs to later phases.
    raise HTTPException(status_code=501, detail="Member removal is planned for a later phase.")
