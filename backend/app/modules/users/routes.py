from fastapi import APIRouter, Depends
from pydantic import BaseModel
import uuid
from typing import List, Optional

from app.auth.dependencies import AuthenticatedUser, get_current_user

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


class UserMeResponse(BaseModel):
    id: uuid.UUID
    email: Optional[str]
    full_name: Optional[str]
    organisation_id: Optional[uuid.UUID]
    role_code: Optional[str]
    permissions: List[str]


@router.get("/me", response_model=UserMeResponse)
async def get_current_user_profile(
    user: AuthenticatedUser = Depends(get_current_user),
):
    return UserMeResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        organisation_id=user.organisation_id,
        role_code=user.role_code,
        permissions=user.permissions,
    )
