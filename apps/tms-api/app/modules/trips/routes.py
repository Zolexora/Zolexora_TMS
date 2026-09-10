import uuid
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_active_organisation, CurrentUserContext
from app.db.session import get_db
from app.modules.trips.schemas import (
    TripCompleteRequest,
    TripReceiptAddRequest,
    TripResponse,
    TripStartRequest,
)
from app.modules.trips import service

router = APIRouter(prefix="/api/v1/trips", tags=["Trips"])


@router.post("/duties/{duty_id}/start", response_model=TripResponse, status_code=status.HTTP_201_CREATED)
async def start_trip(
    duty_id: uuid.UUID,
    req: TripStartRequest,
    ctx: CurrentUserContext = Depends(get_current_active_organisation),
    db: AsyncSession = Depends(get_db),
):
    return await service.start_trip(
        org_id=ctx.organisation_id,
        duty_id=duty_id,
        actor_id=ctx.user_id,
        req=req,
        db=db,
    )


@router.post("/{trip_id}/complete", response_model=TripResponse)
async def complete_trip(
    trip_id: uuid.UUID,
    req: TripCompleteRequest,
    ctx: CurrentUserContext = Depends(get_current_active_organisation),
    db: AsyncSession = Depends(get_db),
):
    return await service.complete_trip(
        org_id=ctx.organisation_id,
        trip_id=trip_id,
        actor_id=ctx.user_id,
        req=req,
        db=db,
    )


@router.post("/{trip_id}/receipts", response_model=TripResponse)
async def add_trip_receipt(
    trip_id: uuid.UUID,
    req: TripReceiptAddRequest,
    ctx: CurrentUserContext = Depends(get_current_active_organisation),
    db: AsyncSession = Depends(get_db),
):
    return await service.add_trip_receipt(
        org_id=ctx.organisation_id,
        trip_id=trip_id,
        actor_id=ctx.user_id,
        req=req,
        db=db,
    )


@router.post("/{trip_id}/pod")
async def upload_pod(
    trip_id: uuid.UUID,
    notes: Optional[str] = Form(None),
    file: UploadFile = File(...),
    ctx: CurrentUserContext = Depends(get_current_active_organisation),
    db: AsyncSession = Depends(get_db),
):
    content = await file.read()
    url = await service.upload_pod(
        org_id=ctx.organisation_id,
        trip_id=trip_id,
        file_bytes=content,
        file_name=file.filename or "pod.pdf",
        content_type=file.content_type or "application/pdf",
        notes=notes,
        db=db,
    )
    return {"pod_attachment_url": url}


@router.get("", response_model=list[TripResponse])
async def list_trips(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    ctx: CurrentUserContext = Depends(get_current_active_organisation),
    db: AsyncSession = Depends(get_db),
):
    from app.modules.trips.models import TripStatus
    status_filter = TripStatus(status) if status else None
    return await service.list_trips(
        org_id=ctx.organisation_id,
        db=db,
        status_filter=status_filter,
        limit=limit,
        offset=offset,
    )


@router.get("/{trip_id}", response_model=TripResponse)
async def get_trip(
    trip_id: uuid.UUID,
    ctx: CurrentUserContext = Depends(get_current_active_organisation),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_trip(
        org_id=ctx.organisation_id,
        trip_id=trip_id,
        db=db,
    )

