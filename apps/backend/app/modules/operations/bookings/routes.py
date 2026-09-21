import uuid
from typing import Optional
from fastapi import APIRouter, Body, Depends, Query, status

from app.auth.dependencies import TenantContext, get_tenant_context
from app.modules.operations.bookings.schemas import BookingCreate, BookingResponse
from app.modules.operations.bookings import service
from app.modules.operations.bookings.schemas import BookingStatus

router = APIRouter(prefix="/api/v1/bookings", tags=["Bookings"])


@router.post("", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    req: BookingCreate,
    ctx: TenantContext = Depends(get_tenant_context),
):
    return await service.create_booking(ctx, req)


@router.get("", response_model=list[BookingResponse])
async def list_bookings(
    status: Optional[BookingStatus] = None,
    customer_id: Optional[uuid.UUID] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    ctx: TenantContext = Depends(get_tenant_context),
):
    return await service.list_bookings(ctx, status, customer_id, skip, limit)


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: uuid.UUID,
    ctx: TenantContext = Depends(get_tenant_context),
):
    return await service.get_booking(ctx, booking_id)


@router.post("/{booking_id}/cancel", response_model=BookingResponse)
async def cancel_booking(
    booking_id: uuid.UUID,
    reason: Optional[str] = Body(None, embed=True),
    ctx: TenantContext = Depends(get_tenant_context),
):
    return await service.cancel_booking(ctx, booking_id, reason)


@router.post("/{booking_id}/create-duty", status_code=status.HTTP_201_CREATED)
async def create_duty_from_booking(
    booking_id: uuid.UUID,
    req: dict = Body(...),
    ctx: TenantContext = Depends(get_tenant_context),
):
    from app.modules.operations.duties.schemas import DutyCreate, DutyResponse
    from app.modules.operations.duties import service as duty_service

    duty_create = DutyCreate(
        booking_id=booking_id,
        scheduled_start_time=req["scheduled_start_time"],
        scheduled_end_time=req["scheduled_end_time"],
        driver_id=req.get("driver_id"),
        vehicle_id=req.get("vehicle_id"),
        notes=req.get("notes"),
    )
    res = await duty_service.create_duty(ctx, duty_create)
    return DutyResponse.model_validate(res)

