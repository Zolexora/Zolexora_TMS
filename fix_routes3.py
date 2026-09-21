import re

filepath = "apps/backend/app/modules/identity/organisations/routes.py"
with open(filepath, "r") as f:
    content = f.read()

content = content.replace("    OrganisationResponse,", "    OrganisationResponse,\n    CommanderTransferRequest,")
content = content.replace("    list_organisation_members,", "    list_organisation_members,\n    transfer_commander,")

with open(filepath, "w") as f:
    f.write(content)
