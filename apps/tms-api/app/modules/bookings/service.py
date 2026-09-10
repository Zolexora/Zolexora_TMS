import datetime
import uuid
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.geocoding import geocoding_service
from app.core.websocket import ws_manager
from app.modules.audit.models import AuditLog
from app.modules.bookings.models import Booking, BookingStatus
from app.modules.bookings.schemas import BookingCreate, BookingResponse, BookingUpdate
from app.modules.customers.models import Customer


async def create_booking(
    org_id: uuid.UUID,
    actor_id: uuid.UUID,
    req: BookingCreate,
    db: AsyncSession,
) -> BookingResponse:
    # 1. Verify customer exists in tenant
    c_stmt = select(Customer).where(Customer.id == req.customer_id, Customer.organisation_id == org_id)
    c_res = await db.execute(c_stmt)
    if not c_res.scalars().first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found in organisation")

    # 2. Geocode coordinates if not provided
    p_lat, p_lng = req.pickup_lat, req.pickup_lng
    if p_lat is None or p_lng is None:
        p_geo = await geocoding_service.geocode(req.pickup_address)
        if p_geo:
            p_lat, p_lng = p_geo.latitude, p_geo.longitude

    d_lat, d_lng = req.drop_lat, req.drop_lng
    if d_lat is None or d_lng is None:
        d_geo = await geocoding_service.geocode(req.drop_address)
        if d_geo:
            d_lat, d_lng = d_geo.latitude, d_geo.longitude

    booking_num = f"BK-{datetime.datetime.now().year}-{uuid.uuid4().hex[:6].upper()}"

    booking = Booking(
        id=uuid.uuid4(),
        booking_number=booking_num,
        booking_request_id=req.booking_request_id,
        organisation_id=org_id,
        customer_id=req.customer_id,
        booking_type=req.booking_type,
        service_type=req.service_type,
        pickup_address=req.pickup_address.strip(),
        pickup_lat=p_lat,
        pickup_lng=p_lng,
        drop_address=req.drop_address.strip(),
        drop_lat=d_lat,
        drop_lng=d_lng,
        pickup_datetime=req.pickup_datetime,
        expected_completion_datetime=req.expected_completion_datetime,
        passenger_info=req.passenger_info,
        cargo_info=req.cargo_info,
        vehicle_requirements=req.vehicle_requirements,
        driver_requirements=req.driver_requirements,
        commercial_terms=req.commercial_terms,
        operational_instructions=req.operational_instructions,
        status=BookingStatus.CONFIRMED,
        source=req.source,
        created_by_user_id=actor_id,
    )
    db.add(booking)

    audit = AuditLog(
        id=uuid.uuid4(),
        organisation_id=org_id,
        actor_user_id=actor_id,
        action="BOOKING_CREATED",
        entity_type="booking",
        entity_id=booking.id,
        metadata_={"booking_number": booking.booking_number, "type": booking.booking_type.value},
    )
    db.add(audit)

    await db.commit()
    await db.refresh(booking)

    await ws_manager.broadcast_to_org(
        org_id,
        "booking.created",
        {"booking_id": str(booking.id), "booking_number": booking.booking_number, "customer_id": str(booking.customer_id)},
    )

    return BookingResponse.model_validate(booking)


async def list_bookings(
    org_id: uuid.UUID,
    db: AsyncSession,
    status_filter: Optional[BookingStatus] = None,
    customer_id: Optional[uuid.UUID] = None,
    skip: int = 0,
    limit: int = 50,
) -> list[BookingResponse]:
    stmt = select(Booking).where(Booking.organisation_id == org_id)
    if status_filter:
        stmt = stmt.where(Booking.status == status_filter)
    if customer_id:
        stmt = stmt.where(Booking.customer_id == customer_id)

    stmt = stmt.order_by(desc(Booking.created_at)).offset(skip).limit(limit)
    res = await db.execute(stmt)
    rows = res.scalars().all()
    return [BookingResponse.model_validate(r) for r in rows]


async def get_booking(
    org_id: uuid.UUID,
    booking_id: uuid.UUID,
    db: AsyncSession,
) -> BookingResponse:
    stmt = select(Booking).where(Booking.id == booking_id, Booking.organisation_id == org_id)
    res = await db.execute(stmt)
    booking = res.scalars().first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    return BookingResponse.model_validate(booking)


async def cancel_booking(
    org_id: uuid.UUID,
    booking_id: uuid.UUID,
    actor_id: uuid.UUID,
    reason: Optional[str],
    db: AsyncSession,
) -> BookingResponse:
    stmt = select(Booking).where(Booking.id == booking_id, Booking.organisation_id == org_id)
    res = await db.execute(stmt)
    booking = res.scalars().first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    if booking.status in (BookingStatus.COMPLETED, BookingStatus.CANCELLED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel booking with status '{booking.status.value}'.",
        )

    booking.status = BookingStatus.CANCELLED
    audit = AuditLog(
        id=uuid.uuid4(),
        organisation_id=org_id,
        actor_user_id=actor_id,
        action="BOOKING_CANCELLED",
        entity_type="booking",
        entity_id=booking.id,
        metadata_={"reason": reason or "User cancelled"},
    )
    db.add(audit)
    await db.commit()
    await db.refresh(booking)

    await ws_manager.broadcast_to_org(
        org_id,
        "booking.cancelled",
        {"booking_id": str(booking.id), "booking_number": booking.booking_number},
    )

    return BookingResponse.model_validate(booking)
