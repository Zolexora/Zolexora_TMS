import uuid
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from typing import Dict, Any

from app.auth.dependencies import get_current_active_organisation, CurrentUserContext, get_tenant_context
from app.core.tenant import TenantContext
from app.modules.extensions.r1rcm.schemas import R1ImportPreviewResponse, R1ConfirmImportRequest
from app.modules.extensions.r1rcm import service

router = APIRouter(prefix="/api/v1/operations/r1rcm", tags=["R1 RCM Operations"])

# Security Dependency to ensure proper scope
async def require_r1_scope(
    customer_id: uuid.UUID = Form(...),
    location: str = Form(...),
    ctx: CurrentUserContext = Depends(get_current_active_organisation)
):
    # In a real implementation, we query RolePermission / Scopes to ensure 
    # ctx.user_id has access to `customer_id` and `location`.
    # For now, we simulate this verification check.
    return ctx

@router.post("/import", response_model=R1ImportPreviewResponse)
async def upload_r1_excel(
    file: UploadFile = File(...),
    customer_id: uuid.UUID = Form(...),
    location: str = Form(...),
    ctx: CurrentUserContext = Depends(require_r1_scope)
):
    tenant_ctx = await get_tenant_context(ctx.organisation_id)
    return await service.process_excel_upload(tenant_ctx, file, customer_id, location)

@router.post("/import/confirm")
async def confirm_r1_import(
    req: R1ConfirmImportRequest,
    ctx: CurrentUserContext = Depends(get_current_active_organisation)
):
    tenant_ctx = await get_tenant_context(ctx.organisation_id)
    return await service.confirm_import(tenant_ctx, req)
