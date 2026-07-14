from __future__ import annotations

from typing import Any, Optional

from app.db.d1_client import D1Client
from app.db.supabase_pg import SupabasePostgres

COLUMNS = "id, code, company_code, name, pl_group_id, normal_direction, display_order, is_active, created_at, updated_at"


class AccountsRepository:
    # -- Postgres: account master rows -----------------------------------
    @staticmethod
    async def get_by_id(pg: SupabasePostgres, account_id: str) -> Optional[dict[str, Any]]:
        return await pg.fetch_one(f"SELECT {COLUMNS} FROM account_master WHERE id = $1", account_id)

    @staticmethod
    async def get_by_company_and_code(pg: SupabasePostgres, company_code: str, code: str) -> Optional[dict[str, Any]]:
        return await pg.fetch_one(
            f"SELECT {COLUMNS} FROM account_master WHERE company_code = $1 AND code = $2", company_code, code
        )

    @staticmethod
    async def find_by_identifier(pg: SupabasePostgres, identifier: str) -> list[dict[str, Any]]:
        return await pg.fetch_all(
            f"SELECT {COLUMNS} FROM account_master WHERE id = $1 OR code = $1 ORDER BY company_code", identifier
        )

    @staticmethod
    async def check_duplicate(pg: SupabasePostgres, company_code: str, code: str) -> bool:
        return await AccountsRepository.get_by_company_and_code(pg, company_code, code) is not None

    @staticmethod
    async def create(pg: SupabasePostgres, account: dict[str, Any]) -> None:
        await pg.execute(
            f"""
            INSERT INTO account_master ({COLUMNS})
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
            """,
            account["id"], account["code"], account["company_code"], account["name"], account["pl_group_id"],
            account["normal_direction"], account["display_order"], account["is_active"],
            account["created_at"], account["updated_at"],
        )

    @staticmethod
    async def update(pg: SupabasePostgres, account: dict[str, Any]) -> None:
        await pg.execute(
            """
            UPDATE account_master SET name = $1, pl_group_id = $2, normal_direction = $3,
              display_order = $4, is_active = $5, updated_at = $6 WHERE id = $7
            """,
            account["name"], account["pl_group_id"], account["normal_direction"], account["display_order"],
            account["is_active"], account["updated_at"], account["id"],
        )

    @staticmethod
    async def get_all(
        pg: SupabasePostgres, company_code: Optional[str] = None, search: Optional[str] = None, active: Optional[bool] = None
    ) -> list[dict[str, Any]]:
        clauses, params = [], []
        if company_code:
            params.append(company_code)
            clauses.append(f"company_code = ${len(params)}")
        if search:
            params.append(f"%{search.lower()}%")
            clauses.append(f"(lower(code) LIKE ${len(params)} OR lower(name) LIKE ${len(params)})")
        if active is not None:
            params.append(active)
            clauses.append(f"is_active = ${len(params)}")
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        return await pg.fetch_all(
            f"SELECT {COLUMNS} FROM account_master {where} ORDER BY display_order, code, name", *params
        )

    # -- D1: posted-ledger balances (transactional data) ------------------
    @staticmethod
    async def balances_for_company(d1: D1Client, company_code: str) -> dict[str, int]:
        result = await d1.query(
            """
            SELECT le.account_code AS account_code, SUM(le.debit) - SUM(le.credit) AS balance
            FROM Ledger_Entries le
            JOIN Entry_Batches eb ON le.batch_id = eb.id
            WHERE le.company_code = ? AND lower(eb.status) = 'posted'
            GROUP BY le.account_code
            """,
            [company_code],
        )
        return {row["account_code"]: int(row["balance"] or 0) for row in result.rows}

    @staticmethod
    async def balance_for_account(d1: D1Client, company_code: str, account_code: str) -> int:
        result = await d1.query(
            """
            SELECT SUM(le.debit) - SUM(le.credit) AS balance
            FROM Ledger_Entries le
            JOIN Entry_Batches eb ON le.batch_id = eb.id
            WHERE le.account_code = ? AND le.company_code = ? AND lower(eb.status) = 'posted'
            """,
            [account_code, company_code],
        )
        if not result.rows:
            return 0
        return int(result.rows[0].get("balance") or 0)

    @staticmethod
    async def has_posted_history(d1: D1Client, company_code: str, account_code: str) -> bool:
        result = await d1.query(
            """
            SELECT 1 FROM Ledger_Entries le JOIN Entry_Batches eb ON eb.id = le.batch_id
            WHERE le.company_code = ? AND le.account_code = ? AND lower(eb.status) = 'posted' LIMIT 1
            """,
            [company_code, account_code],
        )
        return len(result.rows) > 0

    @staticmethod
    async def get_all_with_balance(
        pg: SupabasePostgres, d1: D1Client, company_code: Optional[str] = None,
        search: Optional[str] = None, active: Optional[bool] = None,
    ) -> list[dict[str, Any]]:
        accounts = await AccountsRepository.get_all(pg, company_code, search, active)
        if not accounts:
            return []
        # One balance lookup per distinct company represented in the result set.
        companies = {a["company_code"] for a in accounts}
        balance_maps = {code: await AccountsRepository.balances_for_company(d1, code) for code in companies}
        return [{**a, "balance": balance_maps[a["company_code"]].get(a["code"], 0)} for a in accounts]

    @staticmethod
    async def get_with_balance(pg: SupabasePostgres, d1: D1Client, account_id: str) -> Optional[dict[str, Any]]:
        account = await AccountsRepository.get_by_id(pg, account_id)
        if not account:
            return None
        balance = await AccountsRepository.balance_for_account(d1, account["company_code"], account["code"])
        return {**account, "balance": balance}

    # -- D1: opening-balance batch/entry (written at account create/edit time) --
    @staticmethod
    async def insert_initial_balance_batch(d1: D1Client, batch_id: str, company_code: str, period: str) -> None:
        await d1.query(
            """
            INSERT OR IGNORE INTO Entry_Batches
              (id, company_code, period, status, batch_type, created_at, updated_at)
            VALUES (?, ?, ?, 'posted', 'standard', datetime('now'), datetime('now'))
            """,
            [batch_id, company_code, period],
        )

    @staticmethod
    async def insert_ledger_entry(
        d1: D1Client, entry_id: str, batch_id: str, company_code: str, account_code: str, debit: int, credit: int
    ) -> None:
        await d1.query(
            """
            INSERT INTO Ledger_Entries (id, batch_id, company_code, account_code, debit, credit, description)
            VALUES (?, ?, ?, ?, ?, ?, 'Initial Balance')
            """,
            [entry_id, batch_id, company_code, account_code, debit, credit],
        )
