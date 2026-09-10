from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.modules.organisations.models import OrganisationStatus, OrganisationType
from app.modules.organisations.membership_models import MemberStatus


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
    role_code: str = Field(..., description="Role code (must NOT be COMMANDER)")

    @field_validator("role_code")
    @classmethod
    def validate_role_not_commander(cls, v: str) -> str:
        if v.upper() == "COMMANDER":
            raise ValueError("Commander role is reserved strictly for the initial organisation creator and cannot be assigned.")
        return v.upper()


class MemberResponse(BaseModel):
    id: uuid.UUID
    organisation_id: uuid.UUID
    user_id: uuid.UUID
    role_code: str
    role_name: str
    status: MemberStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
