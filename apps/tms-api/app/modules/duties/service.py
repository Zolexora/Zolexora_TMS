import datetime
import uuid
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.websocket import ws_manager
from app.modules.audit.models import AuditLog
from app.modules.bookings.models import Booking, BookingStatus
from app.modules.drivers.models import Driver, DriverStatus
from app.modules.duties.models import (
    Duty,
    DutyAssignment,
    DutyAssignmentStatus,
    DutyStatus,
)
from app.modules.duties.schemas import (
    DutyAssignRequest,
    DutyCreate,
    DutyReassignRequest,
    DutyResponse,
)
from app.modules.vehicles.models import Vehicle, VehicleOperationalStatus


async def validate_driver_eligibility(
    driver_id: uuid.UUID,
    org_id: uuid.UUID,
    start_time: datetime.datetime,
    end_time: datetime.datetime,
    exclude_duty_id: Optional[uuid.UUID],
    db: AsyncSession,
) -> Driver:
    # 1. Driver exists and belongs to organisation
    stmt = select(Driver).where(Driver.id == driver_id, Driver.organisation_id == org_id)
    res = await db.execute(stmt)
    driver = res.scalars().first()
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="DRIVER_NOT_FOUND: Driver does not exist in this organisation",
        )

    if driver.status == DriverStatus.INACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="DRIVER_INACTIVE: Driver account is deactivated",
        )

    # 2. Driver licence compliance check
    if not driver.license_number:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="DRIVER_LICENSE_MISSING: Driver does not have a commercial license registered",
        )

    if driver.license_expiry and driver.license_expiry < start_time.date():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"DRIVER_LICENSE_EXPIRED: Driver's commercial license expired on {driver.license_expiry}",
        )

    # 3. Conflict detection: check overlapping duties
    conflict_stmt = select(Duty).where(
        Duty.organisation_id == org_id,
        Duty.driver_id == driver_id,
        Duty.status.not_in([DutyStatus.CANCELLED, DutyStatus.DUTY_COMPLETED]),
        and_(
            Duty.scheduled_start_time < end_time,
            Duty.scheduled_end_time > start_time,
        ),
    )
    if exclude_duty_id:
        conflict_stmt = conflict_stmt.where(Duty.id != exclude_duty_id)

    conflict_res = await db.execute(conflict_stmt)
    conflict = conflict_res.scalars().first()
    if conflict:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"DRIVER_ALREADY_ASSIGNED: Driver is already allocated to duty {conflict.duty_number} between {conflict.scheduled_start_time} and {conflict.scheduled_end_time}",
        )

    return driver


async def validate_vehicle_eligibility(
    vehicle_id: uuid.UUID,
    org_id: uuid.UUID,
    start_time: datetime.datetime,
    end_time: datetime.datetime,
    exclude_duty_id: Optional[uuid.UUID],
    db: AsyncSession,
) -> Vehicle:
    # 1. Vehicle exists and belongs to organisation
    stmt = select(Vehicle).where(Vehicle.id == vehicle_id, Vehicle.organisation_id == org_id)
    res = await db.execute(stmt)
    vehicle = res.scalars().first()
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="VEHICLE_NOT_FOUND: Vehicle does not exist in this organisation",
        )

    # 2. Operational status check
    if vehicle.status in [VehicleOperationalStatus.MAINTENANCE, VehicleOperationalStatus.DECOMMISSIONED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"VEHICLE_NOT_OPERATIONAL: Vehicle is currently {vehicle.status.value}",
        )

    # 3. Conflict detection: check overlapping duties
    conflict_stmt = select(Duty).where(
        Duty.organisation_id == org_id,
        Duty.vehicle_id == vehicle_id,
        Duty.status.not_in([DutyStatus.CANCELLED, DutyStatus.DUTY_COMPLETED]),
        and_(
            Duty.scheduled_start_time < end_time,
            Duty.scheduled_end_time > start_time,
        ),
    )
    if exclude_duty_id:
        conflict_stmt = conflict_stmt.where(Duty.id != exclude_duty_id)

    conflict_res = await db.execute(conflict_stmt)
    conflict = conflict_res.scalars().first()
    if conflict:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"VEHICLE_ALREADY_ASSIGNED: Vehicle {vehicle.registration_number} is already allocated to duty {conflict.duty_number} during this time window",
        )

    return vehicle


