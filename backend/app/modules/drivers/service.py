import uuid
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.storage import upload_image_to_cloudinary, upload_document_to_r2
from app.modules.audit.models import AuditLog
from app.modules.drivers.models import Driver, DriverStatus, DriverType
from app.modules.drivers.schemas import DriverCreate, DriverResponse, DriverUpdate


async def create_driver(
    org_id: uuid.UUID,
    actor_id: uuid.UUID,
    req: DriverCreate,
    db: AsyncSession,
) -> DriverResponse:
    # Check uniqueness within tenant
    chk_stmt = select(Driver).where(
        Driver.organisation_id == org_id,
        (Driver.phone == req.phone.strip()) | (Driver.license_number == req.license_number.strip().upper()),
    )
    chk_res = await db.execute(chk_stmt)
    if chk_res.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A driver with this phone number or license number is already registered in your organisation",
        )

    driver = Driver(
        id=uuid.uuid4(),
        organisation_id=org_id,
        vendor_id=req.vendor_id,
        full_name=req.full_name.strip(),
        phone=req.phone.strip(),
        alternate_phone=req.alternate_phone.strip() if req.alternate_phone else None,
        email=req.email,
        license_number=req.license_number.strip().upper(),
        license_type=req.license_type.strip().upper(),
        license_expiry=req.license_expiry,
        badge_number=req.badge_number.strip().upper() if req.badge_number else None,
        aadhaar_last4=req.aadhaar_last4,
        pan=req.pan.strip().upper() if req.pan else None,
        driver_type=req.driver_type,
        status=DriverStatus.AVAILABLE,
        avatar_url=req.avatar_url,
        documents=req.documents,
    )
    db.add(driver)

    audit = AuditLog(
        id=uuid.uuid4(),
        organisation_id=org_id,
        actor_user_id=actor_id,
        action="DRIVER_CREATED",
        entity_type="driver",
        entity_id=driver.id,
        metadata_={"driver_name": driver.full_name, "license": driver.license_number},
    )
    db.add(audit)

    await db.commit()
    await db.refresh(driver)
    return DriverResponse.model_validate(driver)


async def list_drivers(
    org_id: uuid.UUID,
    db: AsyncSession,
    status_filter: Optional[DriverStatus] = None,
    driver_type: Optional[DriverType] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> list[DriverResponse]:
    stmt = select(Driver).where(Driver.organisation_id == org_id)

    if status_filter:
        stmt = stmt.where(Driver.status == status_filter)

    if driver_type:
        stmt = stmt.where(Driver.driver_type == driver_type)

    if search:
        pattern = f"%{search.strip()}%"
        stmt = stmt.where(Driver.full_name.ilike(pattern) | Driver.phone.ilike(pattern) | Driver.license_number.ilike(pattern))

    stmt = stmt.order_by(desc(Driver.created_at)).offset(skip).limit(limit)
    res = await db.execute(stmt)
    rows = res.scalars().all()
    return [DriverResponse.model_validate(r) for r in rows]


async def get_driver(
    org_id: uuid.UUID,
    driver_id: uuid.UUID,
    db: AsyncSession,
) -> DriverResponse:
    stmt = select(Driver).where(
        Driver.id == driver_id,
        Driver.organisation_id == org_id,
    )
    res = await db.execute(stmt)
    driver = res.scalars().first()
    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")
    return DriverResponse.model_validate(driver)


async def update_driver(
    org_id: uuid.UUID,
    driver_id: uuid.UUID,
    actor_id: uuid.UUID,
    req: DriverUpdate,
    db: AsyncSession,
) -> DriverResponse:
    stmt = select(Driver).where(
        Driver.id == driver_id,
        Driver.organisation_id == org_id,
    )
    res = await db.execute(stmt)
    driver = res.scalars().first()
    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")

    update_data = req.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        if val is not None and isinstance(val, str):
            val = val.strip()
            if field in ("license_number", "license_type", "badge_number", "pan"):
                val = val.upper()
        setattr(driver, field, val)

    audit = AuditLog(
        id=uuid.uuid4(),
        organisation_id=org_id,
        actor_user_id=actor_id,
        action="DRIVER_UPDATED",
        entity_type="driver",
        entity_id=driver.id,
        metadata_={"updated_fields": list(update_data.keys())},
    )
    db.add(audit)

    await db.commit()
    await db.refresh(driver)
    return DriverResponse.model_validate(driver)


async def delete_driver(
    org_id: uuid.UUID,
    driver_id: uuid.UUID,
    actor_id: uuid.UUID,
    db: AsyncSession,
) -> None:
    stmt = select(Driver).where(
        Driver.id == driver_id,
        Driver.organisation_id == org_id,
    )
    res = await db.execute(stmt)
    driver = res.scalars().first()
    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")

    driver.status = DriverStatus.INACTIVE
    audit = AuditLog(
        id=uuid.uuid4(),
        organisation_id=org_id,
        actor_user_id=actor_id,
        action="DRIVER_DEACTIVATED",
        entity_type="driver",
        entity_id=driver.id,
        metadata_={"driver_name": driver.full_name},
    )
    db.add(audit)
    await db.commit()


async def upload_driver_avatar(
    org_id: uuid.UUID,
    driver_id: uuid.UUID,
    file_bytes: bytes,
    db: AsyncSession,
) -> str:
    stmt = select(Driver).where(Driver.id == driver_id, Driver.organisation_id == org_id)
    res = await db.execute(stmt)
    driver = res.scalars().first()
    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")

    url = await upload_image_to_cloudinary(file_bytes, folder=f"zolexora/{org_id}/drivers")
    driver.avatar_url = url
    await db.commit()
    return url


async def upload_driver_doc(
    org_id: uuid.UUID,
    driver_id: uuid.UUID,
    doc_type: str,
    file_name: str,
    file_bytes: bytes,
    content_type: str,
    db: AsyncSession,
) -> str:
    stmt = select(Driver).where(Driver.id == driver_id, Driver.organisation_id == org_id)
    res = await db.execute(stmt)
    driver = res.scalars().first()
    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")

    url = await upload_document_to_r2(
        file_bytes=file_bytes,
        file_name=file_name,
        content_type=content_type,
        folder=f"tenants/{org_id}/drivers/{driver_id}",
    )
    docs = dict(driver.documents)
    docs[doc_type] = url
    driver.documents = docs
    await db.commit()
    return url
