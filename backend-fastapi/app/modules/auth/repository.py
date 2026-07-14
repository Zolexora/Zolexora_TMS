from __future__ import annotations

import uuid
from typing import Any, Optional

from app.db.supabase_pg import SupabasePostgres


class AuthRepository:
    @staticmethod
    async def grant_company_access(pg: SupabasePostgres, auth_user_id: str, company_code: str) -> None:
        await pg.execute(
            """
            INSERT INTO user_company_access (id, auth_user_id, company_code, is_active, created_at, updated_at)
            VALUES ($1, $2, $3, true, now(), now())
            ON CONFLICT (auth_user_id, company_code) DO UPDATE SET is_active = true, updated_at = now()
            """,
            f"uca_{uuid.uuid4()}", auth_user_id, company_code,
        )

    @staticmethod
    async def revoke_company_access(pg: SupabasePostgres, auth_user_id: str, company_code: str) -> None:
        await pg.execute(
            "UPDATE user_company_access SET is_active = false, updated_at = now() "
            "WHERE auth_user_id = $1 AND company_code = $2",
            auth_user_id, company_code,
        )

    @staticmethod
    async def list_profiles(pg: SupabasePostgres) -> list[dict[str, Any]]:
        return await pg.fetch_all(
            "SELECT auth_user_id, email, full_name, role, created_at FROM user_profiles ORDER BY email"
        )

    @staticmethod
    async def set_role(pg: SupabasePostgres, auth_user_id: str, role: str) -> Optional[dict[str, Any]]:
        return await pg.fetch_one(
            "UPDATE user_profiles SET role = $1 WHERE auth_user_id = $2 "
            "RETURNING auth_user_id, email, full_name, role",
            role, auth_user_id,
        )

    @staticmethod
    async def company_access_for_user(pg: SupabasePostgres, auth_user_id: str) -> list[str]:
        rows = await pg.fetch_all(
            "SELECT company_code FROM user_company_access WHERE auth_user_id = $1 AND is_active = true ORDER BY company_code",
            auth_user_id,
        )
        return [r["company_code"] for r in rows]
