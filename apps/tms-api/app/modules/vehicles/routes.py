import uuid
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status

from app.auth.dependencies import get_current_active_organisation, get_tenant_context, CurrentUserContext
from app.core.tenant import TenantContext
from app.modules.vehicles.schemas import VehicleCreate, VehicleResponse, VehicleUpdate, VehicleBodyType, VehicleOperationalStatus, VehicleOwnershipType
from app.modules.vehicles import service

router = APIRouter(prefix="/api/v1/vehicles", tags=["Vehicles"])


@router.post("", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
async def create_vehicle(
    req: VehicleCreate,
    ctx: CurrentUserContext = Depends(get_current_active_organisation),
    tenant_ctx: TenantContext = Depends(get_tenant_context),
):
    return await service.create_vehicle(
        org_id=ctx.organisation_id,
        actor_id=ctx.user_id,
        req=req,
        tenant_ctx=tenant_ctx,
    )


@router.get("", response_model=list[VehicleResponse])
async def list_vehicles(
    status: Optional[VehicleOperationalStatus] = None,
    vehicle_type: Optional[VehicleBodyType] = None,
    ownership_type: Optional[VehicleOwnershipType] = None,
    search: Optional[str] = Query(None, min_length=1, max_length=100),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    ctx: CurrentUserContext = Depends(get_current_active_organisation),
    tenant_ctx: TenantContext = Depends(get_tenant_context),
):
    return await service.list_vehicles(
        org_id=ctx.organisation_id,
        tenant_ctx=tenant_ctx,
        status_filter=status,
        vehicle_type=vehicle_type,
        ownership_type=ownership_type,
        search=search,
        skip=skip,
        limit=limit,
    )


@router.get("/{vehicle_id}", response_model=VehicleResponse)
async def get_vehicle(
    vehicle_id: uuid.UUID,
    ctx: CurrentUserContext = Depends(get_current_active_organisation),
    tenant_ctx: TenantContext = Depends(get_tenant_context),
):
    return await service.get_vehicle(
        org_id=ctx.organisation_id,
        vehicle_id=vehicle_id,
        tenant_ctx=tenant_ctx,
    )


@router.patch("/{vehicle_id}", response_model=VehicleResponse)
async def update_vehicle(
    vehicle_id: uuid.UUID,
    req: VehicleUpdate,
    ctx: CurrentUserContext = Depends(get_current_active_organisation),
    tenant_ctx: TenantContext = Depends(get_tenant_context),
):
    return await service.update_vehicle(
        org_id=ctx.organisation_id,
        vehicle_id=vehicle_id,
        actor_id=ctx.user_id,
        req=req,
        tenant_ctx=tenant_ctx,
    )


@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vehicle(
    vehicle_id: uuid.UUID,
    ctx: CurrentUserContext = Depends(get_current_active_organisation),
    tenant_ctx: TenantContext = Depends(get_tenant_context),
):
    await service.delete_vehicle(
        org_id=ctx.organisation_id,
        vehicle_id=vehicle_id,
        actor_id=ctx.user_id,
        tenant_ctx=tenant_ctx,
    )


@router.post("/{vehicle_id}/documents")
async def upload_document(
    vehicle_id: uuid.UUID,
    doc_type: str = Form(..., description="e.g. rc, insurance, fitness, permit, puc"),
    file: UploadFile = File(...),
    ctx: CurrentUserContext = Depends(get_current_active_organisation),
    tenant_ctx: TenantContext = Depends(get_tenant_context),
):
    content = await file.read()
    url = await service.upload_vehicle_doc(
        org_id=ctx.organisation_id,
        vehicle_id=vehicle_id,
        doc_type=doc_type,
        file_name=file.filename or "document.pdf",
        file_bytes=content,
        content_type=file.content_type or "application/pdf",
        tenant_ctx=tenant_ctx,
    )
    return {"doc_type": doc_type, "document_url": url}
