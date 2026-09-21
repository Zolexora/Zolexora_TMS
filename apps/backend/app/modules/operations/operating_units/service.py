import uuid
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from app.core.tenant import TenantContext
from app.modules.operations.operating_units.models import OperatingUnit, OperatingUnitLocation
from app.modules.operations.operating_units.repository import OperatingUnitRepository, OperatingUnitLocationRepository
from app.modules.operations.operating_units.schemas import OperatingUnitCreate, OperatingUnitUpdate, OperatingUnitLocationCreate, OperatingUnitLocationUpdate

class OperatingUnitService:
    def __init__(self, db: AsyncSession, tenant: TenantContext):
        self.ou_repo = OperatingUnitRepository(db, tenant)
        self.location_repo = OperatingUnitLocationRepository(db, tenant)

    async def list_operating_units(self) -> List[OperatingUnit]:
        return await self.ou_repo.list_all()

    async def get_operating_unit(self, ou_id: uuid.UUID) -> OperatingUnit:
        ou = await self.ou_repo.get_by_id(ou_id)
        if not ou:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Operating Unit not found")
        return ou

    async def create_operating_unit(self, data: OperatingUnitCreate) -> OperatingUnit:
        try:
            return await self.ou_repo.create(**data.model_dump())
        except IntegrityError:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Operating Unit with this code already exists")

    async def update_operating_unit(self, ou_id: uuid.UUID, data: OperatingUnitUpdate) -> OperatingUnit:
        update_data = data.model_dump(exclude_unset=True)
        try:
            ou = await self.ou_repo.update(ou_id, **update_data)
        except IntegrityError:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Operating Unit code conflict")
        
        if not ou:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Operating Unit not found")
        return ou

    async def list_locations(self, ou_id: uuid.UUID) -> List[OperatingUnitLocation]:
        # Validate OU exists and belongs to tenant
        await self.get_operating_unit(ou_id)
        return await self.location_repo.list_by_operating_unit(ou_id)

    async def create_location(self, ou_id: uuid.UUID, data: OperatingUnitLocationCreate) -> OperatingUnitLocation:
        # Validate OU exists and belongs to tenant
        await self.get_operating_unit(ou_id)
        create_data = data.model_dump()
        create_data["operating_unit_id"] = ou_id
        try:
            return await self.location_repo.create(**create_data)
        except IntegrityError:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Location with this code already exists for this OU")

    async def update_location(self, ou_id: uuid.UUID, location_id: uuid.UUID, data: OperatingUnitLocationUpdate) -> OperatingUnitLocation:
        # Validate OU exists and belongs to tenant
        await self.get_operating_unit(ou_id)
        
        # Verify location belongs to OU
        loc = await self.location_repo.get_by_id(location_id)
        if not loc or loc.operating_unit_id != ou_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found for this Operating Unit")
            
        update_data = data.model_dump(exclude_unset=True)
        try:
            updated_loc = await self.location_repo.update(location_id, **update_data)
            return updated_loc
        except IntegrityError:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Location code conflict")
