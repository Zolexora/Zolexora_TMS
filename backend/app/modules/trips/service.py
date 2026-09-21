import datetime
from decimal import Decimal
import uuid
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.storage import upload_document_to_r2
from app.core.websocket import ws_manager
from app.modules.audit.models import AuditLog
from app.modules.duties.models import Duty, DutyStatus
from app.modules.trips.models import Trip, TripEvent, TripStatus
from app.modules.trips.schemas import (
    TripCompleteRequest,
    TripEventResponse,
    TripReceiptAddRequest,
    TripResponse,
    TripStartRequest,
)


async def start_trip(
    org_id: uuid.UUID,
    duty_id: uuid.UUID,
    actor_id: uuid.UUID,
    req: TripStartRequest,
    db: AsyncSession,
) -> TripResponse:
    # 1. Fetch duty
    stmt = select(Duty).where(Duty.id == duty_id, Duty.organisation_id == org_id)
    res = await db.execute(stmt)
    duty = res.scalars().first()
    if not duty:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Duty not found")

    if not duty.driver_id or not duty.vehicle_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Duty has no assigned driver or vehicle")

    # Check if trip already started
    existing_trip_stmt = select(Trip).where(Trip.duty_id == duty.id)
    existing_trip_res = await db.execute(existing_trip_stmt)
    if existing_trip_res.scalars().first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A trip has already been initialized for this duty")

    now = datetime.datetime.now(datetime.timezone.utc)
    trip_num = f"TR-{now.year}-{uuid.uuid4().hex[:6].upper()}"

    trip = Trip(
        id=uuid.uuid4(),
        trip_number=trip_num,
        organisation_id=org_id,
        duty_id=duty.id,
        driver_id=duty.driver_id,
        vehicle_id=duty.vehicle_id,
        start_odometer=req.start_odometer,
        start_timestamp=now,
        start_location=req.start_location,
        status=TripStatus.IN_TRANSIT,
    )
    db.add(trip)

    # Record first milestone
    event = TripEvent(
        id=uuid.uuid4(),
        trip_id=trip.id,
        event_type="TRIP_STARTED",
        timestamp=now,
        latitude=req.start_location.get("lat") if isinstance(req.start_location, dict) else None,
        longitude=req.start_location.get("lng") if isinstance(req.start_location, dict) else None,
        notes=f"Starting odometer: {req.start_odometer} KM",
    )
    db.add(event)

    # Sync duty status
    duty.status = DutyStatus.IN_TRANSIT
    duty.actual_start_time = now

    audit = AuditLog(
        id=uuid.uuid4(),
        organisation_id=org_id,
        actor_user_id=actor_id,
        action="TRIP_STARTED",
        entity_type="trip",
        entity_id=trip.id,
        metadata_={"trip_number": trip.trip_number, "start_odometer": str(req.start_odometer)},
    )
    db.add(audit)

    await db.commit()
    await db.refresh(trip)

    await ws_manager.broadcast_to_org(
        org_id,
        "trip.started",
        {"trip_id": str(trip.id), "trip_number": trip.trip_number, "duty_id": str(duty.id)},
    )

    return TripResponse.model_validate(trip)


