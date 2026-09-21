import uuid
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.models import AuditLog
from app.modules.customers.models import Customer, CustomerStatus
from app.modules.customers.schemas import CustomerCreate, CustomerResponse, CustomerUpdate


async def create_customer(
    org_id: uuid.UUID,
    actor_id: uuid.UUID,
    req: CustomerCreate,
    db: AsyncSession,
) -> CustomerResponse:
    customer = Customer(
        id=uuid.uuid4(),
        organisation_id=org_id,
        name=req.name.strip(),
        contact_person=req.contact_person.strip() if req.contact_person else None,
        email=req.email,
        phone=req.phone.strip() if req.phone else None,
        billing_address=req.billing_address.strip() if req.billing_address else None,
        gstin=req.gstin.strip().upper() if req.gstin else None,
        pan=req.pan.strip().upper() if req.pan else None,
        payment_terms_days=req.payment_terms_days,
        credit_limit=req.credit_limit,
        status=CustomerStatus.ACTIVE,
        notes=req.notes,
    )
    db.add(customer)

    audit = AuditLog(
        id=uuid.uuid4(),
        organisation_id=org_id,
        actor_user_id=actor_id,
        action="CUSTOMER_CREATED",
        entity_type="customer",
        entity_id=customer.id,
        metadata_={"customer_name": customer.name, "gstin": customer.gstin},
    )
    db.add(audit)

    await db.commit()
    await db.refresh(customer)
    return CustomerResponse.model_validate(customer)


async def list_customers(
    org_id: uuid.UUID,
    db: AsyncSession,
    status_filter: Optional[CustomerStatus] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> list[CustomerResponse]:
    stmt = select(Customer).where(Customer.organisation_id == org_id)

    if status_filter:
        stmt = stmt.where(Customer.status == status_filter)

    if search:
        pattern = f"%{search.strip()}%"
        stmt = stmt.where(Customer.name.ilike(pattern) | Customer.phone.ilike(pattern))

    stmt = stmt.order_by(desc(Customer.created_at)).offset(skip).limit(limit)
    res = await db.execute(stmt)
    rows = res.scalars().all()
    return [CustomerResponse.model_validate(r) for r in rows]


async def get_customer(
    org_id: uuid.UUID,
    customer_id: uuid.UUID,
    db: AsyncSession,
) -> CustomerResponse:
    stmt = select(Customer).where(
        Customer.id == customer_id,
        Customer.organisation_id == org_id,
    )
    res = await db.execute(stmt)
    customer = res.scalars().first()
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    return CustomerResponse.model_validate(customer)


async def update_customer(
    org_id: uuid.UUID,
    customer_id: uuid.UUID,
    actor_id: uuid.UUID,
    req: CustomerUpdate,
    db: AsyncSession,
) -> CustomerResponse:
    stmt = select(Customer).where(
        Customer.id == customer_id,
        Customer.organisation_id == org_id,
    )
    res = await db.execute(stmt)
    customer = res.scalars().first()
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    update_data = req.model_dump(exclude_unset=True)
    if "name" in update_data and update_data["name"]:
        customer.name = update_data["name"].strip()
    if "contact_person" in update_data:
        customer.contact_person = update_data["contact_person"]
    if "email" in update_data:
        customer.email = update_data["email"]
    if "phone" in update_data:
        customer.phone = update_data["phone"]
    if "billing_address" in update_data:
        customer.billing_address = update_data["billing_address"]
    if "gstin" in update_data and update_data["gstin"]:
        customer.gstin = update_data["gstin"].strip().upper()
    if "pan" in update_data and update_data["pan"]:
        customer.pan = update_data["pan"].strip().upper()
    if "payment_terms_days" in update_data and update_data["payment_terms_days"] is not None:
        customer.payment_terms_days = update_data["payment_terms_days"]
    if "credit_limit" in update_data and update_data["credit_limit"] is not None:
        customer.credit_limit = update_data["credit_limit"]
    if "status" in update_data and update_data["status"]:
        customer.status = update_data["status"]
    if "notes" in update_data:
        customer.notes = update_data["notes"]

    audit = AuditLog(
        id=uuid.uuid4(),
        organisation_id=org_id,
        actor_user_id=actor_id,
        action="CUSTOMER_UPDATED",
        entity_type="customer",
        entity_id=customer.id,
        metadata_={"updated_fields": list(update_data.keys())},
    )
    db.add(audit)

    await db.commit()
    await db.refresh(customer)
    return CustomerResponse.model_validate(customer)


async def delete_customer(
    org_id: uuid.UUID,
    customer_id: uuid.UUID,
    actor_id: uuid.UUID,
    db: AsyncSession,
) -> None:
    stmt = select(Customer).where(
        Customer.id == customer_id,
        Customer.organisation_id == org_id,
    )
    res = await db.execute(stmt)
    customer = res.scalars().first()
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    customer.status = CustomerStatus.INACTIVE
    audit = AuditLog(
        id=uuid.uuid4(),
        organisation_id=org_id,
        actor_user_id=actor_id,
        action="CUSTOMER_DEACTIVATED",
        entity_type="customer",
        entity_id=customer.id,
        metadata_={"customer_name": customer.name},
    )
    db.add(audit)
    await db.commit()
