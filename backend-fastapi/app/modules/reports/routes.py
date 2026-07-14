from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.core.security import UserSession, get_current_user
from app.db.d1_client import D1Client
from app.db.supabase_pg import SupabasePostgres
from app.deps import get_d1, get_pg
from app.modules.reports.schemas import parse_pl_report_query
from app.modules.reports.service import ReportsService

router = APIRouter(tags=["reports"])


@router.get("/reports/pl")
async def profit_and_loss(
    request: Request,
    pg: SupabasePostgres = Depends(get_pg), d1: D1Client = Depends(get_d1),
    user: UserSession = Depends(get_current_user),
):
    query = parse_pl_report_query(dict(request.query_params))
    return await ReportsService.profit_and_loss(pg, d1, query, user)
