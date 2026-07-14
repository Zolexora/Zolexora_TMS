from __future__ import annotations
from fastapi import APIRouter, Depends, Query
from app.core.errors import ValidationError
from app.core.security import UserSession, get_current_user
from app.db.supabase_pg import SupabasePostgres
from app.deps import get_pg
from app.modules.clients.service import ClientsService

router = APIRouter(tags=["clients"])


@router.get("/clients")
async def list_clients(
    company_code: str | None = Query(default=None, alias="company_code"),
    company_id: str | None = Query(default=None, alias="company_id"),
    pg: SupabasePostgres = Depends(get_pg),
    user: UserSession = Depends(get_current_user),
):
    code = company_code or company_id
    if not code:
        raise ValidationError("company_code is required")
    return await ClientsService.list(pg, code, user)
