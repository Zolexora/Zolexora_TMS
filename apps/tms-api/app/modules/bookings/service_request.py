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
from app.modules.bookings.models_request import BookingRequest, BookingRequestStatus
from app.modules.bookings.schemas import BookingResponse
from app.modules.bookings.schemas_request import (
    BookingRequestCreate,
    BookingRequestResponse,
    BookingRequestUpdate,
)
from app.modules.customers.models import Customer


async def create_booking_request(
    org_id: uuid.UUID,
    actor_id: uuid.UUID,
    req: BookingRequestCreate,
    db: AsyncSession,
) -> BookingRequestResponse:
    # 1. Verify customer belongs to tenant
    c_stmt = select(Customer).where(Customer.id == req.customer_id, Customer.organisation_id == org_id)
    c_res = await db.execute(c_stmt)
    if not c_res.scalars().first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found in organisation")

    # 2. Geocode if coordinates omitted
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

    req_number = f"BR-{datetime.datetime.now().year}-{uuid.uuid4().hex[:6].upper()}"

    booking_req = BookingRequest(
        id=uuid.uuid4(),
        request_number=req_number,
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
        special_instructions=req.special_instructions,
        source=req.source,
        estimated_pricing=req.estimated_pricing,
        status=BookingRequestStatus.DRAFT,
        created_by_user_id=actor_id,
    )
    db.add(booking_req)

    audit = AuditLog(
        id=uuid.uuid4(),
        organisation_id=org_id,
        actor_user_id=actor_id,
        action="BOOKING_REQUEST_CREATED",
        entity_type="booking_request",
        entity_id=booking_req.id,
        metadata_={"request_number": booking_req.request_number, "status": booking_req.status.value},
    )
    db.add(audit)

    await db.commit()
    await db.refresh(booking_req)
    return BookingRequestResponse.model_validate(booking_req)


async def list_booking_requests(
    org_id: uuid.UUID,
    db: AsyncSession,
    status_filter: Optional[BookingRequestStatus] = None,
    customer_id: Optional[uuid.UUID] = None,
    skip: int = 0,
    limit: int = 50,
) -> list[BookingRequestResponse]:
    stmt = select(BookingRequest).where(BookingRequest.organisation_id == org_id)
    if status_filter:
        stmt = stmt.where(BookingRequest.status == status_filter)
    if customer_id:
        stmt = stmt.where(BookingRequest.customer_id == customer_id)

    stmt = stmt.order_by(desc(BookingRequest.created_at)).offset(skip).limit(limit)
    res = await db.execute(stmt)
    rows = res.scalars().all()
    return [BookingRequestResponse.model_validate(r) for r in rows]


async def get_booking_request(
    org_id: uuid.UUID,
    request_id: uuid.UUID,
    db: AsyncSession,
) -> BookingRequestResponse:
    stmt = select(BookingRequest).where(BookingRequest.id == request_id, BookingRequest.organisation_id == org_id)
    res = await db.execute(stmt)
    req = res.scalars().first()
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking request not found")
    return BookingRequestResponse.model_validate(req)


async def submit_booking_request(
    org_id: uuid.UUID,
    request_id: uuid.UUID,
    actor_id: uuid.UUID,
    db: AsyncSession,
) -> BookingRequestResponse:
    stmt = select(BookingRequest).where(BookingRequest.id == request_id, BookingRequest.organisation_id == org_id)
    res = await db.execute(stmt)
    req = res.scalars().first()
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking request not found")

    if req.status != BookingRequestStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot submit request from status '{req.status.value}'. Must be in 'DRAFT'.",
        )

    req.status = BookingRequestStatus.REQUESTED
    audit = AuditLog(
        id=uuid.uuid4(),
        organisation_id=org_id,
        actor_user_id=actor_id,
        action="BOOKING_REQUEST_SUBMITTED",
        entity_type="booking_request",
        entity_id=req.id,
        metadata_={"request_number": req.request_number},
    )
    db.add(audit)
    await db.commit()
    await db.refresh(req)
    return BookingRequestResponse.model_validate(req)


