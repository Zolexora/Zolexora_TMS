import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.auth.dependencies import get_tenant_context
from app.core.tenant import TenantContext
from app.modules.operations.operating_units.schemas import (
    OperatingUnitCreate, OperatingUnitUpdate, OperatingUnitResponse,
    OperatingUnitLocationCreate, OperatingUnitLocationUpdate, OperatingUnitLocationResponse
)
from app.modules.operations.operating_units.service import OperatingUnitService

router = APIRouter(prefix="/api/v1/operations/operating-units", tags=["Operating Units"])

def get_ou_service(
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(get_tenant_context)
) -> OperatingUnitService:
    return OperatingUnitService(db, tenant)

@router.get("", response_model=List[OperatingUnitResponse])
async def list_operating_units(service: OperatingUnitService = Depends(get_ou_service)):
    return await service.list_operating_units()

@router.post("", response_model=OperatingUnitResponse, status_code=status.HTTP_201_CREATED)
async def create_operating_unit(data: OperatingUnitCreate, service: OperatingUnitService = Depends(get_ou_service)):
    return await service.create_operating_unit(data)

@router.get("/{ou_id}", response_model=OperatingUnitResponse)
async def get_operating_unit(ou_id: uuid.UUID, service: OperatingUnitService = Depends(get_ou_service)):
    return await service.get_operating_unit(ou_id)

@router.patch("/{ou_id}", response_model=OperatingUnitResponse)
async def update_operating_unit(ou_id: uuid.UUID, data: OperatingUnitUpdate, service: OperatingUnitService = Depends(get_ou_service)):
    return await service.update_operating_unit(ou_id, data)

@router.get("/{ou_id}/locations", response_model=List[OperatingUnitLocationResponse])
async def list_ou_locations(ou_id: uuid.UUID, service: OperatingUnitService = Depends(get_ou_service)):
    return await service.list_locations(ou_id)

@router.post("/{ou_id}/locations", response_model=OperatingUnitLocationResponse, status_code=status.HTTP_201_CREATED)
async def create_ou_location(ou_id: uuid.UUID, data: OperatingUnitLocationCreate, service: OperatingUnitService = Depends(get_ou_service)):
    return await service.create_location(ou_id, data)

@router.patch("/{ou_id}/locations/{location_id}", response_model=OperatingUnitLocationResponse)
async def update_ou_location(ou_id: uuid.UUID, location_id: uuid.UUID, data: OperatingUnitLocationUpdate, service: OperatingUnitService = Depends(get_ou_service)):
    return await service.update_location(ou_id, location_id, data)
