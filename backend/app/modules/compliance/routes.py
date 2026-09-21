from fastapi import APIRouter, Depends, HTTPException, status, Query, Body, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
import uuid
import datetime

from app.db.session import get_db
from app.auth.dependencies import get_current_user, require_permission
from app.modules.users.models import Profile
from app.modules.compliance.models import (
    ComplianceRequirement,
    ComplianceRecord,
    ComplianceVerification,
    ComplianceStatus,
    ComplianceVerificationAction,
    ComplianceEntityType,
)
from app.modules.compliance.schemas import (
    ComplianceRequirementCreate,
    ComplianceRequirementUpdate,
    ComplianceRequirementResponse,
    ComplianceRecordCreate,
    ComplianceRecordUpdate,
    ComplianceRecordResponse, ComplianceWaiveRequest,
    ComplianceEvaluation,
)
from app.modules.compliance.engine import ComplianceEngine

router = APIRouter(prefix="/api/v1/compliance", tags=["Compliance"])

@router.get("/requirements", response_model=List[ComplianceRequirementResponse])
async def list_requirements(
    entity_type: Optional[ComplianceEntityType] = None,
    current_user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ComplianceRequirement).where(
        (ComplianceRequirement.organisation_id == current_user.organisation_id) | (ComplianceRequirement.organisation_id.is_(None))
    )
    if entity_type:
        stmt = stmt.where(ComplianceRequirement.entity_type == entity_type)
        
    res = await db.execute(stmt)
    return res.scalars().all()

@router.post("/requirements", response_model=ComplianceRequirementResponse)
async def create_requirement(
    req: ComplianceRequirementCreate,
    current_user: Profile = Depends(require_permission("compliance.manage_rules")),
    db: AsyncSession = Depends(get_db),
):
    requirement = ComplianceRequirement(
        organisation_id=current_user.organisation_id,
        **req.model_dump()
    )
    db.add(requirement)
    await db.commit()
    await db.refresh(requirement)
    return requirement

@router.get("/records", response_model=List[ComplianceRecordResponse])
async def list_records(
    entity_type: Optional[ComplianceEntityType] = None,
    entity_id: Optional[uuid.UUID] = None,
    status: Optional[ComplianceStatus] = None,
    current_user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ComplianceRecord).where(ComplianceRecord.organisation_id == current_user.organisation_id)
    if entity_type:
        stmt = stmt.where(ComplianceRecord.entity_type == entity_type)
    if entity_id:
        stmt = stmt.where(ComplianceRecord.entity_id == entity_id)
    if status:
        stmt = stmt.where(ComplianceRecord.status == status)
        
    res = await db.execute(stmt)
    return res.scalars().all()

@router.post("/records", response_model=ComplianceRecordResponse)
async def create_or_update_record(
    req: ComplianceRecordCreate,
    current_user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ComplianceRecord).where(
        ComplianceRecord.organisation_id == current_user.organisation_id,
        ComplianceRecord.requirement_id == req.requirement_id,
        ComplianceRecord.entity_id == req.entity_id,
        ComplianceRecord.entity_type == req.entity_type,
    )
    res = await db.execute(stmt)
    record = res.scalars().first()

    if record:
        for k, v in req.model_dump(exclude_unset=True).items():
            setattr(record, k, v)
        # Reset verification if replacing document
        if req.document_url and record.status != ComplianceStatus.VALID:
            if record.requirement.verification_required:
                record.status = ComplianceStatus.VERIFICATION_REQUIRED
            else:
                record.status = ComplianceStatus.VALID
    else:
        req_obj_stmt = select(ComplianceRequirement).where(ComplianceRequirement.id == req.requirement_id)
        req_obj_res = await db.execute(req_obj_stmt)
        req_obj = req_obj_res.scalars().first()
        
        status = req.status
        if req.document_url and req_obj and req_obj.verification_required:
            status = ComplianceStatus.VERIFICATION_REQUIRED

        record = ComplianceRecord(
            organisation_id=current_user.organisation_id,
            **req.model_dump(by_alias=True)
        )
        record.status = status
        db.add(record)

    await db.commit()
    await db.refresh(record)
    return record

@router.post("/records/{record_id}/verify", response_model=ComplianceRecordResponse)
async def verify_record(
    record_id: uuid.UUID = Path(...),
    method: str = Body(default="MANUAL"),
    comments: Optional[str] = Body(default=None),
    current_user: Profile = Depends(require_permission("compliance.verify")),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ComplianceRecord).where(
        ComplianceRecord.id == record_id,
        ComplianceRecord.organisation_id == current_user.organisation_id
    )
    res = await db.execute(stmt)
    record = res.scalars().first()
    if not record:
        raise HTTPException(status_code=404, detail="Compliance record not found")

    old_status = record.status
    record.status = ComplianceStatus.VALID
    record.verified_at = datetime.datetime.now(datetime.timezone.utc)
    record.verified_by = current_user.id
    record.verification_method = method

    verif = ComplianceVerification(
        organisation_id=current_user.organisation_id,
        compliance_record_id=record.id,
        action=ComplianceVerificationAction.VERIFY,
        previous_status=old_status,
        new_status=ComplianceStatus.VALID,
        actor_id=current_user.id,
        comments=comments
    )
    db.add(verif)
    
    await db.commit()
    await db.refresh(record)
    return record

@router.get("/evaluate", response_model=ComplianceEvaluation)
async def evaluate_compliance(
    vehicle_id: Optional[uuid.UUID] = None,
    driver_id: Optional[uuid.UUID] = None,
    vendor_id: Optional[uuid.UUID] = None,
    customer_id: Optional[uuid.UUID] = None,
    service_type: Optional[str] = None,
    state_code: Optional[str] = None,
    current_user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await ComplianceEngine.evaluate(
        db=db,
        organisation_id=current_user.organisation_id,
        vehicle_id=vehicle_id,
        driver_id=driver_id,
        vendor_id=vendor_id,
        customer_id=customer_id,
        service_type=service_type,
        state_code=state_code,
    )

@router.post("/records/{record_id}/waive", response_model=ComplianceRecordResponse)
async def waive_compliance_record(
    record_id: uuid.UUID,
    waive_req: ComplianceWaiveRequest,
    current_user: Profile = Depends(require_permission("compliance.override")),
    db: AsyncSession = Depends(get_db),
):
    query = select(ComplianceRecord).filter(
        ComplianceRecord.id == record_id,
        ComplianceRecord.organisation_id == current_user.organisation_id
    )
    result = await db.execute(query)
    record = result.scalars().first()
    
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
        
    record.status = ComplianceStatus.WAIVED
    record.verified_by = current_user.id
    record.verified_at = datetime.datetime.now(datetime.timezone.utc)
    record.verification_method = "MANUAL_WAIVER"
    
    # Store reason in metadata
    meta = record.metadata_ or {}
    meta["waiver_reason"] = waive_req.reason
    meta["waived_by_email"] = current_user.email
    record.metadata_ = meta
    
    record.expiry_date = waive_req.valid_until
    
    await db.commit()
    await db.refresh(record)
    return record
