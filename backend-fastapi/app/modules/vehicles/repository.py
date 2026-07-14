from __future__ import annotations
from typing import Any, Optional
from app.db.supabase_pg import SupabasePostgres

# NOTE: matching the original backend exactly -- vehicles has no exposed
# routes/service; it exists purely as a lookup used internally by the
# entries module (dimension resolution for transport-type batches).
COLUMNS = (
    "id, company_code, registration_number, ownership_id, vehicle_model_id, vehicle_type, "
    "allocated_site_id, default_manager_id, is_emi_applicable, is_active, created_at, updated_at"
)


class VehiclesRepository:
    @staticmethod
    async def get_by_id(pg: SupabasePostgres, vehicle_id: str) -> Optional[dict[str, Any]]:
        return await pg.fetch_one(f"SELECT {COLUMNS} FROM vehicles WHERE id = $1", vehicle_id)

    @staticmethod
    async def get_by_company_and_registration(pg: SupabasePostgres, company_code: str, registration_number: str) -> Optional[dict[str, Any]]:
        return await pg.fetch_one(
            f"SELECT {COLUMNS} FROM vehicles WHERE company_code = $1 AND registration_number = $2",
            company_code, registration_number,
        )
