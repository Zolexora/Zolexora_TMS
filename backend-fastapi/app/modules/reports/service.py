"""Ported from reports.service.ts, with the sign bug documented in
.agents/project_status fixed.

THE BUG (original code): each account's ledger balance was computed as a
raw `debit - credit`, with no adjustment for the account's own normal
direction, and that raw value was summed straight into totalRevenue when
the account's group was credit-normal. Revenue accounts are credit-normal,
so a healthy revenue account (credit-heavy, e.g. debit=0, credit=1000)
produced a raw balance of -1000 -- meaning genuine revenue was reported as
a large negative number, and net_profit was calculated backwards.

THE FIX: normalize each account's balance into its own natural direction
first -- `debit - credit` for debit-normal accounts (expenses, as before),
but `credit - debit` for credit-normal accounts (revenue). Every group
total, the recursive group-tree rollup, and totalRevenue/totalExpense all
consume this already-normalized value, so a group's `balance` in the
`details` array is always positive when that account/group is performing
in its expected direction, and net_profit = totalRevenue - totalExpense is
meaningful.
"""
from __future__ import annotations

from typing import Any, Optional

from app.core.errors import NotFoundError
from app.core.security import UserSession
from app.db.d1_client import D1Client
from app.db.supabase_pg import SupabasePostgres
from app.modules.companies.repository import CompaniesRepository
from app.modules.reports.repository import ReportsRepository
from app.modules.reports.schemas import PLReportQuery


def _natural_balance(account: dict[str, Any], raw_debit_minus_credit: float) -> float:
    return raw_debit_minus_credit if account["normal_direction"] == "debit" else -raw_debit_minus_credit


class ReportsService:
    @staticmethod
    async def profit_and_loss(pg: SupabasePostgres, d1: D1Client, query: PLReportQuery, user: UserSession) -> dict[str, Any]:
        for company_id in query.company_ids:
            user.assert_company_access(company_id)
            if not await CompaniesRepository.get_by_code(pg, company_id):
                raise NotFoundError("Company not found")

        accounts = await ReportsRepository.get_accounts_for_companies(pg, query.company_ids)
        ledger_sums = await ReportsRepository.get_ledger_sums(d1, query.company_ids, query.start, query.end)
        ledger_map = {row["account_code"]: (row["total_debit"], row["total_credit"]) for row in ledger_sums}

        account_balances: dict[str, float] = {}
        for account in accounts:
            debit, credit = ledger_map.get(account["code"], (0, 0))
            account_balances[account["code"]] = _natural_balance(account, debit - credit)

        groups = await ReportsRepository.get_pl_groups_for_companies(pg, query.company_ids)
        groups_by_id = {g["id"]: g for g in groups}
        children_by_parent: dict[Optional[str], list[dict[str, Any]]] = {}
        for g in groups:
            children_by_parent.setdefault(g["parent_id"], []).append(g)

        group_balances: dict[str, float] = {}

        def group_balance(group_id: str, _depth: int = 0) -> float:
            if group_id in group_balances:
                return group_balances[group_id]
            if _depth > 50:  # cycle guard; PLGroupsService already prevents cycles on write
                return 0.0
            balance = sum(
                account_balances.get(a["code"], 0) for a in accounts if a["pl_group_id"] == group_id
            )
            for child in children_by_parent.get(group_id, []):
                balance += group_balance(child["id"], _depth + 1)
            group_balances[group_id] = balance
            return balance

        for g in groups:
            group_balance(g["id"])

        total_revenue = 0.0
        total_expense = 0.0
        for account in accounts:
            if not account["pl_group_id"]:
                continue
            group = groups_by_id.get(account["pl_group_id"])
            if not group:
                continue
            depth = 0
            while group.get("parent_id") and depth < 20:
                parent = groups_by_id.get(group["parent_id"])
                if not parent:
                    break
                group = parent
                depth += 1
            balance = account_balances.get(account["code"], 0)
            if group["normal_direction"] == "credit":
                total_revenue += balance
            elif group["normal_direction"] == "debit":
                total_expense += balance

        return {
            "company_code": query.company_value,
            "company_id": query.company_value,
            "revenue": total_revenue,
            "expense": total_expense,
            "net_profit": total_revenue - total_expense,
            "details": [
                {
                    **g,
                    "type": "Revenue" if g["normal_direction"] == "credit" else "Expense",
                    "balance": group_balances.get(g["id"], 0),
                }
                for g in groups
            ],
        }
