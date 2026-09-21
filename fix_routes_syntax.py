import re

filepath = "apps/backend/app/modules/identity/organisations/routes.py"
with open(filepath, "r") as f:
    content = f.read()

content = content.replace("from app.modules.identity.organisations.schemas import (\\n    InvitationResponse,", "from app.modules.identity.organisations.schemas import (\\n    InvitationResponse,")

with open(filepath, "w") as f:
    f.write(content)
