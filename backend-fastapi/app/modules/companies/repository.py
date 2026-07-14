from __future__ import annotations

from typing import Any, Optional

from app.db.supabase_pg import SupabasePostgres

COLUMNS = (
    "code, name, currency, fiscal_year_start, legal_name, business_type, gst_number, "
    "pan_number, registered_address, logo_object_key, is_active, created_at, updated_at"
)


class CompaniesRepository:
    @staticmethod
    async def get_by_code(pg: SupabasePostgres, code: str) -> Optional[dict[str, Any]]:
        return await pg.fetch_one(f"SELECT {COLUMNS} FROM companies WHERE code = $1", code)

    @staticmethod
    async def exists(pg: SupabasePostgres, code: str) -> bool:
        return await pg.fetch_val("SELECT 1 FROM companies WHERE code = $1", code) is not None

    @staticmethod
    async def create(pg: SupabasePostgres, company: dict[str, Any]) -> None:
        await pg.execute(
            f"""
            INSERT INTO companies ({COLUMNS})
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)
            """,
            company["code"], company["name"], company["currency"], company["fiscal_year_start"],
            company["legal_name"], company["business_type"], company["gst_number"], company["pan_number"],
            company["registered_address"], company["logo_object_key"], company["is_active"],
            company["created_at"], company["updated_at"],
        )

    @staticmethod
    async def get_all(pg: SupabasePostgres) -> list[dict[str, Any]]:
        return await pg.fetch_all(f"SELECT {COLUMNS} FROM companies ORDER BY code")

    @staticmethod
    async def update(pg: SupabasePostgres, code: str, company: dict[str, Any]) -> None:
        await pg.execute(
            """
            UPDATE companies SET name = $1, currency = $2, fiscal_year_start = $3, legal_name = $4,
              business_type = $5, gst_number = $6, pan_number = $7, registered_address = $8,
              logo_object_key = $9, is_active = $10, updated_at = $11
            WHERE code = $12
            """,
            company["name"], company["currency"], company["fiscal_year_start"], company["legal_name"],
            company["business_type"], company["gst_number"], company["pan_number"], company["registered_address"],
            company["logo_object_key"], company["is_active"], company["updated_at"], code,
        )