async def confirm_booking_request(
    org_id: uuid.UUID,
    request_id: uuid.UUID,
    actor_id: uuid.UUID,
    db: AsyncSession,
) -> dict:
    """
    Validates state transition and atomically generates authoritative Booking from BookingRequest.
    """
    stmt = select(BookingRequest).where(BookingRequest.id == request_id, BookingRequest.organisation_id == org_id)
    res = await db.execute(stmt)
    req = res.scalars().first()
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking request not found")

    if req.status not in (BookingRequestStatus.DRAFT, BookingRequestStatus.REQUESTED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot confirm request in status '{req.status.value}'.",
        )

    booking_num = f"BK-{datetime.datetime.now().year}-{uuid.uuid4().hex[:6].upper()}"
    booking = Booking(
        id=uuid.uuid4(),
        booking_number=booking_num,
        booking_request_id=req.id,
        organisation_id=org_id,
        customer_id=req.customer_id,
        booking_type=req.booking_type,
        service_type=req.service_type,
        pickup_address=req.pickup_address,
        pickup_lat=req.pickup_lat,
        pickup_lng=req.pickup_lng,
        drop_address=req.drop_address,
        drop_lat=req.drop_lat,
        drop_lng=req.drop_lng,
        pickup_datetime=req.pickup_datetime,
        expected_completion_datetime=req.expected_completion_datetime,
        passenger_info=req.passenger_info,
        cargo_info=req.cargo_info,
        vehicle_requirements=req.vehicle_requirements,
        driver_requirements={},
        rate_card_version_id=req.rate_card_version_id,
        commercial_terms={"estimated_pricing": str(req.estimated_pricing)} if req.estimated_pricing else {},
        operational_instructions=req.special_instructions,
        status=BookingStatus.CONFIRMED,
        source=req.source,
        metadata_={"created_from_request": req.request_number},
        created_by_user_id=actor_id,
    )
    db.add(booking)

    req.status = BookingRequestStatus.CONFIRMED

    audit = AuditLog(
        id=uuid.uuid4(),
        organisation_id=org_id,
        actor_user_id=actor_id,
        action="BOOKING_REQUEST_CONFIRMED",
        entity_type="booking_request",
        entity_id=req.id,
        metadata_={"request_number": req.request_number, "generated_booking": booking.booking_number},
    )
    db.add(audit)

    await db.commit()
    await db.refresh(req)
    await db.refresh(booking)

    # Broadcast WebSocket event
    await ws_manager.broadcast_to_org(
        org_id,
        "booking.confirmed",
        {"booking_id": str(booking.id), "booking_number": booking.booking_number, "customer_id": str(booking.customer_id)},
    )

    return BookingResponse.model_validate(booking)


async def cancel_booking_request(
    org_id: uuid.UUID,
    request_id: uuid.UUID,
    actor_id: uuid.UUID,
    reason: Optional[str],
    db: AsyncSession,
) -> BookingRequestResponse:
    stmt = select(BookingRequest).where(BookingRequest.id == request_id, BookingRequest.organisation_id == org_id)
    res = await db.execute(stmt)
    req = res.scalars().first()
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking request not found")

    if req.status == BookingRequestStatus.CONFIRMED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel an already confirmed booking request. Cancel the active booking instead.",
        )

    req.status = BookingRequestStatus.CANCELLED
    audit = AuditLog(
        id=uuid.uuid4(),
        organisation_id=org_id,
        actor_user_id=actor_id,
        action="BOOKING_REQUEST_CANCELLED",
        entity_type="booking_request",
        entity_id=req.id,
        metadata_={"reason": reason or "User cancelled"},
    )
    db.add(audit)
    await db.commit()
    await db.refresh(req)
    return BookingRequestResponse.model_validate(req)