async def create_duty(
    org_id: uuid.UUID,
    actor_id: uuid.UUID,
    req: DutyCreate,
    db: AsyncSession,
) -> DutyResponse:
    # 1. Verify booking exists and is confirmed
    b_stmt = select(Booking).where(Booking.id == req.booking_id, Booking.organisation_id == org_id)
    b_res = await db.execute(b_stmt)
    booking = b_res.scalars().first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    if booking.status != BookingStatus.CONFIRMED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot create duty from booking with status '{booking.status.value}'. Must be CONFIRMED.",
        )

    if req.scheduled_end_time < req.scheduled_start_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Scheduled end time must be greater than or equal to scheduled start time",
        )

    # 2. Validate driver & vehicle if provided at creation
    if req.driver_id:
        await validate_driver_eligibility(req.driver_id, org_id, req.scheduled_start_time, req.scheduled_end_time, None, db)
    if req.vehicle_id:
        await validate_vehicle_eligibility(req.vehicle_id, org_id, req.scheduled_start_time, req.scheduled_end_time, None, db)

    duty_num = f"DT-{datetime.datetime.now().year}-{uuid.uuid4().hex[:6].upper()}"

    duty = Duty(
        id=uuid.uuid4(),
        duty_number=duty_num,
        organisation_id=org_id,
        booking_id=req.booking_id,
        driver_id=req.driver_id,
        vehicle_id=req.vehicle_id,
        scheduled_start_time=req.scheduled_start_time,
        scheduled_end_time=req.scheduled_end_time,
        status=DutyStatus.ALLOCATED,
        notes=req.notes,
    )
    db.add(duty)
    await db.flush()

    if req.driver_id and req.vehicle_id:
        assignment = DutyAssignment(
            id=uuid.uuid4(),
            duty_id=duty.id,
            driver_id=req.driver_id,
            vehicle_id=req.vehicle_id,
            assigned_by_user_id=actor_id,
            status=DutyAssignmentStatus.ASSIGNED,
        )
        db.add(assignment)

    audit = AuditLog(
        id=uuid.uuid4(),
        organisation_id=org_id,
        actor_user_id=actor_id,
        action="DUTY_CREATED",
        entity_type="duty",
        entity_id=duty.id,
        metadata_={"duty_number": duty.duty_number, "booking_number": booking.booking_number},
    )
    db.add(audit)

    await db.commit()
    await db.refresh(duty)

    await ws_manager.broadcast_to_org(
        org_id,
        "duty.created",
        {"duty_id": str(duty.id), "duty_number": duty.duty_number, "booking_id": str(duty.booking_id)},
    )

    return DutyResponse.model_validate(duty)


async def assign_duty(
    org_id: uuid.UUID,
    duty_id: uuid.UUID,
    actor_id: uuid.UUID,
    req: DutyAssignRequest,
    db: AsyncSession,
) -> DutyResponse:
    # 1. Fetch duty
    stmt = select(Duty).where(Duty.id == duty_id, Duty.organisation_id == org_id)
    res = await db.execute(stmt)
    duty = res.scalars().first()
    if not duty:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Duty not found")

    if duty.status in [DutyStatus.CANCELLED, DutyStatus.DUTY_COMPLETED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot assign resources to duty in terminal status '{duty.status.value}'",
        )

    # 2. Transactional validation
    driver = await validate_driver_eligibility(req.driver_id, org_id, duty.scheduled_start_time, duty.scheduled_end_time, duty.id, db)
    vehicle = await validate_vehicle_eligibility(req.vehicle_id, org_id, duty.scheduled_start_time, duty.scheduled_end_time, duty.id, db)

    # 3. Supersede old assignments
    old_assign_stmt = select(DutyAssignment).where(
        DutyAssignment.duty_id == duty.id,
        DutyAssignment.status == DutyAssignmentStatus.ASSIGNED,
    )
    old_assign_res = await db.execute(old_assign_stmt)
    for old_asg in old_assign_res.scalars().all():
        old_asg.status = DutyAssignmentStatus.SUPERSEDED

    # 4. Insert new assignment
    assignment = DutyAssignment(
        id=uuid.uuid4(),
        duty_id=duty.id,
        driver_id=driver.id,
        vehicle_id=vehicle.id,
        assigned_by_user_id=actor_id,
        status=DutyAssignmentStatus.ASSIGNED,
    )
    db.add(assignment)

    duty.driver_id = driver.id
    duty.vehicle_id = vehicle.id
    duty.status = DutyStatus.ALLOCATED

    audit = AuditLog(
        id=uuid.uuid4(),
        organisation_id=org_id,
        actor_user_id=actor_id,
        action="DUTY_ASSIGNED",
        entity_type="duty",
        entity_id=duty.id,
        metadata_={
            "duty_number": duty.duty_number,
            "driver_name": driver.full_name,
            "vehicle_reg": vehicle.registration_number,
        },
    )
    db.add(audit)

    await db.commit()
    await db.refresh(duty)

    await ws_manager.broadcast_to_org(
        org_id,
        "duty.assigned",
        {
            "duty_id": str(duty.id),
            "duty_number": duty.duty_number,
            "driver_id": str(driver.id),
            "vehicle_id": str(vehicle.id),
        },
    )

    return DutyResponse.model_validate(duty)


