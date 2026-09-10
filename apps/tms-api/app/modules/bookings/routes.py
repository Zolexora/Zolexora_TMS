import uuid
from typing import Optional
from fastapi import APIRouter, Body, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_active_organisation, CurrentUserContext
from app.db.session import get_db
from app.modules.bookings.models import BookingStatus
from app.modules.bookings.schemas import BookingCreate, BookingResponse
from app.modules.bookings import service

router = APIRouter(prefix="/api/v1/bookings", tags=["Bookings"])


@router.post("", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    req: BookingCreate,
    ctx: CurrentUserContext = Depends(get_current_active_organisation),
    db: AsyncSession = Depends(get_db),
):
    return await service.create_booking(
        org_id=ctx.organisation_id,
        actor_id=ctx.user_id,
        req=req,
        db=db,
    )


@router.get("", response_model=list[BookingResponse])
async def list_bookings(
    status: Optional[BookingStatus] = None,
    customer_id: Optional[uuid.UUID] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    ctx: CurrentUserContext = Depends(get_current_active_organisation),
    db: AsyncSession = Depends(get_db),
):
    return await service.list_bookings(
        org_id=ctx.organisation_id,
        db=db,
        status_filter=status,
        customer_id=customer_id,
        skip=skip,
        limit=limit,
    )


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: uuid.UUID,
    ctx: CurrentUserContext = Depends(get_current_active_organisation),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_booking(
        org_id=ctx.organisation_id,
        booking_id=booking_id,
        db=db,
    )


@router.post("/{booking_id}/cancel", response_model=BookingResponse)
async def cancel_booking(
    booking_id: uuid.UUID,
    reason: Optional[str] = Body(None, embed=True),
    ctx: CurrentUserContext = Depends(get_current_active_organisation),
    db: AsyncSession = Depends(get_db),
):
    return await service.cancel_booking(
        org_id=ctx.organisation_id,
        booking_id=booking_id,
        actor_id=ctx.user_id,
        reason=reason,
        db=db,
    )


@router.post("/{booking_id}/create-duty", status_code=status.HTTP_201_CREATED)
async def create_duty_from_booking(
    booking_id: uuid.UUID,
    req: dict = Body(...),
    ctx: CurrentUserContext = Depends(get_current_active_organisation),
    db: AsyncSession = Depends(get_db),
):
    from app.modules.duties.schemas import DutyCreate, DutyResponse
    from app.modules.duties import service as duty_service

    duty_create = DutyCreate(
        booking_id=booking_id,
        scheduled_start_time=req["scheduled_start_time"],
        scheduled_end_time=req["scheduled_end_time"],
        driver_id=req.get("driver_id"),
        vehicle_id=req.get("vehicle_id"),
        notes=req.get("notes"),
    )
    res = await duty_service.create_duty(
        org_id=ctx.organisation_id,
        actor_id=ctx.user_id,
        req=duty_create,
        db=db,
    )
    return DutyResponse.model_validate(res)

