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
from app.modules.entries.schemas import parse_create_entry
from app.modules.entries.service import EntriesService

router = APIRouter(tags=["entries"])


@router.post("/entries", status_code=201)
async def create_entry(
    request: Request,
    pg: SupabasePostgres = Depends(get_pg), d1: D1Client = Depends(get_d1),
    user: UserSession = Depends(require_permission(PERMISSIONS["ENTRY_CREATE"])),
):
    body = await read_json_object(request)
    return await EntriesService.create(pg, d1, parse_create_entry(body), user)


@router.get("/entries")
async def list_entries(
    company_code: Optional[str] = Query(default=None, alias="company_code"),
    company_id: Optional[str] = Query(default=None, alias="company_id"),
    period: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    limit: Optional[int] = Query(default=None),
    pg: SupabasePostgres = Depends(get_pg), d1: D1Client = Depends(get_d1),
    user: UserSession = Depends(get_current_user),
):
    code = company_code or company_id
    if not code:
        raise ValidationError("company_code is required")
    return await EntriesService.list(pg, d1, code, user, {"period": period, "status": status, "limit": limit})


@router.get("/entries/{batch_id}")
async def get_entry(batch_id: str, d1: D1Client = Depends(get_d1), user: UserSession = Depends(get_current_user)):
    return await EntriesService.get(d1, batch_id, user)


@router.post("/entries/{batch_id}/post")
async def post_entry(
    batch_id: str,
    pg: SupabasePostgres = Depends(get_pg), d1: D1Client = Depends(get_d1),
    user: UserSession = Depends(require_permission(PERMISSIONS["ENTRY_POST"])),
):
    return await EntriesService.post(pg, d1, batch_id, user)


@router.post("/entries/{batch_id}/reverse", status_code=201)
async def reverse_entry(
    batch_id: str,
    pg: SupabasePostgres = Depends(get_pg), d1: D1Client = Depends(get_d1),
    user: UserSession = Depends(require_permission(PERMISSIONS["ENTRY_REVERSE"])),
):
    return await EntriesService.reverse(pg, d1, batch_id, user)
