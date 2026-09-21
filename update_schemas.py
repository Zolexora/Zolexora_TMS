filepath = "apps/backend/app/modules/identity/organisations/schemas.py"
with open(filepath, "r") as f:
    content = f.read()

content = content.replace("is_creator: bool", "is_creator: bool\n    is_commander: bool")

transfer_schema = """
class CommanderTransferRequest(BaseModel):
    new_commander_user_id: uuid.UUID
    former_commander_role: str = Field(..., description="Role code assigned to the former commander after transfer")
    password: Optional[str] = Field(None, description="Current password for re-authentication confirmation if applicable")
"""

content += transfer_schema

with open(filepath, "w") as f:
    f.write(content)