async def dispatch_duty(
    org_id: uuid.UUID,
    duty_id: uuid.UUID,
    actor_id: uuid.UUID,
    db: AsyncSession,
) -> DutyResponse:
    stmt = select(Duty).where(Duty.id == duty_id, Duty.organisation_id == org_id)
    res = await db.execute(stmt)
    duty = res.scalars().first()
    if not duty:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Duty not found")

    if not duty.driver_id or not duty.vehicle_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot dispatch duty without both Driver and Vehicle allocated",
        )

    if duty.status != DutyStatus.ALLOCATED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot dispatch duty from status '{duty.status.value}'. Must be ALLOCATED.",
        )

    duty.status = DutyStatus.DISPATCHED
    duty.dispatched_at = datetime.datetime.now(datetime.timezone.utc)
    duty.dispatched_by_user_id = actor_id

    audit = AuditLog(
        id=uuid.uuid4(),
        organisation_id=org_id,
        actor_user_id=actor_id,
        action="DUTY_DISPATCHED",
        entity_type="duty",
        entity_id=duty.id,
        metadata_={"duty_number": duty.duty_number},
    )
    db.add(audit)

    await db.commit()
    await db.refresh(duty)

    await ws_manager.broadcast_to_org(
        org_id,
        "duty.dispatched",
        {"duty_id": str(duty.id), "duty_number": duty.duty_number},
    )

    return DutyResponse.model_validate(duty)


async def driver_accept_duty(
    org_id: uuid.UUID,
    duty_id: uuid.UUID,
    driver_user_id: uuid.UUID,
    db: AsyncSession,
) -> DutyResponse:
    stmt = select(Duty).where(Duty.id == duty_id, Duty.organisation_id == org_id)
    res = await db.execute(stmt)
    duty = res.scalars().first()
    if not duty:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Duty not found")

    # Update assignment
    asg_stmt = select(DutyAssignment).where(
        DutyAssignment.duty_id == duty.id,
        DutyAssignment.status == DutyAssignmentStatus.ASSIGNED,
    ).order_by(desc(DutyAssignment.assigned_at))
    asg_res = await db.execute(asg_stmt)
    asg = asg_res.scalars().first()
    if asg:
        asg.status = DutyAssignmentStatus.ACCEPTED
        asg.accepted_at = datetime.datetime.now(datetime.timezone.utc)

    audit = AuditLog(
        id=uuid.uuid4(),
        organisation_id=org_id,
        actor_user_id=driver_user_id,
        action="DRIVER_ACCEPTED_DUTY",
        entity_type="duty",
        entity_id=duty.id,
        metadata_={"duty_number": duty.duty_number},
    )
    db.add(audit)
    await db.commit()
    await db.refresh(duty)

    await ws_manager.broadcast_to_org(
        org_id,
        "duty.driver_accepted",
        {"duty_id": str(duty.id), "duty_number": duty.duty_number},
    )

    return DutyResponse.model_validate(duty)


