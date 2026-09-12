from typing import Any, Callable, Dict, List, Optional
import uuid
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenant import TenantContext
from app.modules.platform.models import ProviderType


from app.auth.jwks import verify_supabase_jwt
from app.db.session import get_db

security = HTTPBearer(auto_error=False)


class AuthenticatedUser(BaseModel):
    id: uuid.UUID
    email: Optional[str] = None
    full_name: Optional[str] = None
    organisation_id: Optional[uuid.UUID] = None
    role_code: Optional[str] = None
    permissions: List[str] = []

    @property
    def user_id(self) -> uuid.UUID:
        return self.id

    def has_permission(self, permission: str) -> bool:
        if self.role_code == "COMMANDER":
            return True
        return permission in self.permissions


CurrentUserContext = AuthenticatedUser


async def get_current_claims(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
) -> Dict[str, Any]:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization credentials were not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        claims = await verify_supabase_jwt(credentials.credentials)
        return claims
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired authorization token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    claims: Dict[str, Any] = Depends(get_current_claims),
    db: AsyncSession = Depends(get_db),
) -> AuthenticatedUser:
    sub = claims.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token subject (sub) missing",
        )
    try:
        user_uuid = uuid.UUID(sub)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID format in token",
        )

    # Query active organisation membership & role from PostgreSQL
    query = text("""
        SELECT 
            m.organisation_id,
            r.code as role_code,
            p.full_name,
            m.created_at,
            array_agg(perm.code) FILTER (WHERE perm.code IS NOT NULL) as permissions
        FROM public.organisation_members m
        JOIN public.roles r ON r.id = m.role_id
        LEFT JOIN public.profiles p ON p.id = m.user_id
        LEFT JOIN public.role_permissions rp ON rp.role_id = r.id
        LEFT JOIN public.permissions perm ON perm.id = rp.permission_id
        WHERE m.user_id = :user_id AND m.status = 'ACTIVE'
        GROUP BY m.organisation_id, r.code, p.full_name, m.created_at
        ORDER BY m.created_at ASC
        LIMIT 1
    """)
    result = await db.execute(query, {"user_id": user_uuid})
    row = result.mappings().first()

    org_id = row["organisation_id"] if row else None
    role_code = row["role_code"] if row else None
    full_name = row["full_name"] if row else claims.get("user_metadata", {}).get("full_name")
    perms = list(row["permissions"]) if row and row["permissions"] else []

    return AuthenticatedUser(
        id=user_uuid,
        email=claims.get("email"),
        full_name=full_name,
        organisation_id=org_id,
        role_code=role_code,
        permissions=perms,
    )


def require_permission(permission: str) -> Callable:
    async def dependency(user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
        if not user.organisation_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not belong to an active organisation. Onboarding required.",
            )
        if not user.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions: '{permission}' required",
            )
        return user
    return dependency


async def require_commander(user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
    if user.role_code != "COMMANDER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the Organisation Commander can perform this action",
        )
    return user


async def get_current_active_organisation(
    user: AuthenticatedUser = Depends(get_current_user),
) -> AuthenticatedUser:
    if not user.organisation_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not belong to an active organisation. Onboarding required.",
        )
    return user


async def get_tenant_context(
    user: AuthenticatedUser = Depends(get_current_active_organisation),
    db: AsyncSession = Depends(get_db),
) -> TenantContext:
    # Resolve assignments
    query = text("""
        SELECT 
            da.assignment_status,
            dr.provider as db_provider,
            dr.database_identifier,
            mr.cluster_identifier,
            ma.database_name as mongo_db_name,
            sa.cloudinary_folder_prefix,
            sa.r2_bucket,
            sa.r2_prefix
        FROM public.organisation_database_assignments da
        JOIN public.tenant_database_registry dr ON dr.id = da.database_registry_id
        LEFT JOIN public.organisation_mongodb_assignments ma ON ma.organisation_id = da.organisation_id AND ma.status = 'ACTIVE'
        LEFT JOIN public.tenant_mongodb_registry mr ON mr.id = ma.mongodb_registry_id
        LEFT JOIN public.organisation_storage_assignments sa ON sa.organisation_id = da.organisation_id
        WHERE da.organisation_id = :org_id AND da.assignment_status = 'ACTIVE'
        LIMIT 1
    """)
    
    result = await db.execute(query, {"org_id": user.organisation_id})
    row = result.mappings().first()
    
    if not row:
        # Fallback to defaults or raise error
        # In transition phase, we might not have assignments for everyone, so we could assume POSTGRESQL for existing orgs
        return TenantContext(
            organisation_id=user.organisation_id,
            tenant_database_provider=ProviderType.POSTGRESQL,
            tenant_database_identifier="default_postgres",
            mongodb_cluster_identifier=None,
            mongodb_database_name=None,
            cloudinary_prefix=f"zolexora/organisations/{user.organisation_id}/",
            r2_bucket="tms-documents",
            r2_prefix=f"organisations/{user.organisation_id}/"
        )
        
    return TenantContext(
        organisation_id=user.organisation_id,
        tenant_database_provider=ProviderType(row["db_provider"]),
        tenant_database_identifier=row["database_identifier"],
        mongodb_cluster_identifier=row["cluster_identifier"],
        mongodb_database_name=row["mongo_db_name"],
        cloudinary_prefix=row["cloudinary_folder_prefix"] or f"zolexora/organisations/{user.organisation_id}/",
        r2_bucket=row["r2_bucket"] or "tms-documents",
        r2_prefix=row["r2_prefix"] or f"organisations/{user.organisation_id}/"
    )

async def require_platform_admin(user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
    if "PLATFORM_ADMIN" not in user.permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Platform Administrators can perform this action",
        )
    return user
