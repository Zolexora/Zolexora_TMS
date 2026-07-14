from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.core.permissions import PERMISSIONS
from app.core.security import UserSession, require_permission
from app.db.d1_client import D1Client
from app.db.supabase_pg import SupabasePostgres
from app.deps import get_d1, get_pg
from app.modules.imports.service import ImportsService

router = APIRouter(tags=["imports"])


@router.post("/imports/validate")
async def validate_import(
    company_code: str = Form(...),
    file: UploadFile = File(...),
    pg: SupabasePostgres = Depends(get_pg), d1: D1Client = Depends(get_d1),
    user: UserSession = Depends(require_permission(PERMISSIONS["IMPORT_VALIDATE"])),
):
    raw_bytes = await file.read()
    return await ImportsService.validate(pg, d1, company_code, raw_bytes, user)


@router.post("/imports/confirm")
async def confirm_import(
    validation_id: str = Form(...),
    company_code: str = Form(...),
    pg: SupabasePostgres = Depends(get_pg), d1: D1Client = Depends(get_d1),
    user: UserSession = Depends(require_permission(PERMISSIONS["IMPORT_CONFIRM"])),
):
    return await ImportsService.confirm(pg, d1, validation_id, company_code, user)
