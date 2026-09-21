import re

filepath = "apps/backend/app/modules/identity/organisations/routes.py"
with open(filepath, "r") as f:
    content = f.read()

content = content.replace(
    "from app.auth.dependencies import (",
    "from app.auth.dependencies import (\n    AuthenticatedIdentity,\n    get_current_identity,"
)

content = content.replace(
    "user: AuthenticatedUser = Depends(get_current_user),",
    "user: AuthenticatedIdentity = Depends(get_current_identity),"
)

with open(filepath, "w") as f:
    f.write(content)
