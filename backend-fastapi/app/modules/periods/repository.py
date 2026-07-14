from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from app.db.d1_client import D1Client
from app.db.supabase_pg import SupabasePostgres

YEAR_COLUMNS = "id, company_code, name, start_date, end_date, status, is_active, created_at, updated_at"
PERIOD_COLUMNS = (
    "id, company_code, financial_year_id, month_number, period_code, status, is_active, "
    "created_at, updated_at, start_date, end_date, status_before_lock"
)


@dataclass
class NewPeriod:
    id: str
    month_number: int
    period_code: str
    start_date: str
    end_date: str


class PeriodsRepository:
    # -- Postgres: financial years / periods -----------------------------
    @staticmethod
    async def list_years(pg: SupabasePostgres, company_code: str) -> list[dict[str, Any]]:
        return await pg.fetch_all(
            f"SELECT {YEAR_COLUMNS} FROM financial_years WHERE company_code = $1 ORDER BY start_date DESC", company_code
        )

    @staticmethod
    async def get_year(pg: SupabasePostgres, year_id: str) -> Optional[dict[str, Any]]:
        return await pg.fetch_one(f"SELECT {YEAR_COLUMNS} FROM financial_years WHERE id = $1", year_id)

    @staticmethod
    async def find_overlap(
        pg: SupabasePostgres, company_code: str, start_date: str, end_date: str, exclude_id: Optional[str] = None
    ) -> Optional[dict[str, Any]]:
        return await pg.fetch_one(
            f"""
            SELECT {YEAR_COLUMNS} FROM financial_years
            WHERE company_code = $1 AND start_date <= $2 AND end_date >= $3 AND ($4::text IS NULL OR id <> $4)
            LIMIT 1
            """,
            company_code, end_date, start_date, exclude_id,
        )

    @staticmethod
    async def create_year_with_periods(pg: SupabasePostgres, year: dict[str, Any], periods: list[NewPeriod]) -> None:
        async with pg.transaction() as conn:
            await conn.execute(
                f"""
                INSERT INTO financial_years ({YEAR_COLUMNS})
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)
                """,
                year["id"], year["company_code"], year["name"], year["start_date"], year["end_date"],
                year["status"], year["is_active"], year["created_at"], year["updated_at"],
            )
            for period in periods:
                await conn.execute(
                    """
                    INSERT INTO financial_periods
                      (id, company_code, financial_year_id, month_number, period_code, status,
                       is_active, created_at, updated_at, start_date, end_date)
                    VALUES ($1, $2, $3, $4, $5, 'open', true, $6, $7, $8, $9)
                    """,
                    period.id, year["company_code"], year["id"], period.month_number, period.period_code,
                    year["created_at"], year["updated_at"], period.start_date, period.end_date,
                )

    @staticmethod
    async def update_year_with_periods(
        pg: SupabasePostgres, year: dict[str, Any], periods: Optional[list[NewPeriod]] = None
    ) -> None:
        async with pg.transaction() as conn:
            if periods is not None:
                await conn.execute("DELETE FROM financial_periods WHERE financial_year_id = $1", year["id"])
                for period in periods:
                    await conn.execute(
                        """
                        INSERT INTO financial_periods
                          (id, company_code, financial_year_id, month_number, period_code, status,
                           is_active, created_at, updated_at, start_date, end_date)
                        VALUES ($1, $2, $3, $4, $5, 'open', true, $6, $7, $8, $9)
                        """,
                        period.id, year["company_code"], year["id"], period.month_number, period.period_code,
                        year["created_at"], year["updated_at"], period.start_date, period.end_date,
                    )
            await conn.execute(
                """
                UPDATE financial_years SET name = $1, start_date = $2, end_date = $3,
                  status = $4, is_active = $5, updated_at = $6 WHERE id = $7
                """,
                year["name"], year["start_date"], year["end_date"], year["status"], year["is_active"],
                year["updated_at"], year["id"],
            )

    @staticmethod
    async def list_periods(
        pg: SupabasePostgres, company_code: str, financial_year_id: Optional[str] = None
    ) -> list[dict[str, Any]]:
        if financial_year_id:
            return await pg.fetch_all(
                f"SELECT {PERIOD_COLUMNS} FROM financial_periods WHERE company_code = $1 AND financial_year_id = $2 ORDER BY start_date",
                company_code, financial_year_id,
            )
        return await pg.fetch_all(
            f"SELECT {PERIOD_COLUMNS} FROM financial_periods WHERE company_code = $1 ORDER BY start_date", company_code
        )

    @staticmethod
    async def get_period(pg: SupabasePostgres, period_id: str) -> Optional[dict[str, Any]]:
        return await pg.fetch_one(f"SELECT {PERIOD_COLUMNS} FROM financial_periods WHERE id = $1", period_id)

    @staticmethod
    async def get_period_by_code(pg: SupabasePostgres, company_code: str, period_code: str) -> Optional[dict[str, Any]]:
        return await pg.fetch_one(
            f"SELECT {PERIOD_COLUMNS} FROM financial_periods WHERE company_code = $1 AND period_code = $2",
            company_code, period_code,
        )

    @staticmethod
    async def update_period_status(pg: SupabasePostgres, period_id: str, status: str) -> None:
        if status == "locked":
            await pg.execute(
                "UPDATE financial_periods SET status_before_lock = status, status = 'locked', updated_at = now() WHERE id = $1",
                period_id,
            )
        else:
            await pg.execute(
                "UPDATE financial_periods SET status = $1, status_before_lock = NULL, updated_at = now() WHERE id = $2",
                status, period_id,
            )

    # -- D1: batch-existence checks (transactional data) ------------------
    @staticmethod
    async def has_batches_in_range(d1: D1Client, company_code: str, start_period: str, end_period: str) -> bool:
        result = await d1.query(
            "SELECT 1 FROM Entry_Batches WHERE company_code = ? AND period BETWEEN ? AND ? LIMIT 1",
            [company_code, start_period, end_period],
        )
        return len(result.rows) > 0

    @staticmethod
    async def count_draft_batches(d1: D1Client, company_code: str, period_code: str) -> int:
        result = await d1.query(
            "SELECT COUNT(*) AS count FROM Entry_Batches WHERE company_code = ? AND period = ? AND lower(status) = 'draft'",
            [company_code, period_code],
        )
        return int(result.rows[0]["count"]) if result.rows else 0
