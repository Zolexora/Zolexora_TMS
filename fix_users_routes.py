import re

filepath = "apps/backend/app/modules/identity/users/routes.py"
with open(filepath, "r") as f:
    content = f.read()

# Fix UserMeResponse
old_model = """class UserMeResponse(BaseModel):
    id: uuid.UUID
    email: Optional[str]
    full_name: Optional[str]
    organisation_id: Optional[uuid.UUID]
    role_code: Optional[str]
    permissions: List[str]"""
new_model = """class UserMeResponse(BaseModel):
    id: uuid.UUID
    email: Optional[str]
    full_name: Optional[str]
    organisation_id: Optional[uuid.UUID]
    is_creator: bool"""
content = content.replace(old_model, new_model)

# Fix endpoint mapping
old_mapping = """        id=user.id,
        email=user.email,
        full_name=user.full_name,
        organisation_id=user.organisation_id,
        role_code=user.role_code,
        permissions=user.permissions,"""
new_mapping = """        id=user.id,
        email=user.email,
        full_name=user.full_name,
        organisation_id=user.organisation_id,
        is_creator=user.is_creator,"""
content = content.replace(old_mapping, new_mapping)

# Add memberships endpoint
additional_endpoint = """
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.modules.identity.organisations.models import Organisation
from app.modules.identity.organisations.membership_models import OrganisationMember, MemberStatus

class UserOrganisationResponse(BaseModel):
    id: uuid.UUID
    name: str
    is_creator: bool

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
            is_creator=member.is_creator
        ) for org, member in rows
    ]
"""
content += additional_endpoint

with open(filepath, "w") as f:
    f.write(content)
