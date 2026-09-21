import uuid
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from app.core.tenant import TenantContext
from app.modules.crm.clients.models import Client, ClientLocation, ClientOperatingUnit, ClientLocationOUHistory
from app.modules.crm.clients.repository import ClientRepository, ClientLocationRepository, ClientOperatingUnitRepository, ClientLocationOUHistoryRepository
from app.modules.crm.clients.schemas import (
    ClientCreate, ClientUpdate, ClientLocationCreate, ClientLocationUpdate,
    ClientOURelationshipRequest, ClientLocationTransferRequest
)
from app.modules.operations.operating_units.repository import OperatingUnitRepository

class ClientService:
    def __init__(self, db: AsyncSession, tenant: TenantContext, current_user_id: uuid.UUID = None):
        self.db = db
        self.tenant = tenant
        self.current_user_id = current_user_id
        self.client_repo = ClientRepository(db, tenant)
        self.location_repo = ClientLocationRepository(db, tenant)
        self.client_ou_repo = ClientOperatingUnitRepository(db, tenant)
        self.history_repo = ClientLocationOUHistoryRepository(db, tenant)
        self.ou_repo = OperatingUnitRepository(db, tenant)

    async def list_clients(self) -> List[Client]:
        return await self.client_repo.list_all()

    async def get_client(self, client_id: uuid.UUID) -> Client:
        client = await self.client_repo.get_by_id(client_id)
        if not client:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
        return client

    async def create_client(self, data: ClientCreate) -> Client:
        try:
            return await self.client_repo.create(**data.model_dump())
        except IntegrityError:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Client code or name conflict")

    async def update_client(self, client_id: uuid.UUID, data: ClientUpdate) -> Client:
        update_data = data.model_dump(exclude_unset=True)
        try:
            client = await self.client_repo.update(client_id, **update_data)
        except IntegrityError:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Client code or name conflict")
        
        if not client:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
        return client

    # Client Locations
    async def list_locations(self, client_id: uuid.UUID) -> List[ClientLocation]:
        await self.get_client(client_id) # validate
        return await self.location_repo.list_by_client(client_id)

    async def get_location(self, client_id: uuid.UUID, location_id: uuid.UUID) -> ClientLocation:
        await self.get_client(client_id) # validate
        loc = await self.location_repo.get_by_id(location_id)
        if not loc or loc.client_id != client_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client Location not found")
        return loc

    async def create_location(self, client_id: uuid.UUID, data: ClientLocationCreate) -> ClientLocation:
        await self.get_client(client_id) # validate
        create_data = data.model_dump()
        create_data["client_id"] = client_id
        
        # Verify OU if provided
        ou_id = create_data.get("operating_unit_id")
        if ou_id:
            ou = await self.ou_repo.get_by_id(ou_id)
            if not ou:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Operating Unit not found or invalid tenant")
                
        loc = await self.location_repo.create(**create_data)
        
        # Record initial history if OU is assigned
        if ou_id:
            await self.history_repo.create(
                client_location_id=loc.id,
                previous_operating_unit_id=None,
                new_operating_unit_id=ou_id,
                actor_id=self.current_user_id,
                reason="Initial Assignment"
            )
        return loc

    async def update_location(self, client_id: uuid.UUID, location_id: uuid.UUID, data: ClientLocationUpdate) -> ClientLocation:
        await self.get_client(client_id) # validate
        # We must prevent updating operating_unit_id directly via simple update!
        # Users must use the transfer endpoint to maintain history.
        update_data = data.model_dump(exclude_unset=True)
        if "operating_unit_id" in update_data:
            update_data.pop("operating_unit_id")
            
        loc = await self.location_repo.update(location_id, **update_data)
        if not loc or loc.client_id != client_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client Location not found")
        return loc

    # Explicit Client <-> OU Relationships
    async def list_ou_relationships(self, client_id: uuid.UUID) -> List[ClientOperatingUnit]:
        await self.get_client(client_id)
        return await self.client_ou_repo.list_by_client(client_id)
        
    async def add_ou_relationship(self, client_id: uuid.UUID, data: ClientOURelationshipRequest) -> ClientOperatingUnit:
        await self.get_client(client_id)
        ou = await self.ou_repo.get_by_id(data.operating_unit_id)
        if not ou:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Operating Unit not found or invalid tenant")
            
        # check if exists
        existing = await self.client_ou_repo.get_relationship(client_id, data.operating_unit_id)
        if existing:
            return existing
            
        return await self.client_ou_repo.create(
            client_id=client_id,
            operating_unit_id=data.operating_unit_id,
            status=data.status
        )
        
    async def remove_ou_relationship(self, client_id: uuid.UUID, ou_id: uuid.UUID) -> bool:
        await self.get_client(client_id)
        rel = await self.client_ou_repo.get_relationship(client_id, ou_id)
        if not rel:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Relationship not found")
        return await self.client_ou_repo.delete(rel.id)

    # Transfers
    async def transfer_location(self, client_id: uuid.UUID, location_id: uuid.UUID, data: ClientLocationTransferRequest) -> ClientLocation:
        loc = await self.get_location(client_id, location_id)
        
        # Verify new OU
        new_ou_id = data.new_operating_unit_id
        ou = await self.ou_repo.get_by_id(new_ou_id)
        if not ou:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New Operating Unit not found or invalid tenant")
            
        prev_ou_id = loc.operating_unit_id
        if prev_ou_id == new_ou_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Location is already assigned to this Operating Unit")
            
        # 1. Update assignment
        updated_loc = await self.location_repo.update(location_id, operating_unit_id=new_ou_id)
        
        # 2. Record history
        await self.history_repo.create(
            client_location_id=location_id,
            previous_operating_unit_id=prev_ou_id,
            new_operating_unit_id=new_ou_id,
            actor_id=self.current_user_id,
            reason=data.reason or "Transfer"
        )
        
        return updated_loc
        
    async def list_location_history(self, client_id: uuid.UUID, location_id: uuid.UUID) -> List[ClientLocationOUHistory]:
        await self.get_location(client_id, location_id)
        return await self.history_repo.list_history(location_id)
