import uuid
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.models import AuditLog
from app.modules.vendors.models import Vendor, VendorStatus, VendorType
from app.modules.vendors.schemas import VendorCreate, VendorResponse, VendorUpdate


async def create_vendor(
    org_id: uuid.UUID,
    actor_id: uuid.UUID,
    req: VendorCreate,
    db: AsyncSession,
) -> VendorResponse:
    vendor = Vendor(
        id=uuid.uuid4(),
        organisation_id=org_id,
        name=req.name.strip(),
        vendor_type=req.vendor_type,
        contact_person=req.contact_person.strip() if req.contact_person else None,
        email=req.email,
        phone=req.phone.strip() if req.phone else None,
        address=req.address.strip() if req.address else None,
        gstin=req.gstin.strip().upper() if req.gstin else None,
        pan=req.pan.strip().upper() if req.pan else None,
        bank_account_name=req.bank_account_name.strip() if req.bank_account_name else None,
        bank_account_number=req.bank_account_number.strip() if req.bank_account_number else None,
        bank_ifsc=req.bank_ifsc.strip().upper() if req.bank_ifsc else None,
        bank_name=req.bank_name.strip() if req.bank_name else None,
        status=VendorStatus.ACTIVE,
    )
    db.add(vendor)

    audit = AuditLog(
        id=uuid.uuid4(),
        organisation_id=org_id,
        actor_user_id=actor_id,
        action="VENDOR_CREATED",
        entity_type="vendor",
        entity_id=vendor.id,
        metadata_={"vendor_name": vendor.name, "vendor_type": vendor.vendor_type.value},
    )
    db.add(audit)

    await db.commit()
    await db.refresh(vendor)
    return VendorResponse.model_validate(vendor)


async def list_vendors(
    org_id: uuid.UUID,
    db: AsyncSession,
    vendor_type: Optional[VendorType] = None,
    status_filter: Optional[VendorStatus] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> list[VendorResponse]:
    stmt = select(Vendor).where(Vendor.organisation_id == org_id)

    if vendor_type:
        stmt = stmt.where(Vendor.vendor_type == vendor_type)

    if status_filter:
        stmt = stmt.where(Vendor.status == status_filter)

    if search:
        pattern = f"%{search.strip()}%"
        stmt = stmt.where(Vendor.name.ilike(pattern) | Vendor.phone.ilike(pattern))

    stmt = stmt.order_by(desc(Vendor.created_at)).offset(skip).limit(limit)
    res = await db.execute(stmt)
    rows = res.scalars().all()
    return [VendorResponse.model_validate(r) for r in rows]


async def get_vendor(
    org_id: uuid.UUID,
    vendor_id: uuid.UUID,
    db: AsyncSession,
) -> VendorResponse:
    stmt = select(Vendor).where(
        Vendor.id == vendor_id,
        Vendor.organisation_id == org_id,
    )
    res = await db.execute(stmt)
    vendor = res.scalars().first()
    if not vendor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")
    return VendorResponse.model_validate(vendor)


async def update_vendor(
    org_id: uuid.UUID,
    vendor_id: uuid.UUID,
    actor_id: uuid.UUID,
    req: VendorUpdate,
    db: AsyncSession,
) -> VendorResponse:
    stmt = select(Vendor).where(
        Vendor.id == vendor_id,
        Vendor.organisation_id == org_id,
    )
    res = await db.execute(stmt)
    vendor = res.scalars().first()
    if not vendor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")

    update_data = req.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        if val is not None and isinstance(val, str):
            val = val.strip()
            if field in ("gstin", "pan", "bank_ifsc"):
                val = val.upper()
        setattr(vendor, field, val)

    audit = AuditLog(
        id=uuid.uuid4(),
        organisation_id=org_id,
        actor_user_id=actor_id,
        action="VENDOR_UPDATED",
        entity_type="vendor",
        entity_id=vendor.id,
        metadata_={"updated_fields": list(update_data.keys())},
    )
    db.add(audit)

    await db.commit()
    await db.refresh(vendor)
    return VendorResponse.model_validate(vendor)


async def delete_vendor(
    org_id: uuid.UUID,
    vendor_id: uuid.UUID,
    actor_id: uuid.UUID,
    db: AsyncSession,
) -> None:
    stmt = select(Vendor).where(
        Vendor.id == vendor_id,
        Vendor.organisation_id == org_id,
    )
    res = await db.execute(stmt)
    vendor = res.scalars().first()
    if not vendor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")

    vendor.status = VendorStatus.INACTIVE
    audit = AuditLog(
        id=uuid.uuid4(),
        organisation_id=org_id,
        actor_user_id=actor_id,
        action="VENDOR_DEACTIVATED",
        entity_type="vendor",
        entity_id=vendor.id,
        metadata_={"vendor_name": vendor.name},
    )
    db.add(audit)
    await db.commit()
