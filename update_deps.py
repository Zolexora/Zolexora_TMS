filepath = "apps/backend/app/auth/dependencies.py"
with open(filepath, "r") as f:
    content = f.read()

old_model = """class AuthenticatedUser(AuthenticatedIdentity):
    organisation_id: uuid.UUID
    role_code: str
    permissions: List[str] = []

    @property
    def user_id(self) -> uuid.UUID:
        return self.id

    def has_permission(self, permission: str) -> bool:
        if self.role_code == "COMMANDER":
            return True
        return permission in self.permissions"""

new_model = """class AuthenticatedUser(AuthenticatedIdentity):
    organisation_id: uuid.UUID
    is_creator: bool = False
    is_commander: bool = False
    
    # We will implement actual role systems in Prompt 07. For now, stub permissions.
    role_code: Optional[str] = None
    permissions: List[str] = []

    @property
    def user_id(self) -> uuid.UUID:
        return self.id

    def has_permission(self, permission: str) -> bool:
        if self.is_commander:
            return True
        return permission in self.permissions"""

content = content.replace(old_model, new_model)
content = content.replace("is_creator=row[\"is_creator\"],", "is_creator=row[\"is_creator\"],\n        is_commander=row[\"is_commander\"],")

with open(filepath, "w") as f:
    f.write(content)
