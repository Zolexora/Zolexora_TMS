import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.repository import BaseTenantRepository
from app.core.tenant import TenantContext
from app.modules.operations.operating_units.models import OperatingUnit, OperatingUnitLocation

class OperatingUnitRepository(BaseTenantRepository[OperatingUnit]):
    def __init__(self, db: AsyncSession, tenant: TenantContext):
        super().__init__(OperatingUnit, db, tenant)

class OperatingUnitLocationRepository(BaseTenantRepository[OperatingUnitLocation]):
    def __init__(self, db: AsyncSession, tenant: TenantContext):
        super().__init__(OperatingUnitLocation, db, tenant)
        
    async def list_by_operating_unit(self, operating_unit_id: uuid.UUID) -> List[OperatingUnitLocation]:
        stmt = select(self.model).where(
            self._tenant_filter(),
            self.model.operating_unit_id == operating_unit_id
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
