import uuid
from pydantic import BaseModel
from app.modules.core.platform.models import ProviderType

class TenantContext(BaseModel):
    organisation_id: uuid.UUID
    tenant_database_provider: ProviderType
    tenant_database_identifier: str
    mongodb_cluster_identifier: str | None = None
    mongodb_database_name: str | None = None
    cloudinary_prefix: str
    r2_bucket: str
    r2_prefix: str
    user_id: uuid.UUID
    role_code: str | None = None
    permissions: list[str] = []
