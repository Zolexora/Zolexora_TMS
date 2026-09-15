import uuid
from typing import Optional
from fastapi import APIRouter, Body, Depends, Query, status

from app.auth.dependencies import TenantContext, get_tenant_context
from app.modules.duties.schemas import (
    DutyAssignRequest,
    DutyCreate,
    DutyResponse,
    DutyStatus,
)
from app.modules.duties import service

router = APIRouter(prefix="/api/v1/duties", tags=["Duties"])


@router.post("", response_model=DutyResponse, status_code=status.HTTP_201_CREATED)
async def create_duty(
    req: DutyCreate,
    ctx: TenantContext = Depends(get_tenant_context),
):
    return await service.create_duty(ctx, req)


@router.get("", response_model=list[DutyResponse])
async def list_duties(
    status: Optional[DutyStatus] = None,
    driver_id: Optional[uuid.UUID] = None,
    vehicle_id: Optional[uuid.UUID] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    ctx: TenantContext = Depends(get_tenant_context),
):
    return await service.list_duties(ctx, status, driver_id, vehicle_id, skip, limit)


@router.get("/{duty_id}", response_model=DutyResponse)
async def get_duty(
    duty_id: uuid.UUID,
    ctx: TenantContext = Depends(get_tenant_context),
):
    return await service.get_duty(ctx, duty_id)


@router.post("/{duty_id}/assign", response_model=DutyResponse)
async def assign_duty(
    duty_id: uuid.UUID,
    req: DutyAssignRequest,
    ctx: TenantContext = Depends(get_tenant_context),
):
    return await service.assign_duty(ctx, duty_id, req)


@router.post("/{duty_id}/dispatch", response_model=DutyResponse)
async def dispatch_duty(
    duty_id: uuid.UUID,
    ctx: TenantContext = Depends(get_tenant_context),
):
    return await service.dispatch_duty(ctx, duty_id)


@router.post("/{duty_id}/accept", response_model=DutyResponse)
async def accept_duty(
    duty_id: uuid.UUID,
    ctx: TenantContext = Depends(get_tenant_context),
):
    return await service.driver_accept_duty(ctx, duty_id)


@router.post("/{duty_id}/reject", response_model=DutyResponse)
async def reject_duty(
    duty_id: uuid.UUID,
    reason: Optional[str] = Body(None, embed=True),
    ctx: TenantContext = Depends(get_tenant_context),
):
    return await service.driver_reject_duty(ctx, duty_id, reason)


@router.post("/{duty_id}/arrived-pickup", response_model=DutyResponse)
async def arrive_pickup(
    duty_id: uuid.UUID,
    ctx: TenantContext = Depends(get_tenant_context),
):
    return await service.update_duty_milestone(ctx, duty_id, DutyStatus.ARRIVED_PICKUP)


@router.post("/{duty_id}/in-transit", response_model=DutyResponse)
async def in_transit(
    duty_id: uuid.UUID,
    ctx: TenantContext = Depends(get_tenant_context),
):
    return await service.update_duty_milestone(ctx, duty_id, DutyStatus.IN_TRANSIT)


@router.post("/{duty_id}/arrived-drop", response_model=DutyResponse)
async def arrive_drop(
    duty_id: uuid.UUID,
    ctx: TenantContext = Depends(get_tenant_context),
):
    return await service.update_duty_milestone(ctx, duty_id, DutyStatus.ARRIVED_DROP)


@router.post("/{duty_id}/complete", response_model=DutyResponse)
async def complete_duty(
    duty_id: uuid.UUID,
    ctx: TenantContext = Depends(get_tenant_context),
):
    return await service.update_duty_milestone(ctx, duty_id, DutyStatus.DUTY_COMPLETED)

