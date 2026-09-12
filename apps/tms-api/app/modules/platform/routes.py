import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.auth.dependencies import AuthenticatedUser, require_platform_admin
from .models import (
    TenantDatabaseRegistry,
    OrganisationDatabaseAssignment,
    TenantMongodbRegistry,
    OrganisationMongodbAssignment,
    OrganisationStorageAssignment,
    PlatformAuditLog,
    RegistryStatus,
    ProviderType
)
from .schemas import (
    TenantDatabaseRegistryResponse,
    ProvisionDatabaseRequest,
    AssignDatabaseRequest,
    AssignMongodbRequest,
    AssignStorageRequest
)

router = APIRouter(prefix="/platform/tenants", tags=["Platform Tenant Management"])

@router.post("/databases", response_model=TenantDatabaseRegistryResponse, status_code=status.HTTP_201_CREATED)
async def provision_database(
    request: ProvisionDatabaseRequest,
    db: AsyncSession = Depends(get_db),
    admin: AuthenticatedUser = Depends(require_platform_admin)
):
    query = await db.execute(select(TenantDatabaseRegistry).where(TenantDatabaseRegistry.database_identifier == request.database_identifier))
    if query.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Database identifier already exists")
        
    registry = TenantDatabaseRegistry(
        provider=request.provider,
        database_identifier=request.database_identifier,
        database_name=request.database_name,
        region=request.region,
        status=RegistryStatus.AVAILABLE
    )
    db.add(registry)
    
    # Audit log
    audit = PlatformAuditLog(
        user_id=admin.id,
        event_type="TENANT_DATABASE_PROVISIONED",
        entity_type="tenant_database_registry",
        payload=f"Provisioned {request.provider.value} db {request.database_identifier}"
    )
    db.add(audit)
    
    await db.commit()
    await db.refresh(registry)
    return registry

@router.post("/databases/assign")
async def assign_database(
    request: AssignDatabaseRequest,
    db: AsyncSession = Depends(get_db),
    admin: AuthenticatedUser = Depends(require_platform_admin)
):
    # Check org doesn't already have one
    query = await db.execute(select(OrganisationDatabaseAssignment).where(OrganisationDatabaseAssignment.organisation_id == request.organisation_id))
    if query.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Organisation already has an assigned database")
        
    db_reg_query = await db.execute(select(TenantDatabaseRegistry).where(TenantDatabaseRegistry.id == request.database_registry_id))
    db_reg = db_reg_query.scalar_one_or_none()
    if not db_reg:
        raise HTTPException(status_code=404, detail="Database registry not found")
        
    if db_reg.status != RegistryStatus.AVAILABLE:
        raise HTTPException(status_code=400, detail=f"Database is not available for assignment (status: {db_reg.status})")
        
    assignment = OrganisationDatabaseAssignment(
        organisation_id=request.organisation_id,
        database_registry_id=request.database_registry_id,
        assignment_status="ACTIVE",
        provisioning_status="READY"
    )
    db.add(assignment)
    
    db_reg.status = RegistryStatus.ASSIGNED
    db_reg.assigned_organisation_id = request.organisation_id
    
    audit = PlatformAuditLog(
        user_id=admin.id,
        organisation_id=request.organisation_id,
        event_type="TENANT_DATABASE_ASSIGNED",
        entity_type="organisation_database_assignments",
        payload=f"Assigned database {db_reg.database_identifier} to org {request.organisation_id}"
    )
    db.add(audit)
    
    await db.commit()
    return {"message": "Database assigned successfully"}

@router.post("/mongodb/assign")
async def assign_mongodb(
    request: AssignMongodbRequest,
    db: AsyncSession = Depends(get_db),
    admin: AuthenticatedUser = Depends(require_platform_admin)
):
    # check existing
    query = await db.execute(select(OrganisationMongodbAssignment).where(OrganisationMongodbAssignment.organisation_id == request.organisation_id))
    if query.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Organisation already has a MongoDB assignment")
        
    # ensure registry exists or create on fly (for simplicity in this phase)
    mr_query = await db.execute(select(TenantMongodbRegistry).where(TenantMongodbRegistry.cluster_identifier == request.cluster_identifier))
    mr = mr_query.scalar_one_or_none()
    if not mr:
        mr = TenantMongodbRegistry(
            cluster_identifier=request.cluster_identifier,
            database_name=request.database_name,
            status=RegistryStatus.AVAILABLE
        )
        db.add(mr)
        await db.commit()
        await db.refresh(mr)
        
    assignment = OrganisationMongodbAssignment(
        organisation_id=request.organisation_id,
        mongodb_registry_id=mr.id,
        database_name=request.database_name,
        namespace_prefix=request.namespace_prefix
    )
    db.add(assignment)
    
    audit = PlatformAuditLog(
        user_id=admin.id,
        organisation_id=request.organisation_id,
        event_type="MONGODB_TENANT_ASSIGNED",
        payload=f"Assigned MongoDB {request.cluster_identifier} namespace {request.namespace_prefix}"
    )
    db.add(audit)
    
    await db.commit()
    return {"message": "MongoDB assigned successfully"}

@router.post("/storage/assign")
async def assign_storage(
    request: AssignStorageRequest,
    db: AsyncSession = Depends(get_db),
    admin: AuthenticatedUser = Depends(require_platform_admin)
):
    query = await db.execute(select(OrganisationStorageAssignment).where(OrganisationStorageAssignment.organisation_id == request.organisation_id))
    if query.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Organisation already has a storage assignment")
        
    assignment = OrganisationStorageAssignment(
        organisation_id=request.organisation_id,
        cloudinary_folder_prefix=request.cloudinary_folder_prefix,
        r2_bucket=request.r2_bucket,
        r2_prefix=request.r2_prefix
    )
    db.add(assignment)
    
    audit = PlatformAuditLog(
        user_id=admin.id,
        organisation_id=request.organisation_id,
        event_type="STORAGE_PREFIX_CREATED",
        payload=f"Assigned Storage R2 {request.r2_bucket}/{request.r2_prefix}"
    )
    db.add(audit)
    
    await db.commit()
    return {"message": "Storage assigned successfully"}

