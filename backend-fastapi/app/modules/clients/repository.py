from __future__ import annotations
from typing import Any, Optional
from app.db.supabase_pg import SupabasePostgres

COLUMNS = "id, company_code, client_code, client_name, is_active, created_at, updated_at"


class ClientsRepository:
    @staticmethod
    async def list(pg: SupabasePostgres, company_code: str) -> list[dict[str, Any]]:
        return await pg.fetch_all(
            f"SELECT {COLUMNS} FROM clients WHERE company_code = $1 ORDER BY client_name, client_code", company_code
        )

    @staticmethod
    async def get_by_id(pg: SupabasePostgres, client_id: str) -> Optional[dict[str, Any]]:
        return await pg.fetch_one(f"SELECT {COLUMNS} FROM clients WHERE id = $1", client_id)

    @staticmethod
    async def get_by_company_and_code(pg: SupabasePostgres, company_code: str, client_code: str) -> Optional[dict[str, Any]]:
        return await pg.fetch_one(
            f"SELECT {COLUMNS} FROM clients WHERE company_code = $1 AND client_code = $2", company_code, client_code
        )
