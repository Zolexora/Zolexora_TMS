import uuid
from typing import Optional
from fastapi import APIRouter, Body, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_active_organisation, CurrentUserContext
from app.db.session import get_db
from app.modules.bookings.models_request import BookingRequestStatus
from app.modules.bookings.schemas_request import (
    BookingRequestCreate,
    BookingRequestResponse,
)
from app.modules.bookings import service_request

router = APIRouter(prefix="/api/v1/booking-requests", tags=["Booking Requests"])


@router.post("", response_model=BookingRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_booking_request(
    req: BookingRequestCreate,
    ctx: CurrentUserContext = Depends(get_current_active_organisation),
    db: AsyncSession = Depends(get_db),
):
    return await service_request.create_booking_request(
        org_id=ctx.organisation_id,
        actor_id=ctx.user_id,
        req=req,
        db=db,
    )


@router.get("", response_model=list[BookingRequestResponse])
async def list_booking_requests(
    status: Optional[BookingRequestStatus] = None,
    customer_id: Optional[uuid.UUID] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    ctx: CurrentUserContext = Depends(get_current_active_organisation),
    db: AsyncSession = Depends(get_db),
):
    return await service_request.list_booking_requests(
        org_id=ctx.organisation_id,
        db=db,
        status_filter=status,
        customer_id=customer_id,
        skip=skip,
        limit=limit,
    )


@router.get("/{request_id}", response_model=BookingRequestResponse)
async def get_booking_request(
    request_id: uuid.UUID,
    ctx: CurrentUserContext = Depends(get_current_active_organisation),
    db: AsyncSession = Depends(get_db),
):
    return await service_request.get_booking_request(
        org_id=ctx.organisation_id,
        request_id=request_id,
        db=db,
    )


@router.post("/{request_id}/submit", response_model=BookingRequestResponse)
async def submit_booking_request(
    request_id: uuid.UUID,
    ctx: CurrentUserContext = Depends(get_current_active_organisation),
    db: AsyncSession = Depends(get_db),
):
    return await service_request.submit_booking_request(
        org_id=ctx.organisation_id,
        request_id=request_id,
        actor_id=ctx.user_id,
        db=db,
    )


from app.modules.bookings.schemas import BookingResponse


@router.post("/{request_id}/confirm", response_model=BookingResponse)
async def confirm_booking_request(
    request_id: uuid.UUID,
    ctx: CurrentUserContext = Depends(get_current_active_organisation),
    db: AsyncSession = Depends(get_db),
):
    return await service_request.confirm_booking_request(
        org_id=ctx.organisation_id,
        request_id=request_id,
        actor_id=ctx.user_id,
        db=db,
    )


@router.post("/{request_id}/cancel", response_model=BookingRequestResponse)
async def cancel_booking_request(
    request_id: uuid.UUID,
    reason: Optional[str] = Body(None, embed=True),
    ctx: CurrentUserContext = Depends(get_current_active_organisation),
    db: AsyncSession = Depends(get_db),
):
    return await service_request.cancel_booking_request(
        org_id=ctx.organisation_id,
        request_id=request_id,
        actor_id=ctx.user_id,
        reason=reason,
        db=db,
    )
