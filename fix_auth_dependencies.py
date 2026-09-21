import re

filepath = "apps/backend/app/auth/dependencies.py"
with open(filepath, "r") as f:
    content = f.read()

# Fix AuthenticatedUser model
auth_user_old = """class AuthenticatedUser(AuthenticatedIdentity):
    organisation_id: uuid.UUID
    role_code: str
    permissions: List[str] = []

    def has_permission(self, permission: str) -> bool:
        if self.role_code == "COMMANDER":
            return True
        return permission in self.permissions"""
auth_user_new = """class AuthenticatedUser(AuthenticatedIdentity):
    organisation_id: uuid.UUID
    is_creator: bool

    def has_permission(self, permission: str) -> bool:
        # Prompt 05: Do not implement permissions yet. Return True for now to keep things working.
        return True"""
content = content.replace(auth_user_old, auth_user_new)

# Fix get_current_active_organisation 
org_func_old = """        query = text(\"\"\"
            SELECT 
                m.organisation_id,
                r.code as role_code,
                array_agg(perm.code) FILTER (WHERE perm.code IS NOT NULL) as permissions
            FROM public.organisation_members m
            JOIN public.roles r ON r.id = m.role_id
            LEFT JOIN public.role_permissions rp ON rp.role_id = r.id
            LEFT JOIN public.permissions perm ON perm.id = rp.permission_id
            WHERE m.user_id = :user_id AND m.organisation_id = :org_id AND m.status = 'ACTIVE'
            GROUP BY m.organisation_id, r.code
        \"\"\")"""
org_func_new = """        query = text(\"\"\"
            SELECT 
                m.organisation_id,
                m.is_creator
            FROM public.organisation_members m
            WHERE m.user_id = :user_id AND m.organisation_id = :org_id AND m.status = 'ACTIVE'
        \"\"\")"""
content = content.replace(org_func_old, org_func_new)

org_func_fb_old = """        query = text(\"\"\"
            SELECT 
                m.organisation_id,
                r.code as role_code,
                array_agg(perm.code) FILTER (WHERE perm.code IS NOT NULL) as permissions
            FROM public.organisation_members m
            JOIN public.roles r ON r.id = m.role_id
            LEFT JOIN public.role_permissions rp ON rp.role_id = r.id
            LEFT JOIN public.permissions perm ON perm.id = rp.permission_id
            WHERE m.user_id = :user_id AND m.status = 'ACTIVE'
            GROUP BY m.organisation_id, r.code
            ORDER BY m.created_at ASC
            LIMIT 1
        \"\"\")"""
org_func_fb_new = """        query = text(\"\"\"
            SELECT 
                m.organisation_id,
                m.is_creator
            FROM public.organisation_members m
            WHERE m.user_id = :user_id AND m.status = 'ACTIVE'
            ORDER BY m.created_at ASC
            LIMIT 1
        \"\"\")"""
content = content.replace(org_func_fb_old, org_func_fb_new)

# Fix AuthenticatedUser instantiation
auth_user_inst_old = """    return AuthenticatedUser(
        id=identity.id,
        email=identity.email,
        full_name=identity.full_name,
        organisation_id=row["organisation_id"],
        role_code=row["role_code"],
        permissions=list(row["permissions"]) if row["permissions"] else [],
    )"""
auth_user_inst_new = """    return AuthenticatedUser(
        id=identity.id,
        email=identity.email,
        full_name=identity.full_name,
        organisation_id=row["organisation_id"],
        is_creator=row["is_creator"],
    )"""
content = content.replace(auth_user_inst_old, auth_user_inst_new)

# Fix require_commander
req_comm_old = """async def require_commander(user: AuthenticatedUser = Depends(get_current_active_organisation)) -> AuthenticatedUser:
    if user.role_code != "COMMANDER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the Organisation Commander can perform this action",
        )
    return user"""
req_comm_new = """async def require_commander(user: AuthenticatedUser = Depends(get_current_active_organisation)) -> AuthenticatedUser:
    if not user.is_creator:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the Organisation Creator (Commander) can perform this action",
        )
    return user"""
content = content.replace(req_comm_old, req_comm_new)

# Fix TenantContext update
tc_old = """        user_id=user.id,
        role_code=user.role_code,
        permissions=user.permissions"""
tc_new = """        user_id=user.id,
        role_code="CREATOR" if user.is_creator else "MEMBER",
        permissions=[]"""
content = content.replace(tc_old, tc_new)

with open(filepath, "w") as f:
    f.write(content)
