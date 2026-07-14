from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Any, Optional

from app.core.errors import AppError, ConflictError, NotFoundError, ValidationError
from app.core.security import UserSession
from app.db.d1_client import D1Client
from app.db.supabase_pg import SupabasePostgres
from app.modules.audit.repository import AuditRepository
from app.modules.companies.repository import CompaniesRepository
from app.modules.periods.repository import NewPeriod, PeriodsRepository
from app.modules.periods.schemas import CreateFinancialYearInput, PeriodTransitionInput, UpdateFinancialYearInput

_ALLOWED_TRANSITIONS = {
    "close": ["open"], "reopen": ["closed"], "lock": ["open", "closed"], "unlock": ["locked"],
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _iso(d: date) -> str:
    return d.isoformat()


def _validate_year_range(start_date: str, end_date: str) -> None:
    start = date.fromisoformat(start_date)
    if start.day != 1:
        raise ValidationError(
            "Financial year must start on the first day of a month", [{"field": "start_date", "message": "Day must be 01"}]
        )
    end_year = start.year + 1
    next_month_first = date(end_year, start.month, 1)
    expected_end = date.fromordinal(next_month_first.toordinal() - 1)
    if _iso(expected_end) != end_date:
        raise ValidationError(
            "Financial year must span exactly twelve calendar months",
            [{"field": "end_date", "message": f"Expected {_iso(expected_end)} for this start date"}],
        )


def _add_months(d: date, months: int) -> date:
    month0 = d.month - 1 + months
    year = d.year + month0 // 12
    month = month0 % 12 + 1
    return date(year, month, 1)


def _generate_periods(year_id: str, start_date: str) -> list[NewPeriod]:
    start = date.fromisoformat(start_date)
    periods = []
    for index in range(12):
        period_start = _add_months(start, index)
        period_end = date.fromordinal(_add_months(start, index + 1).toordinal() - 1)
        period_code = _iso(period_start)[:7]
        periods.append(
            NewPeriod(
                id=f"fp_{year_id}_{period_code}", month_number=period_start.month,
                period_code=period_code, start_date=_iso(period_start), end_date=_iso(period_end),
            )
        )
    return periods


def present_year(year: dict[str, Any]) -> dict[str, Any]:
    return {**year}


def present_period(period: dict[str, Any]) -> dict[str, Any]:
    return {**period}


async def _audit(d1: D1Client, user: UserSession, action: str, company_code: str, details: dict[str, Any]) -> None:
    await AuditRepository.log(d1, user_email=user.email, role=user.role, action=action, details={"company_code": company_code, **details})


class PeriodsService:
    @staticmethod
    async def create_year(pg: SupabasePostgres, d1: D1Client, input: CreateFinancialYearInput, user: UserSession) -> dict[str, Any]:
        user.assert_company_access(input.company_code)
        company = await CompaniesRepository.get_by_code(pg, input.company_code)
        if not company:
            raise NotFoundError("Company not found")
        if not company["is_active"]:
            raise ConflictError("Cannot create a financial year for an inactive company")
        _validate_year_range(input.start_date, input.end_date)
        if await PeriodsRepository.find_overlap(pg, input.company_code, input.start_date, input.end_date):
            raise ConflictError("Financial year dates overlap an existing year")

        now = _now()
        year_id = f"fy_{uuid.uuid4()}"
        year = {
            "id": year_id, "company_code": input.company_code, "name": input.name,
            "start_date": input.start_date, "end_date": input.end_date, "status": "active",
            "is_active": True, "created_at": now, "updated_at": now,
        }
        try:
            await PeriodsRepository.create_year_with_periods(pg, year, _generate_periods(year_id, input.start_date))
        except Exception as exc:
            raise ConflictError("Financial year name or generated period already exists") from exc

        await _audit(d1, user, "CREATE_FINANCIAL_YEAR", input.company_code, {"financial_year_id": year_id, "after": present_year(year)})
        periods = await PeriodsRepository.list_periods(pg, input.company_code, year_id)
        return {**present_year(year), "periods": [present_period(p) for p in periods]}

    @staticmethod
    async def list_years(pg: SupabasePostgres, company_code: str, user: UserSession) -> list[dict[str, Any]]:
        user.assert_company_access(company_code)
        return [present_year(y) for y in await PeriodsRepository.list_years(pg, company_code)]

    @staticmethod
    async def get_year(pg: SupabasePostgres, year_id: str, user: UserSession) -> dict[str, Any]:
        year = await PeriodsRepository.get_year(pg, year_id)
        if not year:
            raise NotFoundError("Financial year not found")
        user.assert_company_access(year["company_code"])
        periods = await PeriodsRepository.list_periods(pg, year["company_code"], year_id)
        return {**present_year(year), "periods": [present_period(p) for p in periods]}

    @staticmethod
    async def update_year(
        pg: SupabasePostgres, d1: D1Client, year_id: str, input: UpdateFinancialYearInput, user: UserSession
    ) -> dict[str, Any]:
        current = await PeriodsRepository.get_year(pg, year_id)
        if not current:
            raise NotFoundError("Financial year not found")
        user.assert_company_access(current["company_code"])
        start_date = input.start_date or current["start_date"]
        end_date = input.end_date or current["end_date"]
        _validate_year_range(start_date, end_date)
        if await PeriodsRepository.find_overlap(pg, current["company_code"], start_date, end_date, year_id):
            raise ConflictError("Financial year dates overlap an existing year")

        boundaries_changed = start_date != current["start_date"] or end_date != current["end_date"]
        if boundaries_changed and await PeriodsRepository.has_batches_in_range(
            d1, current["company_code"], current["start_date"][:7], current["end_date"][:7]
        ):
            raise ConflictError("Financial year dates cannot change after entry batches exist")

        updated = {
            **current, "name": input.name or current["name"], "start_date": start_date, "end_date": end_date,
            "is_active": current["is_active"] if input.is_active is None else input.is_active,
            "updated_at": _now(),
        }
        await PeriodsRepository.update_year_with_periods(
            pg, updated, _generate_periods(year_id, start_date) if boundaries_changed else None
        )
        await _audit(d1, user, "UPDATE_FINANCIAL_YEAR", current["company_code"], {
            "financial_year_id": year_id, "before": present_year(current), "after": present_year(updated),
        })
        return present_year(updated)

    @staticmethod
    async def deactivate_year(pg: SupabasePostgres, d1: D1Client, year_id: str, user: UserSession) -> dict[str, Any]:
        return await PeriodsService.update_year(pg, d1, year_id, UpdateFinancialYearInput(is_active=False), user)

    @staticmethod
    async def list_periods(
        pg: SupabasePostgres, company_code: str, financial_year_id: Optional[str], user: UserSession
    ) -> list[dict[str, Any]]:
        user.assert_company_access(company_code)
        if financial_year_id:
            year = await PeriodsRepository.get_year(pg, financial_year_id)
            if not year or year["company_code"] != company_code:
                raise NotFoundError("Financial year not found for company")
        return [present_period(p) for p in await PeriodsRepository.list_periods(pg, company_code, financial_year_id)]

    @staticmethod
    async def get_period(pg: SupabasePostgres, period_id: str, user: UserSession) -> dict[str, Any]:
        period = await PeriodsRepository.get_period(pg, period_id)
        if not period:
            raise NotFoundError("Financial period not found")
        user.assert_company_access(period["company_code"])
        return present_period(period)

    @staticmethod
    async def transition(
        pg: SupabasePostgres, d1: D1Client, period_id: str, action: str, input: PeriodTransitionInput, user: UserSession
    ) -> dict[str, Any]:
        period = await PeriodsRepository.get_period(pg, period_id)
        if not period:
            raise NotFoundError("Financial period not found")
        user.assert_company_access(period["company_code"])

        targets = {
            "close": "closed", "reopen": "open", "lock": "locked",
            "unlock": period.get("status_before_lock") or "closed",
        }
        if period["status"] not in _ALLOWED_TRANSITIONS[action]:
            raise ConflictError(f"Cannot {action} a period currently {period['status']}")
        if action == "close" and await PeriodsRepository.count_draft_batches(d1, period["company_code"], period["period_code"]) > 0:
            raise ConflictError("Cannot close a period with draft entry batches")

        target = targets[action]
        await PeriodsRepository.update_period_status(pg, period_id, target)
        await _audit(d1, user, f"PERIOD_{action.upper()}", period["company_code"], {
            "financial_period_id": period_id, "period_code": period["period_code"],
            "before_status": period["status"], "after_status": target, "reason": input.reason,
        })
        return {**present_period(period), "status": target, "updated_at": _now()}

    @staticmethod
    async def assert_open_period(pg: SupabasePostgres, company_code: str, period_code: str) -> dict[str, Any]:
        company = await CompaniesRepository.get_by_code(pg, company_code)
        if not company:
            raise NotFoundError("Company not found")
        if not company["is_active"]:
            raise AppError(400, "Company is inactive", "Inactive companies cannot receive financial writes", "COMPANY_INACTIVE")
        period = await PeriodsRepository.get_period_by_code(pg, company_code, period_code)
        if not period or not period["is_active"]:
            raise AppError(400, "Financial period not found", "An active financial period is required", "PERIOD_NOT_FOUND")
        year = await PeriodsRepository.get_year(pg, period["financial_year_id"])
        if not year or not year["is_active"]:
            raise AppError(400, "Financial year is inactive", "An active financial year is required", "FINANCIAL_YEAR_INACTIVE")
        if period["status"] == "closed":
            raise AppError(400, "Period is closed", "Period is closed", "PERIOD_CLOSED")
        if period["status"] == "locked":
            raise AppError(400, "Period is locked", "Period is locked", "PERIOD_LOCKED")
        return period