async def complete_trip(
    org_id: uuid.UUID,
    trip_id: uuid.UUID,
    actor_id: uuid.UUID,
    req: TripCompleteRequest,
    db: AsyncSession,
) -> TripResponse:
    stmt = select(Trip).where(Trip.id == trip_id, Trip.organisation_id == org_id)
    res = await db.execute(stmt)
    trip = res.scalars().first()
    if not trip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")

    if trip.status == TripStatus.COMPLETED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Trip is already completed")

    # Authoritative Odometer validation
    if req.end_odometer < trip.start_odometer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"ODOMETER_INVALID: Ending odometer ({req.end_odometer}) cannot be less than starting odometer ({trip.start_odometer})",
        )

    now = datetime.datetime.now(datetime.timezone.utc)
    trip.end_odometer = req.end_odometer
    trip.total_distance_km = req.end_odometer - trip.start_odometer
    trip.end_timestamp = now
    trip.end_location = req.end_location
    trip.toll_amount = req.toll_amount
    trip.fuel_amount = req.fuel_amount
    trip.parking_amount = req.parking_amount
    trip.waiting_minutes = req.waiting_minutes
    if req.pod_attachment_url:
        trip.pod_attachment_url = req.pod_attachment_url
        trip.pod_uploaded_at = now
    if req.pod_notes:
        trip.pod_notes = req.pod_notes
    if req.notes:
        trip.notes = req.notes

    trip.status = TripStatus.COMPLETED

    # Record completion milestone
    event = TripEvent(
        id=uuid.uuid4(),
        trip_id=trip.id,
        event_type="TRIP_COMPLETED",
        timestamp=now,
        latitude=req.end_location.get("lat") if isinstance(req.end_location, dict) else None,
        longitude=req.end_location.get("lng") if isinstance(req.end_location, dict) else None,
        notes=f"Ending odometer: {req.end_odometer} KM. Distance: {trip.total_distance_km} KM",
    )
    db.add(event)

    # Sync duty
    duty_stmt = select(Duty).where(Duty.id == trip.duty_id)
    duty_res = await db.execute(duty_stmt)
    duty = duty_res.scalars().first()
    if duty:
        duty.status = DutyStatus.DUTY_COMPLETED
        duty.actual_end_time = now

    audit = AuditLog(
        id=uuid.uuid4(),
        organisation_id=org_id,
        actor_user_id=actor_id,
        action="TRIP_COMPLETED",
        entity_type="trip",
        entity_id=trip.id,
        metadata_={
            "trip_number": trip.trip_number,
            "total_distance_km": str(trip.total_distance_km),
            "toll_amount": str(trip.toll_amount),
        },
    )
    db.add(audit)

    await db.commit()
    await db.refresh(trip)

    await ws_manager.broadcast_to_org(
        org_id,
        "trip.completed",
        {
            "trip_id": str(trip.id),
            "trip_number": trip.trip_number,
            "total_distance_km": str(trip.total_distance_km),
            "duty_id": str(trip.duty_id),
        },
    )

    return TripResponse.model_validate(trip)


async def add_trip_receipt(
    org_id: uuid.UUID,
    trip_id: uuid.UUID,
    actor_id: uuid.UUID,
    req: TripReceiptAddRequest,
    db: AsyncSession,
) -> TripResponse:
    stmt = select(Trip).where(Trip.id == trip_id, Trip.organisation_id == org_id)
    res = await db.execute(stmt)
    trip = res.scalars().first()
    if not trip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")

    receipts = list(trip.operational_receipts)
    receipts.append({
        "id": uuid.uuid4().hex,
        "type": req.receipt_type,
        "amount": str(req.amount),
        "url": req.receipt_url,
        "notes": req.notes,
        "recorded_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "recorded_by": str(actor_id),
    })
    trip.operational_receipts = receipts

    await db.commit()
    await db.refresh(trip)
    return TripResponse.model_validate(trip)


async def upload_pod(
    org_id: uuid.UUID,
    trip_id: uuid.UUID,
    file_bytes: bytes,
    file_name: str,
    content_type: str,
    notes: Optional[str],
    db: AsyncSession,
) -> str:
    stmt = select(Trip).where(Trip.id == trip_id, Trip.organisation_id == org_id)
    res = await db.execute(stmt)
    trip = res.scalars().first()
    if not trip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")

    url = await upload_document_to_r2(
        file_bytes=file_bytes,
        file_name=file_name,
        content_type=content_type,
        folder=f"tenants/{org_id}/trips/{trip_id}/pod",
    )
    trip.pod_attachment_url = url
    trip.pod_uploaded_at = datetime.datetime.now(datetime.timezone.utc)
    if notes:
        trip.pod_notes = notes

    await db.commit()
    return url


async def get_trip(
    org_id: uuid.UUID,
    trip_id: uuid.UUID,
    db: AsyncSession,
) -> TripResponse:
    stmt = select(Trip).where(Trip.id == trip_id, Trip.organisation_id == org_id)
    res = await db.execute(stmt)
    trip = res.scalars().first()
    if not trip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    return TripResponse.model_validate(trip)


async def list_trips(
    org_id: uuid.UUID,
    db: AsyncSession,
    status_filter: Optional[TripStatus] = None,
    limit: int = 50,
    offset: int = 0,
) -> list[TripResponse]:
    stmt = select(Trip).where(Trip.organisation_id == org_id)
    if status_filter:
        stmt = stmt.where(Trip.status == status_filter)
    stmt = stmt.order_by(desc(Trip.created_at)).limit(limit).offset(offset)
    res = await db.execute(stmt)
    return [TripResponse.model_validate(t) for t in res.scalars().all()]

