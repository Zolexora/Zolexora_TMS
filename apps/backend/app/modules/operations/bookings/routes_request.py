import uuid
from typing import Optional
from fastapi import APIRouter, Body, Depends, Query, status

from app.auth.dependencies import TenantContext, get_tenant_context
from app.modules.operations.bookings.enums import BookingRequestStatus
from app.modules.operations.bookings.schemas_request import (
    BookingRequestCreate,
    BookingRequestResponse,
)
from app.modules.operations.bookings import service_request
from app.modules.operations.bookings.schemas import BookingResponse

router = APIRouter(prefix="/api/v1/booking-requests", tags=["Booking Requests"])

@router.post("", response_model=BookingRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_booking_request(
    req: BookingRequestCreate,
    ctx: TenantContext = Depends(get_tenant_context),
):
    return await service_request.create_booking_request(ctx, req)

@router.get("", response_model=list[BookingRequestResponse])
async def list_booking_requests(
    status: Optional[BookingRequestStatus] = None,
    customer_id: Optional[uuid.UUID] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    ctx: TenantContext = Depends(get_tenant_context),
):
    return await service_request.list_booking_requests(ctx, status, customer_id, skip, limit)

@router.get("/{request_id}", response_model=BookingRequestResponse)
async def get_booking_request(
    request_id: uuid.UUID,
    ctx: TenantContext = Depends(get_tenant_context),
):
    return await service_request.get_booking_request(ctx, request_id)

@router.post("/{request_id}/submit", response_model=BookingRequestResponse)
async def submit_booking_request(
    request_id: uuid.UUID,
    ctx: TenantContext = Depends(get_tenant_context),
):
    return await service_request.submit_booking_request(ctx, request_id)

@router.post("/{request_id}/confirm", response_model=BookingResponse)
async def confirm_booking_request(
    request_id: uuid.UUID,
    ctx: TenantContext = Depends(get_tenant_context),
):
    return await service_request.confirm_booking_request(ctx, request_id)

@router.post("/{request_id}/cancel", response_model=BookingRequestResponse)
async def cancel_booking_request(
    request_id: uuid.UUID,
    reason: Optional[str] = Body(None, embed=True),
    ctx: TenantContext = Depends(get_tenant_context),
):
    return await service_request.cancel_booking_request(ctx, request_id, reason)
