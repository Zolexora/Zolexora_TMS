from __future__ import annotations

from typing import Any, Optional

from app.db.supabase_pg import SupabasePostgres

COLUMNS = (
    "id, company_code, code, name, group_type, parent_id, display_order, "
    "normal_direction, is_system, is_active, created_at, updated_at"
)

# (id_suffix, code, name, group_type, display_order, normal_direction)
DEFAULTS = [
    ("income", "INCOME", "Operating Income", "income", 10, "credit"),
    ("direct-expense", "DIRECT_EXPENSE", "Direct Expenses", "direct_expense", 20, "debit"),
    ("indirect-expense", "INDIRECT_EXPENSE", "Indirect Expenses", "indirect_expense", 30, "debit"),
    ("other-income", "OTHER_INCOME", "Other Income", "other_income", 40, "credit"),
    ("finance-cost", "FINANCE_COST", "Finance Cost", "finance_cost", 50, "debit"),
    ("depreciation", "DEPRECIATION", "Depreciation", "depreciation", 60, "debit"),
    ("tax", "TAX", "Tax Expense", "tax", 70, "debit"),
]


class PLGroupsRepository:
    @staticmethod
    async def get_by_id(pg: SupabasePostgres, group_id: str) -> Optional[dict[str, Any]]:
        return await pg.fetch_one(f"SELECT {COLUMNS} FROM pl_groups WHERE id = $1", group_id)

    @staticmethod
    async def get_by_company_and_code(pg: SupabasePostgres, company_code: str, code: str) -> Optional[dict[str, Any]]:
        return await pg.fetch_one(
            f"SELECT {COLUMNS} FROM pl_groups WHERE company_code = $1 AND code = $2", company_code, code
        )

    @staticmethod
    async def get_parent_id(pg: SupabasePostgres, group_id: str) -> Optional[str]:
        row = await PLGroupsRepository.get_by_id(pg, group_id)
        return row["parent_id"] if row else None

    @staticmethod
    async def create(pg: SupabasePostgres, group: dict[str, Any]) -> None:
        await pg.execute(
            f"INSERT INTO pl_groups ({COLUMNS}) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)",
            group["id"], group["company_code"], group["code"], group["name"], group["group_type"],
            group["parent_id"], group["display_order"], group["normal_direction"], group["is_system"],
            group["is_active"], group["created_at"], group["updated_at"],
        )

    @staticmethod
    async def get_all(pg: SupabasePostgres, company_code: Optional[str] = None) -> list[dict[str, Any]]:
        if company_code:
            return await pg.fetch_all(
                f"SELECT {COLUMNS} FROM pl_groups WHERE company_code = $1 ORDER BY display_order, name, id",
                company_code,
            )
        return await pg.fetch_all(f"SELECT {COLUMNS} FROM pl_groups ORDER BY company_code, display_order, name, id")

    @staticmethod
    async def update(pg: SupabasePostgres, group: dict[str, Any]) -> None:
        await pg.execute(
            """
            UPDATE pl_groups SET code = $1, name = $2, group_type = $3, parent_id = $4,
              display_order = $5, normal_direction = $6, is_active = $7, updated_at = $8
            WHERE id = $9
            """,
            group["code"], group["name"], group["group_type"], group["parent_id"], group["display_order"],
            group["normal_direction"], group["is_active"], group["updated_at"], group["id"],
        )

    @staticmethod
    async def account_count(pg: SupabasePostgres, group_id: str) -> int:
        return await pg.fetch_val("SELECT COUNT(*) FROM account_master WHERE pl_group_id = $1", group_id)

    @staticmethod
    async def seed_defaults(pg: SupabasePostgres, company_code: str) -> None:
        async with pg.transaction() as conn:
            for suffix, code, name, group_type, order, direction in DEFAULTS:
                await conn.execute(
                    """
                    INSERT INTO pl_groups
                      (id, company_code, code, name, group_type, parent_id, display_order, normal_direction,
                       is_system, is_active, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, NULL, $6, $7, true, true, now(), now())
                    ON CONFLICT (id) DO NOTHING
                    """,
                    f"plg:{company_code}:{suffix}", company_code, code, name, group_type, order, direction,
                )
