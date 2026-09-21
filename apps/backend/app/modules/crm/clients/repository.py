import uuid
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.repository import BaseTenantRepository
from .models import Client, ClientLocation, ClientOperatingUnit, ClientLocationOUHistory

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
        stmt = select(self.model).where(
            self.model.client_id == client_id,
            self._tenant_filter()
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

class ClientOperatingUnitRepository(BaseTenantRepository[ClientOperatingUnit]):
    def __init__(self, db, tenant):
        super().__init__(ClientOperatingUnit, db, tenant)

    async def get_relationship(self, client_id: uuid.UUID, ou_id: uuid.UUID) -> Optional[ClientOperatingUnit]:
        stmt = select(self.model).where(
            self.model.client_id == client_id,
            self.model.operating_unit_id == ou_id,
            self._tenant_filter()
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def list_by_client(self, client_id: uuid.UUID) -> List[ClientOperatingUnit]:
        stmt = select(self.model).where(
            self.model.client_id == client_id,
            self._tenant_filter()
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

class ClientLocationOUHistoryRepository(BaseTenantRepository[ClientLocationOUHistory]):
    def __init__(self, db, tenant):
        super().__init__(ClientLocationOUHistory, db, tenant)

    async def list_history(self, location_id: uuid.UUID) -> List[ClientLocationOUHistory]:
        stmt = select(self.model).where(
            self.model.client_location_id == location_id,
            self._tenant_filter()
        ).order_by(self.model.created_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
