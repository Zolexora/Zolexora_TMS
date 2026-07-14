from __future__ import annotations
from fastapi import APIRouter, Depends, Query, Request
from app.core.permissions import PERMISSIONS
from app.core.security import UserSession, get_current_user, require_permission
from app.core.validation import read_json_object
from app.db.d1_client import D1Client
from app.db.supabase_pg import SupabasePostgres
from app.deps import get_d1, get_pg
from app.modules.settings.schemas import parse_company_query, parse_period_lock
from app.modules.settings.service import SettingsService

router = APIRouter(tags=["settings"])


@router.get("/settings/locks")
async def list_locks(
    company_code: str | None = Query(default=None, alias="company_code"),
    company_id: str | None = Query(default=None, alias="company_id"),
    pg: SupabasePostgres = Depends(get_pg), user: UserSession = Depends(get_current_user),
):
    code = parse_company_query(company_code or company_id)
    return await SettingsService.list_locks(pg, code, user)


@router.post("/settings/lock")
async def set_lock(
    request: Request,
    pg: SupabasePostgres = Depends(get_pg), d1: D1Client = Depends(get_d1),
    user: UserSession = Depends(require_permission(PERMISSIONS["PERIOD_LOCK"])),
):
    body = await read_json_object(request)
    return await SettingsService.set_lock(pg, d1, parse_period_lock(body), user)
