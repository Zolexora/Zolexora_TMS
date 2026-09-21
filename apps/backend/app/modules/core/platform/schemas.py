import uuid
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from .models import ProviderType, RegistryStatus

class TenantDatabaseRegistryResponse(BaseModel):
    id: uuid.UUID
    provider: ProviderType
    database_identifier: str
    database_name: str
    region: Optional[str]
    status: RegistryStatus
    schema_version: int
    assigned_organisation_id: Optional[uuid.UUID]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class ProvisionDatabaseRequest(BaseModel):
    provider: ProviderType
    database_identifier: str
    database_name: str
    region: Optional[str] = None

class AssignDatabaseRequest(BaseModel):
    organisation_id: uuid.UUID
    database_registry_id: uuid.UUID
    
class AssignMongodbRequest(BaseModel):
    organisation_id: uuid.UUID
    cluster_identifier: str
    database_name: str
    namespace_prefix: str

class AssignStorageRequest(BaseModel):
    organisation_id: uuid.UUID
    cloudinary_folder_prefix: str
    r2_bucket: str
    r2_prefix: str
