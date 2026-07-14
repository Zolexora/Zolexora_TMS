from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from app.core.errors import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.core.security import UserSession
from app.db.d1_client import D1Client
from app.db.supabase_pg import SupabasePostgres
from app.modules.accounts.repository import AccountsRepository
from app.modules.accounts.schemas import CreateAccountInput, UpdateAccountInput
from app.modules.audit.repository import AuditRepository
from app.modules.companies.repository import CompaniesRepository
from app.modules.periods.service import PeriodsService
from app.modules.pnl_groups.repository import PLGroupsRepository


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _current_period() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def present(account: dict[str, Any]) -> dict[str, Any]:
    return {**account, "company_id": account["company_code"]}


async def _validate_group(pg: SupabasePostgres, company_code: str, group_id: Optional[str]) -> Optional[dict[str, Any]]:
    if not group_id:
        return None
    group = await PLGroupsRepository.get_by_id(pg, group_id)
    if not group:
        raise ValidationError("P&L group does not exist", [{"field": "pl_group_id", "message": "Unknown P&L group"}])
    if group["company_code"] != company_code:
        raise ValidationError("P&L group belongs to another company")
    if not group["is_active"]:
        raise ValidationError("P&L group is inactive")
    return group


async def _audit(d1: D1Client, user: UserSession, action: str, account: dict, before: Optional[dict] = None) -> None:
    details = {"company_code": account["company_code"], "account_id": account["id"], "after": present(account)}
    if before:
        details["before"] = present(before)
    await AuditRepository.log(d1, user_email=user.email, role=user.role, action=action, details=details)


async def _write_opening_balance(d1: D1Client, company_code: str, code: str, balance: int) -> None:
    period = _current_period()
    batch_id = f"init-batch-{company_code}-{period}"
    await AccountsRepository.insert_initial_balance_batch(d1, batch_id, company_code, period)
    await AccountsRepository.insert_ledger_entry(
        d1, f"entry-{uuid.uuid4()}", batch_id, company_code, code,
        balance if balance > 0 else 0, -balance if balance < 0 else 0,
    )


class AccountsService:
    @staticmethod
    async def create(pg: SupabasePostgres, d1: D1Client, input: CreateAccountInput, user: UserSession) -> dict[str, Any]:
        user.assert_company_access(input.company_code)
        company = await CompaniesRepository.get_by_code(pg, input.company_code)
        if not company:
            raise ValidationError("Company does not exist")
        if not company["is_active"]:
            raise ConflictError("Cannot create an account for an inactive company")
        if await AccountsRepository.check_duplicate(pg, input.company_code, input.code):
            raise ConflictError("Account code already exists in this company")
        group = await _validate_group(pg, input.company_code, input.pl_group_id)
        if input.balance:
            await PeriodsService.assert_open_period(pg, input.company_code, _current_period())

        now = _now()
        account = {
            "id": f"acct_{uuid.uuid4()}", "code": input.code, "company_code": input.company_code, "name": input.name,
            "pl_group_id": input.pl_group_id,
            "normal_direction": input.normal_direction or (group["normal_direction"] if group else "debit"),
            "display_order": input.display_order, "is_active": True, "created_at": now, "updated_at": now,
        }
        await AccountsRepository.create(pg, account)
        if input.balance:
            await _write_opening_balance(d1, input.company_code, input.code, input.balance)
        await _audit(d1, user, "CREATE_ACCOUNT", account)
        return {**present(account), "balance": input.balance or 0}

    @staticmethod
    async def list(
        pg: SupabasePostgres, d1: D1Client, user: UserSession,
        company_code: Optional[str] = None, search: Optional[str] = None, active: Optional[bool] = None,
    ) -> list[dict[str, Any]]:
        if company_code:
            user.assert_company_access(company_code)
        accounts = await AccountsRepository.get_all_with_balance(pg, d1, company_code, search, active)
        return [present(a) for a in accounts if user.has_company_access(a["company_code"])]

    @staticmethod
    async def resolve(pg: SupabasePostgres, identifier: str, user: UserSession, company_code: Optional[str] = None) -> dict[str, Any]:
        if company_code:
            user.assert_company_access(company_code)
            exact = await AccountsRepository.get_by_id(pg, identifier) or await AccountsRepository.get_by_company_and_code(pg, company_code, identifier)
            if not exact or exact["company_code"] != company_code:
                raise NotFoundError("Account not found")
            return exact
        matches = await AccountsRepository.find_by_identifier(pg, identifier)
        accessible = [a for a in matches if user.has_company_access(a["company_code"])]
        if matches and not accessible:
            raise ForbiddenError("You do not have access to this company")
        if not accessible:
            raise NotFoundError("Account not found")
        if len(accessible) > 1:
            raise ConflictError("company_code is required because this account code exists in multiple companies")
        return accessible[0]

    @staticmethod
    async def get(pg: SupabasePostgres, d1: D1Client, identifier: str, user: UserSession, company_code: Optional[str] = None) -> dict[str, Any]:
        account = await AccountsService.resolve(pg, identifier, user, company_code)
        return present(await AccountsRepository.get_with_balance(pg, d1, account["id"]))  # type: ignore[arg-type]

    @staticmethod
    async def lookup(pg: SupabasePostgres, company_code: str, code: str, user: UserSession) -> dict[str, Any]:
        user.assert_company_access(company_code)
        account = await AccountsRepository.get_by_company_and_code(pg, company_code, code)
        if not account or not account["is_active"]:
            raise NotFoundError("Active account not found")
        return present(account)

    @staticmethod
    async def update(
        pg: SupabasePostgres, d1: D1Client, identifier: str, input: UpdateAccountInput, user: UserSession,
        company_code: Optional[str] = None,
    ) -> dict[str, Any]:
        current = await AccountsService.resolve(pg, identifier, user, company_code)
        if input.code is not None and input.code != current["code"]:
            raise ConflictError("Account code is immutable; create a new account instead")
        group_id = input.pl_group_id if input.pl_group_id_set else current["pl_group_id"]
        group = await _validate_group(pg, current["company_code"], group_id)

        if input.balance_set:
            if await AccountsRepository.has_posted_history(d1, current["company_code"], current["code"]):
                raise ConflictError("Posted account history is immutable; use a reversal or adjustment")
            if input.balance:
                await PeriodsService.assert_open_period(pg, current["company_code"], _current_period())

        updated = {
            **current, "name": input.name or current["name"], "pl_group_id": group_id,
            "normal_direction": input.normal_direction or (group["normal_direction"] if group else current["normal_direction"]),
            "display_order": input.display_order if input.display_order is not None else current["display_order"],
            "is_active": current["is_active"] if input.is_active is None else input.is_active,
            "updated_at": _now(),
        }
        await AccountsRepository.update(pg, updated)
        if input.balance:
            await _write_opening_balance(d1, current["company_code"], current["code"], input.balance)
        await _audit(d1, user, "UPDATE_ACCOUNT", updated, current)
        return present(await AccountsRepository.get_with_balance(pg, d1, updated["id"]))  # type: ignore[arg-type]

    @staticmethod
    async def deactivate(pg: SupabasePostgres, d1: D1Client, identifier: str, user: UserSession, company_code: Optional[str] = None) -> dict[str, Any]:
        return await AccountsService.update(pg, d1, identifier, UpdateAccountInput(is_active=False), user, company_code)
