import uuid
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.storage import upload_document_to_r2
from app.modules.audit.models import AuditLog
from app.modules.vehicles.models import (
    Vehicle,
    VehicleBodyType,
    VehicleOperationalStatus,
    VehicleOwnershipType,
)
from app.modules.vehicles.schemas import VehicleCreate, VehicleResponse, VehicleUpdate


async def create_vehicle(
    org_id: uuid.UUID,
    actor_id: uuid.UUID,
    req: VehicleCreate,
    db: AsyncSession,
) -> VehicleResponse:
    reg_clean = req.registration_number.strip().upper().replace(" ", "")

    # Check uniqueness within tenant
    chk_stmt = select(Vehicle).where(
        Vehicle.organisation_id == org_id,
        Vehicle.registration_number == reg_clean,
    )
    chk_res = await db.execute(chk_stmt)
    if chk_res.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Vehicle '{reg_clean}' is already registered in your organisation",
        )

    vehicle = Vehicle(
        id=uuid.uuid4(),
        organisation_id=org_id,
        vendor_id=req.vendor_id,
        registration_number=reg_clean,
        vehicle_type=req.vehicle_type,
        ownership_type=req.ownership_type,
        make=req.make.strip() if req.make else None,
        model=req.model.strip() if req.model else None,
        year=req.year,
        fuel_type=req.fuel_type,
        payload_capacity_kg=req.payload_capacity_kg,
        volume_cft=req.volume_cft,
        odometer_km=req.odometer_km,
        fastag_id=req.fastag_id.strip() if req.fastag_id else None,
        gps_device_id=req.gps_device_id.strip() if req.gps_device_id else None,
        rc_number=req.rc_number.strip().upper() if req.rc_number else None,
        rc_expiry=req.rc_expiry,
        fitness_expiry=req.fitness_expiry,
        permit_expiry=req.permit_expiry,
        insurance_expiry=req.insurance_expiry,
        puc_expiry=req.puc_expiry,
        status=VehicleOperationalStatus.AVAILABLE,
        documents=req.documents,
    )
    db.add(vehicle)

    audit = AuditLog(
        id=uuid.uuid4(),
        organisation_id=org_id,
        actor_user_id=actor_id,
        action="VEHICLE_REGISTERED",
        entity_type="vehicle",
        entity_id=vehicle.id,
        metadata_={"registration_number": vehicle.registration_number, "vehicle_type": vehicle.vehicle_type.value},
    )
    db.add(audit)

    await db.commit()
    await db.refresh(vehicle)
    return VehicleResponse.model_validate(vehicle)


async def list_vehicles(
    org_id: uuid.UUID,
    db: AsyncSession,
    status_filter: Optional[VehicleOperationalStatus] = None,
    vehicle_type: Optional[VehicleBodyType] = None,
    ownership_type: Optional[VehicleOwnershipType] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> list[VehicleResponse]:
    stmt = select(Vehicle).where(Vehicle.organisation_id == org_id)

    if status_filter:
        stmt = stmt.where(Vehicle.status == status_filter)

    if vehicle_type:
        stmt = stmt.where(Vehicle.vehicle_type == vehicle_type)

    if ownership_type:
        stmt = stmt.where(Vehicle.ownership_type == ownership_type)

    if search:
        pattern = f"%{search.strip().upper()}%"
        stmt = stmt.where(Vehicle.registration_number.ilike(pattern) | Vehicle.make.ilike(pattern) | Vehicle.model.ilike(pattern))

    stmt = stmt.order_by(desc(Vehicle.created_at)).offset(skip).limit(limit)
    res = await db.execute(stmt)
    rows = res.scalars().all()
    return [VehicleResponse.model_validate(r) for r in rows]


async def get_vehicle(
    org_id: uuid.UUID,
    vehicle_id: uuid.UUID,
    db: AsyncSession,
) -> VehicleResponse:
    stmt = select(Vehicle).where(
        Vehicle.id == vehicle_id,
        Vehicle.organisation_id == org_id,
    )
    res = await db.execute(stmt)
    vehicle = res.scalars().first()
    if not vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
    return VehicleResponse.model_validate(vehicle)


async def update_vehicle(
    org_id: uuid.UUID,
    vehicle_id: uuid.UUID,
    actor_id: uuid.UUID,
    req: VehicleUpdate,
    db: AsyncSession,
) -> VehicleResponse:
    stmt = select(Vehicle).where(
        Vehicle.id == vehicle_id,
        Vehicle.organisation_id == org_id,
    )
    res = await db.execute(stmt)
    vehicle = res.scalars().first()
    if not vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")

    update_data = req.model_dump(exclude_unset=True)
    if "registration_number" in update_data and update_data["registration_number"]:
        reg_clean = update_data["registration_number"].strip().upper().replace(" ", "")
        vehicle.registration_number = reg_clean

    for field, val in update_data.items():
        if field == "registration_number":
            continue
        if val is not None and isinstance(val, str):
            val = val.strip()
            if field in ("rc_number", "fastag_id", "gps_device_id"):
                val = val.upper()
        setattr(vehicle, field, val)

    audit = AuditLog(
        id=uuid.uuid4(),
        organisation_id=org_id,
        actor_user_id=actor_id,
        action="VEHICLE_UPDATED",
        entity_type="vehicle",
        entity_id=vehicle.id,
        metadata_={"updated_fields": list(update_data.keys())},
    )
    db.add(audit)

    await db.commit()
    await db.refresh(vehicle)
    return VehicleResponse.model_validate(vehicle)


async def delete_vehicle(
    org_id: uuid.UUID,
    vehicle_id: uuid.UUID,
    actor_id: uuid.UUID,
    db: AsyncSession,
) -> None:
    stmt = select(Vehicle).where(
        Vehicle.id == vehicle_id,
        Vehicle.organisation_id == org_id,
    )
    res = await db.execute(stmt)
    vehicle = res.scalars().first()
    if not vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")

    vehicle.status = VehicleOperationalStatus.DECOMMISSIONED
    audit = AuditLog(
        id=uuid.uuid4(),
        organisation_id=org_id,
        actor_user_id=actor_id,
        action="VEHICLE_DECOMMISSIONED",
        entity_type="vehicle",
        entity_id=vehicle.id,
        metadata_={"registration_number": vehicle.registration_number},
    )
    db.add(audit)
    await db.commit()


async def upload_vehicle_doc(
    org_id: uuid.UUID,
    vehicle_id: uuid.UUID,
    doc_type: str,
    file_name: str,
    file_bytes: bytes,
    content_type: str,
    db: AsyncSession,
) -> str:
    stmt = select(Vehicle).where(Vehicle.id == vehicle_id, Vehicle.organisation_id == org_id)
    res = await db.execute(stmt)
    vehicle = res.scalars().first()
    if not vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")

    url = await upload_document_to_r2(
        file_bytes=file_bytes,
        file_name=file_name,
        content_type=content_type,
        folder=f"tenants/{org_id}/vehicles/{vehicle_id}",
    )
    docs = dict(vehicle.documents)
    docs[doc_type] = url
    vehicle.documents = docs
    await db.commit()
    return url
