from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request

from app.core.permissions import PERMISSIONS
from app.core.security import UserSession, get_current_user, require_permission
from app.core.validation import read_json_object
from app.db.d1_client import D1Client
from app.db.supabase_pg import SupabasePostgres
from app.deps import get_d1, get_pg
from app.modules.pnl_groups.schemas import parse_create_pl_group, parse_update_pl_group
from app.modules.pnl_groups.service import PLGroupsService

router = APIRouter(tags=["pnl-groups"])


@router.post("/pnl-groups", status_code=201)
async def create_pl_group(
    request: Request,
    pg: SupabasePostgres = Depends(get_pg), d1: D1Client = Depends(get_d1),
    user: UserSession = Depends(require_permission(PERMISSIONS["PL_GROUP_MANAGE"])),
):
    body = await read_json_object(request)
    return await PLGroupsService.create(pg, d1, parse_create_pl_group(body), user)


@router.get("/pnl-groups")
async def list_pl_groups(
    company_code: str | None = Query(default=None, alias="company_code"),
    pg: SupabasePostgres = Depends(get_pg),
    user: UserSession = Depends(get_current_user),
):
    return await PLGroupsService.list(pg, company_code, user)


@router.get("/pnl-groups/{group_id}")
async def get_pl_group(group_id: str, pg: SupabasePostgres = Depends(get_pg), user: UserSession = Depends(get_current_user)):
    return await PLGroupsService.get(pg, group_id, user)


@router.patch("/pnl-groups/{group_id}")
async def update_pl_group(
    group_id: str, request: Request,
    pg: SupabasePostgres = Depends(get_pg), d1: D1Client = Depends(get_d1),
    user: UserSession = Depends(require_permission(PERMISSIONS["PL_GROUP_MANAGE"])),
):
    body = await read_json_object(request)
    return await PLGroupsService.update(pg, d1, group_id, parse_update_pl_group(body), user)


@router.delete("/pnl-groups/{group_id}")
async def deactivate_pl_group(
    group_id: str,
    pg: SupabasePostgres = Depends(get_pg), d1: D1Client = Depends(get_d1),
    user: UserSession = Depends(require_permission(PERMISSIONS["PL_GROUP_MANAGE"])),
):
    return await PLGroupsService.deactivate(pg, d1, group_id, user)
