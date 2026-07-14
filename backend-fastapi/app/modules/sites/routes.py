from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request

from app.core.errors import ValidationError
from app.core.permissions import PERMISSIONS
from app.core.security import UserSession, get_current_user, require_permission
from app.core.validation import read_json_object
from app.db.d1_client import D1Client
from app.db.supabase_pg import SupabasePostgres
from app.deps import get_d1, get_pg
from app.modules.sites.schemas import parse_create_site, parse_update_site
from app.modules.sites.service import SitesService

router = APIRouter(tags=["sites"])


@router.get("/sites")
async def list_sites(
    company_code: str | None = Query(default=None, alias="company_code"),
    company_id: str | None = Query(default=None, alias="company_id"),
    pg: SupabasePostgres = Depends(get_pg),
    user: UserSession = Depends(get_current_user),
):
    code = company_code or company_id
    if not code:
        raise ValidationError("company_code is required")
    return await SitesService.list(pg, code, user)


@router.post("/sites", status_code=201)
async def create_site(
    request: Request,
    pg: SupabasePostgres = Depends(get_pg), d1: D1Client = Depends(get_d1),
    user: UserSession = Depends(require_permission(PERMISSIONS["COMPANY_MANAGE"])),
):
    body = await read_json_object(request)
    return await SitesService.create(pg, d1, parse_create_site(body), user)


@router.patch("/sites/{site_id}")
async def update_site(
    site_id: str, request: Request,
    pg: SupabasePostgres = Depends(get_pg), d1: D1Client = Depends(get_d1),
    user: UserSession = Depends(require_permission(PERMISSIONS["COMPANY_MANAGE"])),
):
    body = await read_json_object(request)
    return await SitesService.update(pg, d1, site_id, parse_update_site(body), user)


@router.delete("/sites/{site_id}")
async def deactivate_site(
    site_id: str,
    pg: SupabasePostgres = Depends(get_pg), d1: D1Client = Depends(get_d1),
    user: UserSession = Depends(require_permission(PERMISSIONS["COMPANY_MANAGE"])),
):
    return await SitesService.deactivate(pg, d1, site_id, user)
