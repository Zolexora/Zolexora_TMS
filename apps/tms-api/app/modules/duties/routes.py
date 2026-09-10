import uuid
from typing import Optional
from fastapi import APIRouter, Body, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_active_organisation, CurrentUserContext
from app.db.session import get_db
from app.modules.duties.models import DutyStatus
from app.modules.duties.schemas import (
    DutyAssignRequest,
    DutyCreate,
    DutyResponse,
)
from app.modules.duties import service

router = APIRouter(prefix="/api/v1/duties", tags=["Duties"])


@router.post("", response_model=DutyResponse, status_code=status.HTTP_201_CREATED)
async def create_duty(
    req: DutyCreate,
    ctx: CurrentUserContext = Depends(get_current_active_organisation),
    db: AsyncSession = Depends(get_db),
):
    return await service.create_duty(
        org_id=ctx.organisation_id,
        actor_id=ctx.user_id,
        req=req,
        db=db,
    )


@router.get("", response_model=list[DutyResponse])
async def list_duties(
    status: Optional[DutyStatus] = None,
    driver_id: Optional[uuid.UUID] = None,
    vehicle_id: Optional[uuid.UUID] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    ctx: CurrentUserContext = Depends(get_current_active_organisation),
    db: AsyncSession = Depends(get_db),
):
    return await service.list_duties(
        org_id=ctx.organisation_id,
        db=db,
        status_filter=status,
        driver_id=driver_id,
        vehicle_id=vehicle_id,
        skip=skip,
        limit=limit,
    )


@router.get("/{duty_id}", response_model=DutyResponse)
async def get_duty(
    duty_id: uuid.UUID,
    ctx: CurrentUserContext = Depends(get_current_active_organisation),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_duty(
        org_id=ctx.organisation_id,
        duty_id=duty_id,
        db=db,
    )


@router.post("/{duty_id}/assign", response_model=DutyResponse)
async def assign_duty(
    duty_id: uuid.UUID,
    req: DutyAssignRequest,
    ctx: CurrentUserContext = Depends(get_current_active_organisation),
    db: AsyncSession = Depends(get_db),
):
    return await service.assign_duty(
        org_id=ctx.organisation_id,
        duty_id=duty_id,
        actor_id=ctx.user_id,
        req=req,
        db=db,
    )


@router.post("/{duty_id}/dispatch", response_model=DutyResponse)
async def dispatch_duty(
    duty_id: uuid.UUID,
    ctx: CurrentUserContext = Depends(get_current_active_organisation),
    db: AsyncSession = Depends(get_db),
):
    return await service.dispatch_duty(
        org_id=ctx.organisation_id,
        duty_id=duty_id,
        actor_id=ctx.user_id,
        db=db,
    )


@router.post("/{duty_id}/accept", response_model=DutyResponse)
async def accept_duty(
    duty_id: uuid.UUID,
    ctx: CurrentUserContext = Depends(get_current_active_organisation),
    db: AsyncSession = Depends(get_db),
):
    return await service.driver_accept_duty(
        org_id=ctx.organisation_id,
        duty_id=duty_id,
        driver_user_id=ctx.user_id,
        db=db,
    )


@router.post("/{duty_id}/reject", response_model=DutyResponse)
async def reject_duty(
    duty_id: uuid.UUID,
    reason: Optional[str] = Body(None, embed=True),
    ctx: CurrentUserContext = Depends(get_current_active_organisation),
    db: AsyncSession = Depends(get_db),
):
    return await service.driver_reject_duty(
        org_id=ctx.organisation_id,
        duty_id=duty_id,
        driver_user_id=ctx.user_id,
        reason=reason,
        db=db,
    )


@router.post("/{duty_id}/arrived-pickup", response_model=DutyResponse)
async def arrive_pickup(
    duty_id: uuid.UUID,
    ctx: CurrentUserContext = Depends(get_current_active_organisation),
    db: AsyncSession = Depends(get_db),
):
    return await service.update_duty_milestone(
        org_id=ctx.organisation_id,
        duty_id=duty_id,
        actor_id=ctx.user_id,
        target_status=DutyStatus.ARRIVED_PICKUP,
        db=db,
    )


@router.post("/{duty_id}/in-transit", response_model=DutyResponse)
async def in_transit(
    duty_id: uuid.UUID,
    ctx: CurrentUserContext = Depends(get_current_active_organisation),
    db: AsyncSession = Depends(get_db),
):
    return await service.update_duty_milestone(
        org_id=ctx.organisation_id,
        duty_id=duty_id,
        actor_id=ctx.user_id,
        target_status=DutyStatus.IN_TRANSIT,
        db=db,
    )


@router.post("/{duty_id}/arrived-drop", response_model=DutyResponse)
async def arrive_drop(
    duty_id: uuid.UUID,
    ctx: CurrentUserContext = Depends(get_current_active_organisation),
    db: AsyncSession = Depends(get_db),
):
    return await service.update_duty_milestone(
        org_id=ctx.organisation_id,
        duty_id=duty_id,
        actor_id=ctx.user_id,
        target_status=DutyStatus.ARRIVED_DROP,
        db=db,
    )


@router.post("/{duty_id}/complete", response_model=DutyResponse)
async def complete_duty(
    duty_id: uuid.UUID,
    ctx: CurrentUserContext = Depends(get_current_active_organisation),
    db: AsyncSession = Depends(get_db),
):
    return await service.update_duty_milestone(
        org_id=ctx.organisation_id,
        duty_id=duty_id,
        actor_id=ctx.user_id,
        target_status=DutyStatus.DUTY_COMPLETED,
        db=db,
    )
