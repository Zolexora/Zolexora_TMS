from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query, Request

from app.core.errors import ValidationError
from app.core.permissions import PERMISSIONS
from app.core.security import UserSession, get_current_user, require_permission
from app.core.validation import read_json_object
from app.db.d1_client import D1Client
from app.db.supabase_pg import SupabasePostgres
from app.deps import get_d1, get_pg
from app.modules.accounts.schemas import parse_create_account, parse_update_account
from app.modules.accounts.service import AccountsService

router = APIRouter(tags=["accounts"])


@router.post("/accounts", status_code=201)
async def create_account(
    request: Request,
    pg: SupabasePostgres = Depends(get_pg), d1: D1Client = Depends(get_d1),
    user: UserSession = Depends(require_permission(PERMISSIONS["ACCOUNT_MANAGE"])),
):
    body = await read_json_object(request)
    return await AccountsService.create(pg, d1, parse_create_account(body), user)


@router.get("/accounts")
async def list_accounts(
    company_code: Optional[str] = Query(default=None, alias="company_code"),
    company_id: Optional[str] = Query(default=None, alias="company_id"),
    company: Optional[str] = Query(default=None, alias="company"),
    search: Optional[str] = Query(default=None),
    is_active: Optional[str] = Query(default=None, alias="is_active"),
    pg: SupabasePostgres = Depends(get_pg), d1: D1Client = Depends(get_d1),
    user: UserSession = Depends(get_current_user),
):
    if is_active is not None and is_active not in ("all", "true", "false", "1", "0"):
        raise ValidationError("is_active must be true, false, 1, 0, or all")
    active = None if is_active in (None, "all") else is_active in ("true", "1")
    code = company_code or company_id or company
    return await AccountsService.list(pg, d1, user, code, search.strip() if search else None, active)


@router.get("/accounts/lookup")
async def lookup_account(
    company_code: Optional[str] = Query(default=None, alias="company_code"),
    company_id: Optional[str] = Query(default=None, alias="company_id"),
    code: Optional[str] = Query(default=None),
    pg: SupabasePostgres = Depends(get_pg), user: UserSession = Depends(get_current_user),
):
    resolved_company = company_code or company_id
    if not resolved_company or not code:
        raise ValidationError("company_code and code are required")
    return await AccountsService.lookup(pg, resolved_company, code, user)


@router.get("/accounts/{account_id}")
async def get_account(
    account_id: str,
    company_code: Optional[str] = Query(default=None, alias="company_code"),
    pg: SupabasePostgres = Depends(get_pg), d1: D1Client = Depends(get_d1),
    user: UserSession = Depends(get_current_user),
):
    return await AccountsService.get(pg, d1, account_id, user, company_code)


@router.patch("/accounts/{account_id}")
async def update_account(
    account_id: str, request: Request,
    company_code: Optional[str] = Query(default=None, alias="company_code"),
    pg: SupabasePostgres = Depends(get_pg), d1: D1Client = Depends(get_d1),
    user: UserSession = Depends(require_permission(PERMISSIONS["ACCOUNT_MANAGE"])),
):
    body = await read_json_object(request)
    return await AccountsService.update(pg, d1, account_id, parse_update_account(body), user, company_code)


@router.delete("/accounts/{account_id}")
async def deactivate_account(
    account_id: str,
    company_code: Optional[str] = Query(default=None, alias="company_code"),
    pg: SupabasePostgres = Depends(get_pg), d1: D1Client = Depends(get_d1),
    user: UserSession = Depends(require_permission(PERMISSIONS["ACCOUNT_MANAGE"])),
):
    return await AccountsService.deactivate(pg, d1, account_id, user, company_code)
