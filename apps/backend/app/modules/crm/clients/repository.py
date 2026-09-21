import uuid
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.repository import BaseTenantRepository
from .models import Client, ClientLocation

class ClientRepository(BaseTenantRepository[Client]):
    def __init__(self, db, tenant):
        super().__init__(Client, db, tenant)
        
    async def get_with_locations(self, client_id: uuid.UUID) -> Optional[Client]:
        stmt = (
            select(Client)
            .options(selectinload(Client.locations))
            .where(Client.id == client_id, self._tenant_filter())
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

class ClientLocationRepository(BaseTenantRepository[ClientLocation]):
    def __init__(self, db, tenant):
        super().__init__(ClientLocation, db, tenant)

    async def list_by_client(self, client_id: uuid.UUID) -> List[ClientLocation]:
        # Verify the client actually belongs to this tenant via a join or relying on organisation_id if it had one.
        # Since ClientLocation doesn't have an explicit organisation_id right now in our models, we have a gap!
        pass
