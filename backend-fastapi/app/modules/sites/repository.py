from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from app.db.supabase_pg import SupabasePostgres
from app.modules.sites.schemas import NestedSiteInput

COLUMNS = "id, company_code, business_unit_id, site_code, site_name, address, is_active, created_at, updated_at"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class SitesRepository:
    @staticmethod
    async def list(pg: SupabasePostgres, company_code: str) -> list[dict[str, Any]]:
        return await pg.fetch_all(
            f"SELECT {COLUMNS} FROM sites WHERE company_code = $1 ORDER BY site_name, site_code", company_code
        )

    @staticmethod
    async def get(pg: SupabasePostgres, site_id: str) -> Optional[dict[str, Any]]:
        return await pg.fetch_one(f"SELECT {COLUMNS} FROM sites WHERE id = $1", site_id)

    @staticmethod
    async def get_by_code(pg: SupabasePostgres, company_code: str, site_code: str) -> Optional[dict[str, Any]]:
        return await pg.fetch_one(
            f"SELECT {COLUMNS} FROM sites WHERE company_code = $1 AND site_code = $2", company_code, site_code
        )

    @staticmethod
    async def get_business_unit(pg: SupabasePostgres, unit_id: str) -> Optional[dict[str, Any]]:
        return await pg.fetch_one(
            "SELECT id, company_code, is_active FROM business_units WHERE id = $1", unit_id
        )

    @staticmethod
    async def ensure_primary_business_unit(pg: SupabasePostgres, company: dict[str, Any]) -> str:
        unit_id = f"bu:{company['code']}:primary"
        await pg.execute(
            """
            INSERT INTO business_units (id, company_code, code, name, business_type, is_active, created_at, updated_at)
            VALUES ($1, $2, 'PRIMARY', $3, $4, true, now(), now())
            ON CONFLICT (id) DO NOTHING
            """,
            unit_id,
            company["code"],
            f"{company['name']} Operations",
            company.get("business_type") or "General",
        )
        return unit_id

    @staticmethod
    async def create(pg: SupabasePostgres, site: dict[str, Any]) -> None:
        await pg.execute(
            f"""
            INSERT INTO sites ({COLUMNS})
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """,
            site["id"], site["company_code"], site["business_unit_id"], site["site_code"],
            site["site_name"], site["address"], site["is_active"], site["created_at"], site["updated_at"],
        )

    @staticmethod
    async def create_primary_unit_with_sites(
        pg: SupabasePostgres, company: dict[str, Any], sites: list[NestedSiteInput]
    ) -> list[dict[str, Any]]:
        if not sites:
            return []
        unit_id = f"bu:{company['code']}:primary"
        now = _now()
        rows = [
            {
                "id": f"site_{uuid.uuid4()}",
                "company_code": company["code"],
                "business_unit_id": unit_id,
                "site_code": s.site_code,
                "site_name": s.site_name,
                "address": s.address,
                "is_active": True,
                "created_at": now,
                "updated_at": now,
            }
            for s in sites
        ]
        async with pg.transaction() as conn:
            await conn.execute(
                """
                INSERT INTO business_units (id, company_code, code, name, business_type, is_active, created_at, updated_at)
                VALUES ($1, $2, 'PRIMARY', $3, $4, true, $5, $5)
                ON CONFLICT (id) DO NOTHING
                """,
                unit_id, company["code"], f"{company['name']} Operations", company.get("business_type") or "General", now,
            )
            for row in rows:
                await conn.execute(
                    f"INSERT INTO sites ({COLUMNS}) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)",
                    row["id"], row["company_code"], row["business_unit_id"], row["site_code"],
                    row["site_name"], row["address"], row["is_active"], row["created_at"], row["updated_at"],
                )
        return rows

    @staticmethod
    async def update(pg: SupabasePostgres, site: dict[str, Any]) -> None:
        await pg.execute(
            "UPDATE sites SET site_name = $1, address = $2, is_active = $3, updated_at = $4 WHERE id = $5",
            site["site_name"], site["address"], site["is_active"], site["updated_at"], site["id"],
        )
