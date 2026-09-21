import uuid
from typing import Optional
from dataclasses import dataclass
from app.modules.core.platform.models import ProviderType
from app.core.providers.database import D1TenantProvider

@dataclass
class TenantContext:
    organisation_id: uuid.UUID
    tenant_database_provider: ProviderType
    tenant_database_identifier: str
    mongodb_cluster_identifier: Optional[str]
    mongodb_database_name: Optional[str]
    cloudinary_prefix: Optional[str]
    r2_bucket: Optional[str]
    r2_prefix: Optional[str]
    user_id: Optional[uuid.UUID] = None

    @property
    def d1(self) -> D1TenantProvider:
        return D1TenantProvider(self.tenant_database_identifier)
