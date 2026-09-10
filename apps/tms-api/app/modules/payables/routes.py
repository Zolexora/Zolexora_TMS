import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.auth.dependencies import get_current_user, get_current_active_organisation, AuthenticatedUser
from app.modules.payables.schemas import (
    PayableCreateRequest, PayableResponse,
    SettlementCreateRequest, SettlementResponse
)
from app.modules.payables.models import Payable, PayableLine, PayableStatus, Settlement

router = APIRouter(prefix="/payables", tags=["Payables"])


@router.post("", response_model=PayableResponse, status_code=status.HTTP_201_CREATED)
async def create_payable(
    request: PayableCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_org_user: AuthenticatedUser = Depends(get_current_active_organisation),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Create a Payable to a Vendor or Driver.
    """
    if not request.vendor_id and not request.driver_id:
        raise HTTPException(status_code=400, detail="Must specify either vendor_id or driver_id")
        
    payable = Payable(
        organisation_id=current_org_user.organisation_id,
        vendor_id=request.vendor_id,
        driver_id=request.driver_id,
        duty_id=request.duty_id,
        reference_number=request.reference_number,
        currency=request.currency,
        status=PayableStatus.DRAFT,
        notes=request.notes,
        created_by_user_id=current_user.id
    )
    
    subtotal = 0
    deductions = 0
    
    db_lines = []
    for line in request.lines:
        pl = PayableLine(
            description=line.description,
            amount=line.amount,
            is_deduction=line.is_deduction
        )
        if line.is_deduction:
            deductions += line.amount
        else:
            subtotal += line.amount
        db_lines.append(pl)
        
    payable.subtotal = subtotal
    payable.deductions = deductions
    payable.advances = 0 # Can be implemented later
    payable.grand_total = subtotal - deductions
    
    payable.lines = db_lines
    db.add(payable)
    await db.commit()
    await db.refresh(payable)
    
    return payable


@router.get("", response_model=List[PayableResponse])
async def list_payables(
    db: AsyncSession = Depends(get_db),
    current_org_user: AuthenticatedUser = Depends(get_current_active_organisation),
):
    query = await db.execute(
        select(Payable)
        .options(selectinload(Payable.lines))
        .where(Payable.organisation_id == current_org_user.organisation_id)
        .order_by(Payable.created_at.desc())
    )
    return query.scalars().all()


@router.get("/{payable_id}", response_model=PayableResponse)
async def get_payable(
    payable_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_org_user: AuthenticatedUser = Depends(get_current_active_organisation),
):
    query = await db.execute(
        select(Payable)
        .options(selectinload(Payable.lines))
        .where(Payable.id == payable_id, Payable.organisation_id == current_org_user.organisation_id)
    )
    payable = query.scalar_one_or_none()
    if not payable:
        raise HTTPException(status_code=404, detail="Payable not found")
    return payable


@router.post("/{payable_id}/approve")
async def approve_payable(
    payable_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_org_user: AuthenticatedUser = Depends(get_current_active_organisation),
):
    query = await db.execute(
        select(Payable).where(Payable.id == payable_id, Payable.organisation_id == current_org_user.organisation_id)
    )
    payable = query.scalar_one_or_none()
    
    if not payable:
        raise HTTPException(status_code=404, detail="Payable not found")
        
    if payable.status != PayableStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Only DRAFT payables can be approved")
        
    payable.status = PayableStatus.APPROVED
    await db.commit()
    return {"message": "Payable approved successfully"}


@router.post("/{payable_id}/settlements", response_model=SettlementResponse, status_code=status.HTTP_201_CREATED)
async def create_settlement(
    payable_id: uuid.UUID,
    request: SettlementCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_org_user: AuthenticatedUser = Depends(get_current_active_organisation),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Record a payment made against an APPROVED payable.
    """
    query = await db.execute(
        select(Payable).where(Payable.id == payable_id, Payable.organisation_id == current_org_user.organisation_id)
    )
    payable = query.scalar_one_or_none()
    
    if not payable:
        raise HTTPException(status_code=404, detail="Payable not found")
        
    if payable.status not in [PayableStatus.APPROVED, PayableStatus.SETTLED]:
        raise HTTPException(status_code=400, detail="Cannot settle a payable that is not APPROVED")
        
    settlement = Settlement(
        payable_id=payable.id,
        amount=request.amount,
        settlement_date=request.settlement_date,
        payment_reference=request.payment_reference,
        notes=request.notes,
        created_by_user_id=current_user.id
    )
    
    db.add(settlement)
    
    # Auto-update payable status if fully settled
    settlements_query = await db.execute(select(Settlement).where(Settlement.payable_id == payable.id))
    existing_settlements = settlements_query.scalars().all()
    
    total_settled = sum((s.amount for s in existing_settlements), request.amount)
    if total_settled >= payable.grand_total:
        payable.status = PayableStatus.SETTLED
        
    await db.commit()
    await db.refresh(settlement)
    
    return settlement


@router.get("/{payable_id}/settlements", response_model=List[SettlementResponse])
async def list_settlements_for_payable(
    payable_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_org_user: AuthenticatedUser = Depends(get_current_active_organisation),
):
    # Verify ownership
    query = await db.execute(
        select(Payable).where(Payable.id == payable_id, Payable.organisation_id == current_org_user.organisation_id)
    )
    if not query.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Payable not found")
        
    s_query = await db.execute(
        select(Settlement)
        .where(Settlement.payable_id == payable_id)
        .order_by(Settlement.created_at.desc())
    )
    return s_query.scalars().all()
