from fastapi import APIRouter, Depends
from pydantic import BaseModel
import uuid
from typing import List, Optional

from app.auth.dependencies import AuthenticatedUser, get_current_user
from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


class UserMeResponse(BaseModel):
    """
    Auth context returned after successful token verification.
    Includes Commander flag and is_creator for the UI.
    For full effective permissions, call /api/v1/organisations/me/effective-permissions.
    """
    id: uuid.UUID
    # frontend uses user_id as alias
    user_id: uuid.UUID
    email: Optional[str]
    full_name: Optional[str]
    organisation_id: Optional[uuid.UUID]
    is_creator: bool
    is_commander: bool
    # role_code is null until roles are assigned (Prompt 07+)
    role_code: Optional[str] = None


@router.get("/me", response_model=UserMeResponse)
async def get_current_user_profile(
    user: AuthenticatedUser = Depends(get_current_user),
):
    return UserMeResponse(
        id=user.id,
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        organisation_id=user.organisation_id,
        is_creator=user.is_creator,
        is_commander=user.is_commander,
    )


from app.modules.identity.organisations.models import Organisation
from app.modules.identity.organisations.membership_models import OrganisationMember, MemberStatus
from sqlalchemy import select


class UserOrganisationResponse(BaseModel):
    id: uuid.UUID
    name: str
    is_creator: bool
    is_commander: bool


@router.get("/my-organisations", response_model=List[UserOrganisationResponse])
async def get_my_organisations(
    user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Organisation, OrganisationMember)
        .join(OrganisationMember, OrganisationMember.organisation_id == Organisation.id)
        .where(
            OrganisationMember.user_id == user.id,
            OrganisationMember.status == MemberStatus.ACTIVE
        )
    )
    res = await db.execute(stmt)
    rows = res.all()
    return [
        UserOrganisationResponse(
            id=org.id,
            name=org.name,
            is_creator=member.is_creator,
            is_commander=member.is_commander,
        ) for org, member in rows
    ]
