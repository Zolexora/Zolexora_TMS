from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.core.security import UserSession, get_current_user
from app.core.validation import read_json_object
from app.db.d1_client import D1Client
from app.db.supabase_pg import SupabasePostgres
from app.deps import get_d1, get_pg
from app.modules.auth.schemas import parse_company_access, parse_set_role
from app.modules.auth.service import AuthService

router = APIRouter(tags=["auth"])


@router.get("/auth/me")
async def me(user: UserSession = Depends(get_current_user)):
    return AuthService.me(user)


@router.get("/users")
async def list_users(pg: SupabasePostgres = Depends(get_pg), user: UserSession = Depends(get_current_user)):
    return await AuthService.list_users(pg, user)


@router.patch("/users/{auth_user_id}/role")
async def set_role(
    auth_user_id: str, request: Request,
    pg: SupabasePostgres = Depends(get_pg), d1: D1Client = Depends(get_d1),
    user: UserSession = Depends(get_current_user),
):
    body = await read_json_object(request)
    return await AuthService.set_role(pg, d1, auth_user_id, parse_set_role(body).role, user)


@router.post("/users/{auth_user_id}/company-access")
async def grant_company_access(
    auth_user_id: str, request: Request,
    pg: SupabasePostgres = Depends(get_pg), d1: D1Client = Depends(get_d1),
    user: UserSession = Depends(get_current_user),
):
    body = await read_json_object(request)
    return await AuthService.grant_company_access(pg, d1, auth_user_id, parse_company_access(body).company_code, user)


@router.delete("/users/{auth_user_id}/company-access/{company_code}")
async def revoke_company_access(
    auth_user_id: str, company_code: str,
    pg: SupabasePostgres = Depends(get_pg), d1: D1Client = Depends(get_d1),
    user: UserSession = Depends(get_current_user),
):
    return await AuthService.revoke_company_access(pg, d1, auth_user_id, company_code, user)
