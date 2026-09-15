from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from uuid import UUID
from .models import ApplicationType, ApplicationStatus

class RuntimeApplicationInfo(BaseModel):
    id: UUID
    name: str
    type: ApplicationType
    version: str
    status: ApplicationStatus

class RuntimeBranding(BaseModel):
    application_name: str
    logo_url: Optional[str] = None
    theme: Dict[str, Any] = {}

class RuntimeModule(BaseModel):
    enabled: bool

class RuntimeForm(BaseModel):
    form_name: str
    fields_config: Dict[str, Any] = {}
    sections: Dict[str, Any] = {}
    
class RuntimeWorkflow(BaseModel):
    workflow_name: str
    definition: Dict[str, Any] = {}
    
class RuntimeRule(BaseModel):
    rule_name: str
    conditions: Dict[str, Any] = {}
    actions: Dict[str, Any] = {}
    priority: int
    
class RuntimeApproval(BaseModel):
    approval_chain: Dict[str, Any] = {}

class RuntimeConfiguration(BaseModel):
    application: RuntimeApplicationInfo
    branding: RuntimeBranding
    modules: Dict[str, RuntimeModule] = {}
    features: Dict[str, Any] = {}
    navigation: List[Dict[str, Any]] = []
    terminology: Dict[str, str] = {}
    forms: Dict[str, List[RuntimeForm]] = {}
    workflows: Dict[str, List[RuntimeWorkflow]] = {}
    rules: Dict[str, List[RuntimeRule]] = {}
    approvals: Dict[str, List[RuntimeApproval]] = {}
    dashboard: Dict[str, Any] = {}
    reports: Dict[str, Any] = {}
    notifications: Dict[str, Any] = {}
    documents: Dict[str, Any] = {}
    numbering: Dict[str, Any] = {}
    extensions: Dict[str, Any] = {}
