import uuid
from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.auth.dependencies import get_current_user, get_current_active_organisation, AuthenticatedUser
from app.modules.organisations.models import Organisation
from app.modules.users.models import Profile
from app.modules.duties.models import Duty, DutyStatus
from app.modules.trips.models import Trip, TripStatus
from app.modules.billing.models import RateCardVersion, FinancialSnapshot, BillingRecord, BillingStatus
from app.modules.billing.engine import FinancialEngine

router = APIRouter(prefix="/api/v1", tags=["Billing"])

from app.modules.billing.models import RateCard, RateCardVersion, RateCardRule, RateCardSide
from app.modules.billing.schemas import RateCardCreate, RateCardResponse, RateCardVersionCreate


@router.post("/duties/{duty_id}/calculate-billing")
async def calculate_duty_billing(
    duty_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_org_user: AuthenticatedUser = Depends(get_current_active_organisation),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Evaluate a completed duty and generate a FinancialSnapshot.
    """
    # 1. Fetch Duty
    duty_query = await db.execute(
        select(Duty)
        .options(selectinload(Duty.booking))
        .where(Duty.id == duty_id, Duty.organisation_id == current_org_user.organisation_id)
    )
    duty = duty_query.scalar_one_or_none()
    
    if not duty:
        raise HTTPException(status_code=404, detail="Duty not found")
        
    if duty.status != DutyStatus.DUTY_COMPLETED:
        raise HTTPException(status_code=400, detail="Cannot calculate billing for incomplete duty")
        
    # 2. Fetch Trip (if exists)
    trip_query = await db.execute(
        select(Trip).where(Trip.duty_id == duty.id, Trip.organisation_id == current_org_user.organisation_id)
    )
    trip = trip_query.scalar_one_or_none()
    
    # 3. Check for Rate Card
    if not duty.booking.rate_card_version_id:
        raise HTTPException(status_code=400, detail="Duty booking does not have an associated rate card version")
        
    # 4. Check if already calculated and finalized
    existing_snapshot_query = await db.execute(
        select(FinancialSnapshot).where(
            FinancialSnapshot.duty_id == duty.id,
            FinancialSnapshot.is_finalized == True
        )
    )
    if existing_snapshot_query.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="A finalized financial snapshot already exists for this duty")
        
    # Fetch rate card version and rules
    rcv_query = await db.execute(
        select(RateCardVersion)
        .options(selectinload(RateCardVersion.rules))
        .where(RateCardVersion.id == duty.booking.rate_card_version_id)
    )
    rcv = rcv_query.scalar_one_or_none()
    if not rcv:
        raise HTTPException(status_code=404, detail="Rate card version not found")
        
    # Delete any existing un-finalized snapshots for this duty
    await db.execute(
        select(FinancialSnapshot).where(
            FinancialSnapshot.duty_id == duty.id,
            FinancialSnapshot.is_finalized == False
        )
    )
    # Actually delete them (simplified, need to write proper delete statement)
    unfinalized_snapshots = await db.execute(
        select(FinancialSnapshot).where(
            FinancialSnapshot.duty_id == duty.id,
            FinancialSnapshot.is_finalized == False
        )
    )
    for s in unfinalized_snapshots.scalars():
        await db.delete(s)
        
    # 5. Calculate Snapshot
    snapshot = await FinancialEngine.calculate_snapshot(
        db=db,
        duty=duty,
        trip=trip,
        rate_card_version=rcv,
        user_id=current_user.id
    )
    
    # 6. Upsert BillingRecord
    billing_record_query = await db.execute(
        select(BillingRecord).where(BillingRecord.duty_id == duty.id)
    )
    billing_record = billing_record_query.scalar_one_or_none()
    
    if not billing_record:
        billing_record = BillingRecord(
            organisation_id=current_org_user.organisation_id,
            customer_id=duty.booking.customer_id,
            duty_id=duty.id,
            snapshot_id=snapshot.id,
            status=BillingStatus.PENDING
        )
        db.add(billing_record)
    else:
        billing_record.snapshot_id = snapshot.id
        billing_record.status = BillingStatus.PENDING
        
    await db.commit()
    await db.refresh(snapshot)
    
    return {
        "snapshot_id": snapshot.id,
        "grand_total": snapshot.grand_total,
        "taxable_amount": snapshot.taxable_amount,
        "message": "Billing calculation generated successfully"
    }

@router.post("/billing/generate")
async def generate_billing(
    db: AsyncSession = Depends(get_db),
    current_org_user: AuthenticatedUser = Depends(get_current_active_organisation),
):
    """
    Background-triggerable endpoint to find all eligible COMPLETED duties and calculate them.
    In a real app, this should enqueue tasks or handle a batch.
    """
    duties_query = await db.execute(
        select(Duty)
        .options(selectinload(Duty.booking))
        .where(
            Duty.organisation_id == current_org.id,
            Duty.status == DutyStatus.DUTY_COMPLETED
        )
    )
    duties = duties_query.scalars().all()
    
    processed = 0
    errors = []
    
    for duty in duties:
        if not duty.booking.rate_card_version_id:
            continue
            
        # Check if billing record exists
        br_query = await db.execute(select(BillingRecord).where(BillingRecord.duty_id == duty.id))
        if br_query.scalar_one_or_none():
            continue # already processed
            
        try:
            trip_query = await db.execute(select(Trip).where(Trip.duty_id == duty.id))
            trip = trip_query.scalar_one_or_none()
            
            rcv_query = await db.execute(
                select(RateCardVersion)
                .options(selectinload(RateCardVersion.rules))
                .where(RateCardVersion.id == duty.booking.rate_card_version_id)
            )
            rcv = rcv_query.scalar_one_or_none()
            
            if rcv:
                snapshot = await FinancialEngine.calculate_snapshot(db, duty, trip, rcv)
                br = BillingRecord(
                    organisation_id=current_org.id,
                    customer_id=duty.booking.customer_id,
                    duty_id=duty.id,
                    snapshot_id=snapshot.id,
                    status=BillingStatus.PENDING
                )
                db.add(br)
                processed += 1
        except Exception as e:
            errors.append({"duty_id": str(duty.id), "error": str(e)})
            
    await db.commit()
    return {"processed": processed, "errors": errors}

@router.get("/billing")
async def list_billing_records(
    db: AsyncSession = Depends(get_db),
    current_org_user: AuthenticatedUser = Depends(get_current_active_organisation),
):
    """
    List all billing records, typically those pending invoice generation.
    """
    query = await db.execute(
        select(BillingRecord)
        .options(
            selectinload(BillingRecord.snapshot).selectinload(FinancialSnapshot.lines)
        )
        .where(BillingRecord.organisation_id == current_org_user.organisation_id)
        .order_by(BillingRecord.created_at.desc())
    )
    records = query.scalars().all()
    return records


@router.post("/rate-cards", response_model=RateCardResponse)
async def create_rate_card(
    payload: RateCardCreate,
    current_user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    rate_card = RateCard(
        organisation_id=current_user.organisation_id,
        name=payload.name,
        description=payload.description,
        side=RateCardSide(payload.side),
        customer_id=payload.customer_id,
        vendor_id=payload.vendor_id,
        service_type=payload.service_type,
        vehicle_category_id=payload.vehicle_category_id,
        currency=payload.currency,
        active=payload.active
    )
    
    if payload.initial_version:
        version = RateCardVersion(
            version_number=payload.initial_version.version_number,
            effective_from=payload.initial_version.effective_from,
            effective_to=payload.initial_version.effective_to,
            is_immutable=payload.initial_version.is_immutable
        )
        for rule_data in payload.initial_version.rules:
            rule = RateCardRule(**rule_data.model_dump())
            version.rules.append(rule)
        rate_card.versions.append(version)
        
    db.add(rate_card)
    await db.commit()
    await db.refresh(rate_card)
    return rate_card

@router.get("/rate-cards", response_model=List[RateCardResponse])
async def list_rate_cards(
    side: str | None = None,
    customer_id: uuid.UUID | None = None,
    vendor_id: uuid.UUID | None = None,
    current_user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(RateCard).filter(RateCard.organisation_id == current_user.organisation_id).options(selectinload(RateCard.versions).selectinload(RateCardVersion.rules))
    if side:
        query = query.filter(RateCard.side == RateCardSide(side))
    if customer_id:
        query = query.filter(RateCard.customer_id == customer_id)
    if vendor_id:
        query = query.filter(RateCard.vendor_id == vendor_id)
        
    result = await db.execute(query)
    return result.scalars().all()
