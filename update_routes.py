import re

filepath = "apps/backend/app/modules/identity/organisations/routes.py"
with open(filepath, "r") as f:
    content = f.read()

# Add schemas to import
content = content.replace("    OrganisationResponse,", "    OrganisationResponse,\n    CommanderTransferRequest,")

# Add service to import
content = content.replace("    list_organisation_members,", "    list_organisation_members,\n    transfer_commander,")

# Add route
route = """

@router.post("/organisations/commander/transfer")
async def transfer_commander_route(
    req: CommanderTransferRequest,
    user: AuthenticatedIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
):
    # We resolve the membership via db to ensure atomic checks
    # A user can only access this if they are the commander of the org they're trying to transfer
    # X-Organization-Id must be provided in headers for context.
    from app.auth.dependencies import get_current_active_organisation
    from fastapi import Depends, Request
    # Actually it's easier to just use get_current_active_organisation to get the org context
    pass
"""

# Let me write this better by appending cleanly
