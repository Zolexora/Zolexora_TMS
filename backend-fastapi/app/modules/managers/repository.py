from __future__ import annotations
from typing import Any, Optional
from app.db.supabase_pg import SupabasePostgres

# NOTE: matching the original backend exactly -- managers has no exposed
# routes/service; it exists purely as a lookup used internally by the
# entries module (dimension resolution for transport-type batches).
COLUMNS = "id, company_code, manager_code, manager_name, is_active, created_at, updated_at"


class ManagersRepository:
    @staticmethod
    async def get_by_id(pg: SupabasePostgres, manager_id: str) -> Optional[dict[str, Any]]:
        return await pg.fetch_one(f"SELECT {COLUMNS} FROM managers WHERE id = $1", manager_id)

    @staticmethod
    async def get_by_company_and_code(pg: SupabasePostgres, company_code: str, manager_code: str) -> Optional[dict[str, Any]]:
        return await pg.fetch_one(
            f"SELECT {COLUMNS} FROM managers WHERE company_code = $1 AND manager_code = $2", company_code, manager_code
        )