async def driver_reject_duty(
    org_id: uuid.UUID,
    duty_id: uuid.UUID,
    driver_user_id: uuid.UUID,
    reason: Optional[str],
    db: AsyncSession,
) -> DutyResponse:
    stmt = select(Duty).where(Duty.id == duty_id, Duty.organisation_id == org_id)
    res = await db.execute(stmt)
    duty = res.scalars().first()
    if not duty:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Duty not found")

    asg_stmt = select(DutyAssignment).where(
        DutyAssignment.duty_id == duty.id,
        DutyAssignment.status == DutyAssignmentStatus.ASSIGNED,
    ).order_by(desc(DutyAssignment.assigned_at))
    asg_res = await db.execute(asg_stmt)
    asg = asg_res.scalars().first()
    if asg:
        asg.status = DutyAssignmentStatus.REJECTED
        asg.rejected_at = datetime.datetime.now(datetime.timezone.utc)
        asg.rejection_reason = reason or "Driver declined duty"

    # Reset allocation on duty so dispatcher can reallocate
    duty.driver_id = None
    duty.status = DutyStatus.ALLOCATED

    audit = AuditLog(
        id=uuid.uuid4(),
        organisation_id=org_id,
        actor_user_id=driver_user_id,
        action="DRIVER_REJECTED_DUTY",
        entity_type="duty",
        entity_id=duty.id,
        metadata_={"duty_number": duty.duty_number, "reason": reason or "No reason provided"},
    )
    db.add(audit)
    await db.commit()
    await db.refresh(duty)

    await ws_manager.broadcast_to_org(
        org_id,
        "duty.driver_rejected",
        {"duty_id": str(duty.id), "duty_number": duty.duty_number, "reason": reason},
    )

    return DutyResponse.model_validate(duty)


async def update_duty_milestone(
    org_id: uuid.UUID,
    duty_id: uuid.UUID,
    actor_id: uuid.UUID,
    target_status: DutyStatus,
    db: AsyncSession,
) -> DutyResponse:
    stmt = select(Duty).where(Duty.id == duty_id, Duty.organisation_id == org_id)
    res = await db.execute(stmt)
    duty = res.scalars().first()
    if not duty:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Duty not found")

    duty.status = target_status
    if target_status == DutyStatus.IN_TRANSIT and not duty.actual_start_time:
        duty.actual_start_time = datetime.datetime.now(datetime.timezone.utc)
    elif target_status == DutyStatus.DUTY_COMPLETED:
        duty.actual_end_time = datetime.datetime.now(datetime.timezone.utc)

    audit = AuditLog(
        id=uuid.uuid4(),
        organisation_id=org_id,
        actor_user_id=actor_id,
        action=f"DUTY_STATUS_{target_status.value}",
        entity_type="duty",
        entity_id=duty.id,
        metadata_={"duty_number": duty.duty_number, "new_status": target_status.value},
    )
    db.add(audit)
    await db.commit()
    await db.refresh(duty)

    await ws_manager.broadcast_to_org(
        org_id,
        f"duty.{target_status.value.lower()}",
        {"duty_id": str(duty.id), "duty_number": duty.duty_number, "status": target_status.value},
    )

    return DutyResponse.model_validate(duty)


async def list_duties(
    org_id: uuid.UUID,
    db: AsyncSession,
    status_filter: Optional[DutyStatus] = None,
    driver_id: Optional[uuid.UUID] = None,
    vehicle_id: Optional[uuid.UUID] = None,
    skip: int = 0,
    limit: int = 50,
) -> list[DutyResponse]:
    stmt = select(Duty).where(Duty.organisation_id == org_id)
    if status_filter:
        stmt = stmt.where(Duty.status == status_filter)
    if driver_id:
        stmt = stmt.where(Duty.driver_id == driver_id)
    if vehicle_id:
        stmt = stmt.where(Duty.vehicle_id == vehicle_id)

    stmt = stmt.order_by(desc(Duty.created_at)).offset(skip).limit(limit)
    res = await db.execute(stmt)
    rows = res.scalars().all()
    return [DutyResponse.model_validate(r) for r in rows]


async def get_duty(
    org_id: uuid.UUID,
    duty_id: uuid.UUID,
    db: AsyncSession,
) -> DutyResponse:
    stmt = select(Duty).where(Duty.id == duty_id, Duty.organisation_id == org_id)
    res = await db.execute(stmt)
    duty = res.scalars().first()
    if not duty:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Duty not found")
    return DutyResponse.model_validate(duty)
