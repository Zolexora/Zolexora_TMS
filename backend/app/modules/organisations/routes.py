from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import (
    AuthenticatedUser,
    get_current_user,
    require_permission,
)
from app.db.session import get_db
from app.modules.organisations.schemas import (
    MemberInviteRequest,
    MemberResponse,
    OnboardingRequest,
    OnboardingResponse,
    OrganisationResponse,
)
from app.modules.organisations.service import (
    complete_onboarding,
    get_organisation_by_id,
    invite_member,
    list_organisation_members,
)

router = APIRouter(prefix="/api/v1", tags=["Organisations & Onboarding"])


@router.post("/onboarding", response_model=OnboardingResponse, status_code=status.HTTP_201_CREATED)
async def create_organisation_and_commander(
    request: Request,
    req: OnboardingRequest,
    user: AuthenticatedUser = Depends(get_current_user),
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
    user: AuthenticatedUser = Depends(get_current_user),
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


@router.post("/organisations/members/invite", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
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
