from __future__ import annotations

from typing import Any, Optional

from app.db.d1_client import D1Client
from app.db.supabase_pg import SupabasePostgres


class ReportsRepository:
    @staticmethod
    async def get_accounts_for_companies(pg: SupabasePostgres, company_ids: list[str]) -> list[dict[str, Any]]:
        placeholders = ", ".join(f"${i + 1}" for i in range(len(company_ids)))
        return await pg.fetch_all(f"SELECT * FROM account_master WHERE company_code IN ({placeholders})", *company_ids)

    @staticmethod
    async def get_pl_groups_for_companies(pg: SupabasePostgres, company_ids: list[str]) -> list[dict[str, Any]]:
        placeholders = ", ".join(f"${i + 1}" for i in range(len(company_ids)))
        return await pg.fetch_all(f"SELECT * FROM pl_groups WHERE company_code IN ({placeholders})", *company_ids)

    @staticmethod
    async def get_ledger_sums(
        d1: D1Client, company_ids: list[str], start_date: Optional[str] = None, end_date: Optional[str] = None
    ) -> list[dict[str, Any]]:
        placeholders = ", ".join("?" for _ in company_ids)
        query = f"""
            SELECT le.account_code AS account_code,
                   COALESCE(SUM(le.debit), 0) AS total_debit,
                   COALESCE(SUM(le.credit), 0) AS total_credit
            FROM Ledger_Entries le
            JOIN Entry_Batches eb ON le.batch_id = eb.id
            WHERE eb.company_code IN ({placeholders}) AND lower(eb.status) = 'posted'
        """
        params: list[Any] = list(company_ids)
        if start_date:
            query += " AND date(eb.created_at) >= date(?)"
            params.append(start_date)
        if end_date:
            query += " AND date(eb.created_at) <= date(?)"
            params.append(end_date)
        query += " GROUP BY le.account_code"
        result = await d1.query(query, params)
        return result.rows
