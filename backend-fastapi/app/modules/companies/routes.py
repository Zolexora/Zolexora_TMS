from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.core.permissions import PERMISSIONS
from app.core.security import UserSession, get_current_user, require_permission
from app.core.validation import read_json_object
from app.db.d1_client import D1Client
from app.db.supabase_pg import SupabasePostgres
from app.deps import get_d1, get_pg
from app.modules.companies.schemas import parse_create_company, parse_update_company
from app.modules.companies.service import CompaniesService

router = APIRouter(tags=["companies"])


@router.post("/companies", status_code=201)
async def create_company(
    request: Request,
    pg: SupabasePostgres = Depends(get_pg),
    d1: D1Client = Depends(get_d1),
    user: UserSession = Depends(require_permission(PERMISSIONS["COMPANY_MANAGE"])),
):
    body = await read_json_object(request)
    return await CompaniesService.create(pg, d1, parse_create_company(body), user)


@router.get("/companies")
async def list_companies(pg: SupabasePostgres = Depends(get_pg), user: UserSession = Depends(get_current_user)):
    return await CompaniesService.list(pg, user)


@router.get("/companies/{code}")
async def get_company(code: str, pg: SupabasePostgres = Depends(get_pg), user: UserSession = Depends(get_current_user)):
    return await CompaniesService.get(pg, code, user)


async def _update(code: str, request: Request, pg: SupabasePostgres, d1: D1Client, user: UserSession):
    body = await read_json_object(request)
    return await CompaniesService.update(pg, d1, code, parse_update_company(body), user)


@router.put("/companies/{code}")
async def put_company(
    code: str, request: Request,
    pg: SupabasePostgres = Depends(get_pg), d1: D1Client = Depends(get_d1),
    user: UserSession = Depends(require_permission(PERMISSIONS["COMPANY_MANAGE"])),
):
    return await _update(code, request, pg, d1, user)


@router.patch("/companies/{code}")
async def patch_company(
    code: str, request: Request,
    pg: SupabasePostgres = Depends(get_pg), d1: D1Client = Depends(get_d1),
    user: UserSession = Depends(require_permission(PERMISSIONS["COMPANY_MANAGE"])),
):
    return await _update(code, request, pg, d1, user)


@router.delete("/companies/{code}")
async def deactivate_company(
    code: str,
    pg: SupabasePostgres = Depends(get_pg), d1: D1Client = Depends(get_d1),
    user: UserSession = Depends(require_permission(PERMISSIONS["COMPANY_MANAGE"])),
):
    return await CompaniesService.deactivate(pg, d1, code, user)
