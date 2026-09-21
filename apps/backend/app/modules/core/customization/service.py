from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException
from uuid import UUID

from app.modules.core.platform.capabilities import TMS_CAPABILITY_REGISTRY

from .models import (
    OrganisationApplication,
    ApplicationModule,
    ApplicationPage,
    ApplicationAction,
    ApplicationConfiguration,
    ApplicationWorkflow,
    ApplicationRule,
    ApplicationForm,
    ApplicationReport,
    ApplicationApproval,
    ConfigType
)
from .schemas import (
    RuntimeConfiguration,
    RuntimeApplicationInfo,
    RuntimeBranding,
    RuntimeModule,
    RuntimePage,
    RuntimeAction,
    RuntimeForm,
    RuntimeWorkflow,
    RuntimeRule,
    RuntimeApproval
)

class ApplicationRuntimeService:
    @staticmethod
    async def get_runtime_configuration(db: AsyncSession, organisation_id: UUID) -> RuntimeConfiguration:
        # 1. Fetch Application Base
        result = await db.execute(
            select(OrganisationApplication).where(OrganisationApplication.organisation_id == organisation_id)
        )
        app_def = result.scalars().first()
        if not app_def:
            raise HTTPException(status_code=404, detail="Application configuration not found for this organisation")

        app_info = RuntimeApplicationInfo(
            id=app_def.id,
            name=app_def.application_name,
            type=app_def.application_type,
            version=app_def.application_version,
            status=app_def.status
        )

        # 2. Fetch Capabilities (Modules, Pages, Actions) from DB Overrides
        mod_res = await db.execute(select(ApplicationModule).where(ApplicationModule.application_id == app_def.id))
        db_modules = {m.module_code: m.is_enabled for m in mod_res.scalars().all()}

        page_res = await db.execute(select(ApplicationPage).where(ApplicationPage.application_id == app_def.id))
        db_pages = {f"{p.module_code}:{p.page_code}": p.is_enabled for p in page_res.scalars().all()}

        action_res = await db.execute(select(ApplicationAction).where(ApplicationAction.application_id == app_def.id))
        db_actions = {f"{a.page_code}:{a.action_code}": a.is_enabled for a in action_res.scalars().all()}

        # Build Canonical Tree merged with overrides
        runtime_modules = {}
        for mod in TMS_CAPABILITY_REGISTRY.modules:
            mod_enabled = db_modules.get(mod.code, True)
            
            runtime_pages = {}
            for page in mod.pages:
                page_enabled = db_pages.get(f"{mod.code}:{page.code}", True)
                
                runtime_actions = {}
                for action in page.actions:
                    action_enabled = db_actions.get(f"{page.code}:{action.code}", True)
                    runtime_actions[action.code] = RuntimeAction(
                        name=action.name,
                        enabled=action_enabled
                    )
                    
                runtime_pages[page.code] = RuntimePage(
                    name=page.name,
                    enabled=page_enabled,
                    actions=runtime_actions
                )
                
            runtime_modules[mod.code] = RuntimeModule(
                name=mod.name,
                enabled=mod_enabled,
                pages=runtime_pages
            )

        # 3. Fetch Configurations (Theme, Navigation, Terminology, etc)
        conf_res = await db.execute(select(ApplicationConfiguration).where(ApplicationConfiguration.application_id == app_def.id))
        configs = conf_res.scalars().all()
        
        branding = RuntimeBranding(application_name=app_def.application_name)
        navigation = []
        terminology = {}
        numbering = {}
        extensions = {}
        notifications = {}
        documents = {}
        
        for c in configs:
            if c.config_type == ConfigType.THEME:
                branding.theme = c.config_data.get("theme", {})
                branding.logo_url = c.config_data.get("logo_url")
            elif c.config_type == ConfigType.NAVIGATION:
                navigation = c.config_data.get("items", [])
            elif c.config_type == ConfigType.TERMINOLOGY:
                terminology = c.config_data
            elif c.config_type == ConfigType.NUMBERING:
                numbering = c.config_data
            elif c.config_type == ConfigType.EXTENSIONS:
                extensions = c.config_data
            elif c.config_type == ConfigType.NOTIFICATIONS:
                notifications = c.config_data
            elif c.config_type == ConfigType.DOCUMENT_TEMPLATES:
                documents = c.config_data

        # 4. Fetch Forms
        form_res = await db.execute(select(ApplicationForm).where(ApplicationForm.application_id == app_def.id, ApplicationForm.is_active == True))
        forms = form_res.scalars().all()
        runtime_forms = {}
        for f in forms:
            if f.entity_type not in runtime_forms:
                runtime_forms[f.entity_type] = []
            runtime_forms[f.entity_type].append(RuntimeForm(
                form_name=f.form_name,
                fields_config=f.fields_config_json,
                sections=f.sections_json
            ))

        # 5. Fetch Workflows
        wf_res = await db.execute(select(ApplicationWorkflow).where(ApplicationWorkflow.application_id == app_def.id, ApplicationWorkflow.is_active == True))
        workflows = wf_res.scalars().all()
        runtime_workflows = {}
        for w in workflows:
            if w.entity_type not in runtime_workflows:
                runtime_workflows[w.entity_type] = []
            runtime_workflows[w.entity_type].append(RuntimeWorkflow(
                workflow_name=w.workflow_name,
                definition=w.definition_json
            ))

        # 6. Fetch Rules
        rule_res = await db.execute(select(ApplicationRule).where(ApplicationRule.application_id == app_def.id, ApplicationRule.is_active == True))
        rules = rule_res.scalars().all()
        runtime_rules = {}
        for r in rules:
            if r.entity_type not in runtime_rules:
                runtime_rules[r.entity_type] = []
            runtime_rules[r.entity_type].append(RuntimeRule(
                rule_name=r.rule_name,
                conditions=r.conditions_json,
                actions=r.actions_json,
                priority=r.priority
            ))
            
        # 7. Fetch Approvals
        appr_res = await db.execute(select(ApplicationApproval).where(ApplicationApproval.application_id == app_def.id))
        approvals = appr_res.scalars().all()
        runtime_approvals = {}
        for a in approvals:
            if a.entity_type not in runtime_approvals:
                runtime_approvals[a.entity_type] = []
            runtime_approvals[a.entity_type].append(RuntimeApproval(
                approval_chain=a.approval_chain_json
            ))

        return RuntimeConfiguration(
            application=app_info,
            branding=branding,
            modules=runtime_modules,
            navigation=navigation,
            terminology=terminology,
            forms=runtime_forms,
            workflows=runtime_workflows,
            rules=runtime_rules,
            approvals=runtime_approvals,
            numbering=numbering,
            extensions=extensions,
            notifications=notifications,
            documents=documents
        )
