from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.modules.identity.organisations.models import OrganisationStatus, OrganisationType
from app.modules.identity.organisations.membership_models import MemberStatus


class OrganisationBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=160, description="Legal business/organisation name")
    organisation_type: OrganisationType = Field(..., description="Legal classification of organisation")


class OrganisationCreate(OrganisationBase):
    pass


class OrganisationResponse(OrganisationBase):
    id: uuid.UUID
    status: OrganisationStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OnboardingRequest(OrganisationBase):
    pass


class OnboardingResponse(BaseModel):
    organisation: OrganisationResponse
    role_code: str
    message: str


class MemberInviteRequest(BaseModel):
    email: str = Field(..., description="Email address of user to invite")


class MemberResponse(BaseModel):
    id: uuid.UUID
    organisation_id: uuid.UUID
    user_id: uuid.UUID
    status: MemberStatus
    is_creator: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class InvitationResponse(BaseModel):
    id: uuid.UUID
    organisation_id: uuid.UUID
    email: str
    status: str
    expires_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
