from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any

from app.db.session import get_db
from app.auth.dependencies import get_current_active_organisation, AuthenticatedUser
from app.modules.organisations.models import Organisation
from .models import (
    OrganisationApplication,
    ApplicationModule,
    ApplicationConfiguration,
    ApplicationWorkflow,
    ApplicationRule,
    ApplicationForm,
    ApplicationReport,
    ApplicationApproval
)

router = APIRouter(prefix="/api/v1/application", tags=["Application Configuration"])

@router.get("")
async def get_application_definition(
    user: AuthenticatedUser = Depends(get_current_active_organisation),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the overall application definition for the current organisation.
    """
    result = await db.execute(
        select(OrganisationApplication).where(OrganisationApplication.organisation_id == user.organisation_id)
    )
    app_def = result.scalars().first()
    
    if not app_def:
        raise HTTPException(status_code=404, detail="Application configuration not found for this organisation")
        
    return {
        "id": app_def.id,
        "application_type": app_def.application_type,
        "application_name": app_def.application_name,
        "application_version": app_def.application_version,
        "status": app_def.status,
    }

@router.get("/modules")
async def get_application_modules(
    user: AuthenticatedUser = Depends(get_current_active_organisation),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(ApplicationModule).join(OrganisationApplication).where(OrganisationApplication.organisation_id == user.organisation_id)
    )
    modules = result.scalars().all()
    return [{"module_code": m.module_code, "is_enabled": m.is_enabled} for m in modules]

@router.get("/configuration")
async def get_application_configurations(
    user: AuthenticatedUser = Depends(get_current_active_organisation),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(ApplicationConfiguration).join(OrganisationApplication).where(OrganisationApplication.organisation_id == user.organisation_id)
    )
    configs = result.scalars().all()
    return [{"config_type": c.config_type, "config_data": c.config_data} for c in configs]

@router.get("/forms")
async def get_application_forms(
    user: AuthenticatedUser = Depends(get_current_active_organisation),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(ApplicationForm).join(OrganisationApplication).where(OrganisationApplication.organisation_id == user.organisation_id)
    )
    forms = result.scalars().all()
    return [{
        "entity_type": f.entity_type,
        "form_name": f.form_name,
        "fields_config": f.fields_config_json,
        "sections": f.sections_json
    } for f in forms]

@router.get("/workflows")
async def get_application_workflows(
    user: AuthenticatedUser = Depends(get_current_active_organisation),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(ApplicationWorkflow).join(OrganisationApplication).where(OrganisationApplication.organisation_id == user.organisation_id)
    )
    workflows = result.scalars().all()
    return [{
        "entity_type": w.entity_type,
        "workflow_name": w.workflow_name,
        "definition": w.definition_json
    } for w in workflows]

@router.get("/rules")
async def get_application_rules(
    user: AuthenticatedUser = Depends(get_current_active_organisation),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(ApplicationRule).join(OrganisationApplication).where(OrganisationApplication.organisation_id == user.organisation_id)
    )
    rules = result.scalars().all()
    return [{
        "entity_type": r.entity_type,
        "rule_name": r.rule_name,
        "conditions": r.conditions_json,
        "actions": r.actions_json,
        "priority": r.priority
    } for r in rules]
