from typing import Any, Callable, Dict, List, Optional
import uuid
from fastapi import Depends, HTTPException, Security, status, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenant import TenantContext
from app.modules.core.platform.models import ProviderType
from app.auth.jwks import verify_supabase_jwt
from app.db.session import get_db

security = HTTPBearer(auto_error=False)

class AuthenticatedIdentity(BaseModel):
    id: uuid.UUID
    email: Optional[str] = None
    full_name: Optional[str] = None

class AuthenticatedUser(AuthenticatedIdentity):
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

async def get_current_identity(
    claims: Dict[str, Any] = Depends(get_current_claims),
) -> AuthenticatedIdentity:
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

    full_name = claims.get("user_metadata", {}).get("full_name")
    return AuthenticatedIdentity(
        id=user_uuid,
        email=claims.get("email"),
        full_name=full_name,
    )

async def get_current_active_organisation(
    request: Request,
    identity: AuthenticatedIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
) -> AuthenticatedUser:
    """
    Validates organization membership and establishes Tenant Context boundary.
    Never trusts frontend implicitly.
    """
    requested_org_id_str = request.headers.get("X-Organization-Id")
    
    # Securely resolve organization based on explicit request + validation
    if requested_org_id_str:
        try:
            requested_org_id = uuid.UUID(requested_org_id_str)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid X-Organization-Id header format")
            
        query = text("""
            SELECT 
                m.organisation_id,
                m.is_creator,
                m.is_commander
            FROM public.organisation_members m
            WHERE m.user_id = :user_id AND m.organisation_id = :org_id AND m.status = 'ACTIVE'
        """)
        result = await db.execute(query, {"user_id": identity.id, "org_id": requested_org_id})
        row = result.mappings().first()
        
        if not row:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You do not belong to the requested organisation or your status is inactive."
            )
    else:
        # Fallback for local dev or single-org users
        query = text("""
            SELECT 
                m.organisation_id,
                m.is_creator,
                m.is_commander
            FROM public.organisation_members m
            WHERE m.user_id = :user_id AND m.status = 'ACTIVE'
            ORDER BY m.created_at ASC
            LIMIT 1
        """)
        result = await db.execute(query, {"user_id": identity.id})
        row = result.mappings().first()
        
        if not row:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not belong to any active organisation. Onboarding required."
            )

    return AuthenticatedUser(
        id=identity.id,
        email=identity.email,
        full_name=identity.full_name,
        organisation_id=row["organisation_id"],
        is_creator=row["is_creator"],
        is_commander=row["is_commander"],
    )

async def get_current_user(user: AuthenticatedUser = Depends(get_current_active_organisation)) -> AuthenticatedUser:
    # Alias to not break legacy routes
    return user

def require_permission(permission: str) -> Callable:
    async def dependency(user: AuthenticatedUser = Depends(get_current_active_organisation)) -> AuthenticatedUser:
        if not user.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions: '{permission}' required",
            )
        return user
    return dependency

async def require_commander(user: AuthenticatedUser = Depends(get_current_active_organisation)) -> AuthenticatedUser:
    if not user.is_creator:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the Organisation Creator (Commander) can perform this action",
        )
    return user

async def get_tenant_context(
    user: AuthenticatedUser = Depends(get_current_active_organisation),
    db: AsyncSession = Depends(get_db),
) -> TenantContext:
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant infrastructure is not fully provisioned for this organisation.",
        )
        
    return TenantContext(
        organisation_id=user.organisation_id,
        tenant_database_provider=ProviderType(row["db_provider"]),
        tenant_database_identifier=row["database_identifier"],
        mongodb_cluster_identifier=row["cluster_identifier"],
        mongodb_database_name=row["mongo_db_name"],
        cloudinary_prefix=row["cloudinary_folder_prefix"] or f"zolexora/organisations/{user.organisation_id}/",
        r2_bucket=row["r2_bucket"] or "tms-documents",
        r2_prefix=row["r2_prefix"],
        user_id=user.id,
        role_code="CREATOR" if user.is_creator else "MEMBER",
        permissions=[]
    )

async def require_platform_admin(identity: AuthenticatedIdentity = Depends(get_current_identity), db: AsyncSession = Depends(get_db)) -> AuthenticatedIdentity:
    """
    Platform Admin relies ONLY on platform context, never on organization context.
    """
    query = text("""
        SELECT 1 FROM public.platform_admins WHERE user_id = :user_id AND status = 'ACTIVE'
    """)
    result = await db.execute(query, {"user_id": identity.id})
    if not result.scalar():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Platform Administrators can perform this action",
        )
    return identity
