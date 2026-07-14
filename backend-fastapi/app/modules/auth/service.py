from __future__ import annotations

from typing import Any

from app.core.errors import NotFoundError
from app.core.security import UserSession
from app.db.d1_client import D1Client
from app.db.supabase_pg import SupabasePostgres
from app.modules.audit.repository import AuditRepository
from app.modules.auth.repository import AuthRepository
from app.modules.companies.repository import CompaniesRepository


class AuthService:
    @staticmethod
    def me(user: UserSession) -> dict[str, Any]:
        return {
            "user": {
                "id": user.user_id, "email": user.email, "name": user.name, "role": user.role,
                "company_codes": user.company_codes, "all_company_access": user.all_company_access,
            }
        }

    @staticmethod
    async def list_users(pg: SupabasePostgres, user: UserSession) -> list[dict[str, Any]]:
        user.assert_permission("company:manage")  # Admin/FinanceAdmin scope; user management is an admin task
        profiles = await AuthRepository.list_profiles(pg)
        result = []
        for profile in profiles:
            grants = await AuthRepository.company_access_for_user(pg, profile["auth_user_id"])
            result.append({**profile, "company_codes": grants, "all_company_access": profile["role"] == "Admin"})
        return result

    @staticmethod
    async def set_role(pg: SupabasePostgres, d1: D1Client, auth_user_id: str, role: str, actor: UserSession) -> dict[str, Any]:
        if actor.role != "Admin":
            from app.core.errors import ForbiddenError

            raise ForbiddenError("Only Admin may change roles")
        updated = await AuthRepository.set_role(pg, auth_user_id, role)
        if not updated:
            raise NotFoundError("User profile not found")
        await AuditRepository.log(d1, user_email=actor.email, role=actor.role, action="SET_USER_ROLE", details={"target_user": auth_user_id, "role": role})
        return updated

    @staticmethod
    async def grant_company_access(pg: SupabasePostgres, d1: D1Client, auth_user_id: str, company_code: str, actor: UserSession) -> dict[str, Any]:
        actor.assert_permission("company:manage")
        if not await CompaniesRepository.get_by_code(pg, company_code):
            raise NotFoundError("Company not found")
        await AuthRepository.grant_company_access(pg, auth_user_id, company_code)
        await AuditRepository.log(d1, user_email=actor.email, role=actor.role, action="GRANT_COMPANY_ACCESS", details={"target_user": auth_user_id, "company_code": company_code})
        return {"granted": True, "auth_user_id": auth_user_id, "company_code": company_code}

    @staticmethod
    async def revoke_company_access(pg: SupabasePostgres, d1: D1Client, auth_user_id: str, company_code: str, actor: UserSession) -> dict[str, Any]:
        actor.assert_permission("company:manage")
        await AuthRepository.revoke_company_access(pg, auth_user_id, company_code)
        await AuditRepository.log(d1, user_email=actor.email, role=actor.role, action="REVOKE_COMPANY_ACCESS", details={"target_user": auth_user_id, "company_code": company_code})
        return {"revoked": True, "auth_user_id": auth_user_id, "company_code": company_code}
