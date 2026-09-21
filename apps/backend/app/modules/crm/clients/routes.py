import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.auth.dependencies import get_tenant_context, get_current_user, AuthenticatedUser
from app.core.tenant import TenantContext
from app.modules.crm.clients.schemas import (
    ClientCreate, ClientUpdate, ClientResponse,
    ClientLocationCreate, ClientLocationUpdate, ClientLocationResponse,
    ClientOURelationshipRequest, ClientOURelationshipResponse,
    ClientLocationTransferRequest, ClientLocationOUHistoryResponse
)
from app.modules.crm.clients.service import ClientService

router = APIRouter(prefix="/api/v1/crm/clients", tags=["Clients"])

def get_client_service(
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(get_tenant_context),
    user: AuthenticatedUser = Depends(get_current_user)
) -> ClientService:
    return ClientService(db, tenant, user.id)

@router.get("", response_model=List[ClientResponse])
async def list_clients(service: ClientService = Depends(get_client_service)):
    return await service.list_clients()

@router.post("", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(data: ClientCreate, service: ClientService = Depends(get_client_service)):
    return await service.create_client(data)

@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(client_id: uuid.UUID, service: ClientService = Depends(get_client_service)):
    return await service.get_client(client_id)

@router.patch("/{client_id}", response_model=ClientResponse)
async def update_client(client_id: uuid.UUID, data: ClientUpdate, service: ClientService = Depends(get_client_service)):
    return await service.update_client(client_id, data)

# Client Locations
@router.get("/{client_id}/locations", response_model=List[ClientLocationResponse])
async def list_locations(client_id: uuid.UUID, service: ClientService = Depends(get_client_service)):
    return await service.list_locations(client_id)

@router.post("/{client_id}/locations", response_model=ClientLocationResponse, status_code=status.HTTP_201_CREATED)
async def create_location(client_id: uuid.UUID, data: ClientLocationCreate, service: ClientService = Depends(get_client_service)):
    return await service.create_location(client_id, data)

@router.get("/{client_id}/locations/{location_id}", response_model=ClientLocationResponse)
async def get_location(client_id: uuid.UUID, location_id: uuid.UUID, service: ClientService = Depends(get_client_service)):
    return await service.get_location(client_id, location_id)

@router.patch("/{client_id}/locations/{location_id}", response_model=ClientLocationResponse)
async def update_location(client_id: uuid.UUID, location_id: uuid.UUID, data: ClientLocationUpdate, service: ClientService = Depends(get_client_service)):
    return await service.update_location(client_id, location_id, data)

# Transfers & History
@router.post("/{client_id}/locations/{location_id}/transfer", response_model=ClientLocationResponse)
async def transfer_location(client_id: uuid.UUID, location_id: uuid.UUID, data: ClientLocationTransferRequest, service: ClientService = Depends(get_client_service)):
    return await service.transfer_location(client_id, location_id, data)

@router.get("/{client_id}/locations/{location_id}/history", response_model=List[ClientLocationOUHistoryResponse])
async def get_location_history(client_id: uuid.UUID, location_id: uuid.UUID, service: ClientService = Depends(get_client_service)):
    return await service.list_location_history(client_id, location_id)

# Relationships
@router.get("/{client_id}/operating-units", response_model=List[ClientOURelationshipResponse])
async def list_ou_relationships(client_id: uuid.UUID, service: ClientService = Depends(get_client_service)):
    return await service.list_ou_relationships(client_id)

@router.post("/{client_id}/operating-units", response_model=ClientOURelationshipResponse)
async def add_ou_relationship(client_id: uuid.UUID, data: ClientOURelationshipRequest, service: ClientService = Depends(get_client_service)):
    return await service.add_ou_relationship(client_id, data)

@router.delete("/{client_id}/operating-units/{ou_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_ou_relationship(client_id: uuid.UUID, ou_id: uuid.UUID, service: ClientService = Depends(get_client_service)):
    await service.remove_ou_relationship(client_id, ou_id)
