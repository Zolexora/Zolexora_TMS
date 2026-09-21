import re

filepath = "apps/backend/app/modules/identity/organisations/routes.py"
with open(filepath, "r") as f:
    content = f.read()

content = content.replace("from app.modules.identity.organisations.schemas import (", "from app.modules.identity.organisations.schemas import (\\n    InvitationResponse,")
content = content.replace("@router.post(\"/organisations/members/invite\", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)", "@router.post(\"/organisations/members/invite\")")

with open(filepath, "w") as f:
    f.write(content)
