import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_active_organisation, CurrentUserContext
from app.db.session import get_db
from app.modules.vendors.models import VendorStatus, VendorType
from app.modules.vendors.schemas import VendorCreate, VendorResponse, VendorUpdate
from app.modules.vendors import service

router = APIRouter(prefix="/api/v1/vendors", tags=["Vendors"])


@router.post("", response_model=VendorResponse, status_code=status.HTTP_201_CREATED)
async def create_vendor(
    req: VendorCreate,
    ctx: CurrentUserContext = Depends(get_current_active_organisation),
    db: AsyncSession = Depends(get_db),
):
    return await service.create_vendor(
        org_id=ctx.organisation_id,
        actor_id=ctx.user_id,
        req=req,
        db=db,
    )


@router.get("", response_model=list[VendorResponse])
async def list_vendors(
    vendor_type: Optional[VendorType] = None,
    status: Optional[VendorStatus] = None,
    search: Optional[str] = Query(None, min_length=1, max_length=100),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    ctx: CurrentUserContext = Depends(get_current_active_organisation),
    db: AsyncSession = Depends(get_db),
):
    return await service.list_vendors(
        org_id=ctx.organisation_id,
        db=db,
        vendor_type=vendor_type,
        status_filter=status,
        search=search,
        skip=skip,
        limit=limit,
    )


@router.get("/{vendor_id}", response_model=VendorResponse)
async def get_vendor(
    vendor_id: uuid.UUID,
    ctx: CurrentUserContext = Depends(get_current_active_organisation),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_vendor(
        org_id=ctx.organisation_id,
        vendor_id=vendor_id,
        db=db,
    )


@router.patch("/{vendor_id}", response_model=VendorResponse)
async def update_vendor(
    vendor_id: uuid.UUID,
    req: VendorUpdate,
    ctx: CurrentUserContext = Depends(get_current_active_organisation),
    db: AsyncSession = Depends(get_db),
):
    return await service.update_vendor(
        org_id=ctx.organisation_id,
        vendor_id=vendor_id,
        actor_id=ctx.user_id,
        req=req,
        db=db,
    )


@router.delete("/{vendor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vendor(
    vendor_id: uuid.UUID,
    ctx: CurrentUserContext = Depends(get_current_active_organisation),
    db: AsyncSession = Depends(get_db),
):
    await service.delete_vendor(
        org_id=ctx.organisation_id,
        vendor_id=vendor_id,
        actor_id=ctx.user_id,
        db=db,
    )
