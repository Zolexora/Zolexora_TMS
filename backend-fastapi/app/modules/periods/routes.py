from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request

from app.core.errors import ValidationError
from app.core.permissions import PERMISSIONS
from app.core.security import UserSession, get_current_user, require_permission
from app.core.validation import read_json_object
from app.db.d1_client import D1Client
from app.db.supabase_pg import SupabasePostgres
from app.deps import get_d1, get_pg
from app.modules.periods.schemas import parse_create_financial_year, parse_period_transition, parse_update_financial_year
from app.modules.periods.service import PeriodsService

router = APIRouter(tags=["periods"])


@router.post("/financial-years", status_code=201)
async def create_financial_year(
    request: Request,
    pg: SupabasePostgres = Depends(get_pg), d1: D1Client = Depends(get_d1),
    user: UserSession = Depends(require_permission(PERMISSIONS["FINANCIAL_YEAR_MANAGE"])),
):
    body = await read_json_object(request)
    return await PeriodsService.create_year(pg, d1, parse_create_financial_year(body), user)


@router.get("/financial-years")
async def list_financial_years(
    company_code: str = Query(alias="company_code"),
    pg: SupabasePostgres = Depends(get_pg), user: UserSession = Depends(get_current_user),
):
    return await PeriodsService.list_years(pg, company_code, user)


@router.get("/financial-years/{year_id}")
async def get_financial_year(year_id: str, pg: SupabasePostgres = Depends(get_pg), user: UserSession = Depends(get_current_user)):
    return await PeriodsService.get_year(pg, year_id, user)


@router.patch("/financial-years/{year_id}")
async def update_financial_year(
    year_id: str, request: Request,
    pg: SupabasePostgres = Depends(get_pg), d1: D1Client = Depends(get_d1),
    user: UserSession = Depends(require_permission(PERMISSIONS["FINANCIAL_YEAR_MANAGE"])),
):
    body = await read_json_object(request)
    return await PeriodsService.update_year(pg, d1, year_id, parse_update_financial_year(body), user)


@router.delete("/financial-years/{year_id}")
async def deactivate_financial_year(
    year_id: str,
    pg: SupabasePostgres = Depends(get_pg), d1: D1Client = Depends(get_d1),
    user: UserSession = Depends(require_permission(PERMISSIONS["FINANCIAL_YEAR_MANAGE"])),
):
    return await PeriodsService.deactivate_year(pg, d1, year_id, user)


@router.get("/periods")
async def list_periods(
    company_code: str = Query(alias="company_code"),
    financial_year_id: str | None = Query(default=None, alias="financial_year_id"),
    pg: SupabasePostgres = Depends(get_pg), user: UserSession = Depends(get_current_user),
):
    return await PeriodsService.list_periods(pg, company_code, financial_year_id, user)


@router.get("/periods/{period_id}")
async def get_period(period_id: str, pg: SupabasePostgres = Depends(get_pg), user: UserSession = Depends(get_current_user)):
    return await PeriodsService.get_period(pg, period_id, user)


def _permission_for(action: str) -> str:
    return {
        "close": PERMISSIONS["PERIOD_CLOSE"], "reopen": PERMISSIONS["PERIOD_REOPEN"],
        "lock": PERMISSIONS["PERIOD_LOCK"], "unlock": PERMISSIONS["PERIOD_UNLOCK"],
    }[action]


async def _transition(action: str, period_id: str, request: Request, pg: SupabasePostgres, d1: D1Client, user: UserSession):
    user.assert_permission(_permission_for(action))
    body = await read_json_object(request) if await request.body() else {}
    return await PeriodsService.transition(pg, d1, period_id, action, parse_period_transition(body), user)


@router.post("/periods/{period_id}/close")
async def close_period(period_id: str, request: Request, pg: SupabasePostgres = Depends(get_pg), d1: D1Client = Depends(get_d1), user: UserSession = Depends(get_current_user)):
    return await _transition("close", period_id, request, pg, d1, user)


@router.post("/periods/{period_id}/reopen")
async def reopen_period(period_id: str, request: Request, pg: SupabasePostgres = Depends(get_pg), d1: D1Client = Depends(get_d1), user: UserSession = Depends(get_current_user)):
    return await _transition("reopen", period_id, request, pg, d1, user)


@router.post("/periods/{period_id}/lock")
async def lock_period(period_id: str, request: Request, pg: SupabasePostgres = Depends(get_pg), d1: D1Client = Depends(get_d1), user: UserSession = Depends(get_current_user)):
    return await _transition("lock", period_id, request, pg, d1, user)


@router.post("/periods/{period_id}/unlock")
async def unlock_period(period_id: str, request: Request, pg: SupabasePostgres = Depends(get_pg), d1: D1Client = Depends(get_d1), user: UserSession = Depends(get_current_user)):
    return await _transition("unlock", period_id, request, pg, d1, user)
