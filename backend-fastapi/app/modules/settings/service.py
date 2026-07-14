from __future__ import annotations
from typing import Any
from app.core.errors import NotFoundError
from app.core.security import UserSession
from app.db.d1_client import D1Client
from app.db.supabase_pg import SupabasePostgres
from app.modules.companies.repository import CompaniesRepository
from app.modules.periods.repository import PeriodsRepository
from app.modules.periods.schemas import PeriodTransitionInput
from app.modules.periods.service import PeriodsService
from app.modules.settings.schemas import PeriodLockInput


class SettingsService:
    @staticmethod
    async def list_locks(pg: SupabasePostgres, company_code: str, user: UserSession) -> dict[str, Any]:
        user.assert_company_access(company_code)
        if not await CompaniesRepository.get_by_code(pg, company_code):
            raise NotFoundError("Company not found")
        locks = {}
        for period in await PeriodsRepository.list_periods(pg, company_code):
            locks[period["period_code"]] = period["status"] == "locked"
        return {"company_code": company_code, "company_id": company_code, "locks": locks}

    @staticmethod
    async def set_lock(pg: SupabasePostgres, d1: D1Client, input: PeriodLockInput, user: UserSession) -> dict[str, Any]:
        user.assert_company_access(input.company_code)
        period = await PeriodsRepository.get_period_by_code(pg, input.company_code, input.period)
        if not period:
            raise NotFoundError("Financial period not found")
        updated = await PeriodsService.transition(
            pg, d1, period["id"], "lock" if input.lock else "unlock",
            PeriodTransitionInput(reason="Compatibility settings route"), user,
        )
        return {
            "success": True, "company_code": input.company_code, "company_id": input.company_code,
            "period": input.period, "locked": updated["status"] == "locked",
        }
