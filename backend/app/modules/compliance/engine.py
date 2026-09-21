import uuid
import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_, and_
from typing import Optional, List, Dict
from app.modules.compliance.models import ComplianceRequirement, ComplianceRecord, ComplianceStatus, ComplianceEntityType
from app.modules.compliance.schemas import ComplianceEvaluation, ComplianceIssue

class ComplianceEngine:
    @staticmethod
    async def evaluate(
        db: AsyncSession,
        organisation_id: uuid.UUID,
        service_type: Optional[str] = None,
        vehicle_id: Optional[uuid.UUID] = None,
        driver_id: Optional[uuid.UUID] = None,
        vendor_id: Optional[uuid.UUID] = None,
        customer_id: Optional[uuid.UUID] = None,
        state_code: Optional[str] = None,
    ) -> ComplianceEvaluation:
        entities = {}
        if vehicle_id:
            entities[ComplianceEntityType.VEHICLE] = vehicle_id
        if driver_id:
            entities[ComplianceEntityType.DRIVER] = driver_id
        if vendor_id:
            entities[ComplianceEntityType.VENDOR] = vendor_id
        if customer_id:
            entities[ComplianceEntityType.CUSTOMER] = customer_id
        
        entities[ComplianceEntityType.ORGANISATION] = organisation_id

        stmt = select(ComplianceRequirement).where(
            ComplianceRequirement.active == True,
            or_(
                ComplianceRequirement.organisation_id == organisation_id,
                ComplianceRequirement.organisation_id.is_(None)
            )
        )
        res = await db.execute(stmt)
        requirements = res.scalars().all()

        applicable_reqs = []
        for req in requirements:
            if req.entity_type not in entities:
                continue
            
            if req.conditions:
                if req.conditions.get("service_type") and service_type and req.conditions["service_type"] != service_type:
                    continue
                if req.conditions.get("state") and state_code and req.conditions["state"] != state_code:
                    continue
                
            applicable_reqs.append(req)

        if not applicable_reqs:
            return ComplianceEvaluation(status="PASS")

        req_ids = [r.id for r in applicable_reqs]
        record_stmt = select(ComplianceRecord).where(
            ComplianceRecord.organisation_id == organisation_id,
            ComplianceRecord.requirement_id.in_(req_ids),
            ComplianceRecord.entity_id.in_(list(entities.values()))
        )
        res = await db.execute(record_stmt)
        records = res.scalars().all()
        record_map = {(r.requirement_id, r.entity_id): r for r in records}

        evaluation = ComplianceEvaluation(status="PASS")
        
        warning_threshold = datetime.date.today() + datetime.timedelta(days=30)
        today = datetime.date.today()

        for req in applicable_reqs:
            entity_id = entities[req.entity_type]
            record = record_map.get((req.id, entity_id))
            
            evaluation.rule_versions.append(req.id)
            
            if not record:
                if req.mandatory:
                    issue = ComplianceIssue(
                        code=f"{req.code}_MISSING",
                        category=req.category,
                        severity="BLOCK" if req.blocking else "WARNING",
                        entity_type=req.entity_type,
                        entity_id=entity_id,
                        requirement_id=req.id,
                        message=f"Missing mandatory requirement: {req.name}"
                    )
                    if req.blocking:
                        evaluation.blocking_issues.append(issue)
                    else:
                        evaluation.warnings.append(issue)
                    evaluation.missing_requirements.append(req.id)
                continue
            
            actual_status = record.status
            if record.expiry_date:
                if record.expiry_date < today:
                    actual_status = ComplianceStatus.EXPIRED
                elif record.expiry_date <= warning_threshold and actual_status == ComplianceStatus.VALID:
                    actual_status = ComplianceStatus.EXPIRING_SOON

            if actual_status in [ComplianceStatus.MISSING, ComplianceStatus.EXPIRED, ComplianceStatus.REJECTED]:
                issue = ComplianceIssue(
                    code=f"{req.code}_{actual_status.value}",
                    category=req.category,
                    severity="BLOCK" if req.blocking else "WARNING",
                    entity_type=req.entity_type,
                    entity_id=entity_id,
                    requirement_id=req.id,
                    message=f"Requirement {req.name} is {actual_status.value}",
                    document_id=record.document_url,
                    expires_at=record.expiry_date
                )
                if req.blocking:
                    evaluation.blocking_issues.append(issue)
                else:
                    evaluation.warnings.append(issue)
                    
                if actual_status == ComplianceStatus.EXPIRED:
                    evaluation.expired_requirements.append(req.id)
                elif actual_status == ComplianceStatus.MISSING:
                    evaluation.missing_requirements.append(req.id)

            elif actual_status == ComplianceStatus.VERIFICATION_REQUIRED:
                if req.blocking:
                    evaluation.blocking_issues.append(
                        ComplianceIssue(
                            code=f"{req.code}_VERIFICATION_REQUIRED",
                            category=req.category,
                            severity="BLOCK",
                            entity_type=req.entity_type,
                            entity_id=entity_id,
                            requirement_id=req.id,
                            message=f"Requirement {req.name} is pending verification",
                        )
                    )
                evaluation.verification_required.append(req.id)

            elif actual_status == ComplianceStatus.EXPIRING_SOON:
                evaluation.warnings.append(
                    ComplianceIssue(
                        code=f"{req.code}_EXPIRING_SOON",
                        category=req.category,
                        severity="WARNING",
                        entity_type=req.entity_type,
                        entity_id=entity_id,
                        requirement_id=req.id,
                        message=f"Requirement {req.name} is expiring on {record.expiry_date}",
                        document_id=record.document_url,
                        expires_at=record.expiry_date
                    )
                )
                evaluation.valid_requirements.append(req.id)

            elif actual_status in [ComplianceStatus.VALID, ComplianceStatus.WAIVED]:
                evaluation.valid_requirements.append(req.id)

        if evaluation.blocking_issues:
            evaluation.status = "BLOCK"
        elif evaluation.warnings:
            evaluation.status = "WARNING"
            
        return evaluation
