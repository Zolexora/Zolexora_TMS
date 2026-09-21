import datetime
import uuid
from typing import Optional
from fastapi import HTTPException, status

from app.auth.dependencies import TenantContext
from app.core.websocket import ws_manager
from app.modules.operations.duties.schemas import (
    DutyAssignRequest,
    DutyCreate,
    DutyResponse,
    DutyStatus,
)


def _row_to_response(row: dict, org_id: uuid.UUID) -> dict:
    row["organisation_id"] = org_id
    return row


async def _log_duty_event(conn, duty_id: str, actor_id: str, event_type: str, old_status: str, new_status: str, metadata: str = "{}"):
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await conn.execute(
        """
        INSERT INTO duty_events (id, duty_id, actor_id, event_type, previous_status, new_status, event_metadata, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (str(uuid.uuid4()), duty_id, actor_id, event_type, old_status, new_status, metadata, now_str)
    )


async def create_duty(
    ctx: TenantContext,
    req: DutyCreate,
) -> DutyResponse:
    conn = await ctx.d1.get_connection()
    
    # 1. Verify booking exists
    async with conn.execute("SELECT id FROM bookings WHERE id = ?", (str(req.booking_id),)) as cursor:
        b_res = await cursor.fetchone()
        if not b_res:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found in organisation")

    duty_id = str(uuid.uuid4())
    duty_num = f"DTY-{datetime.datetime.now().year}-{duty_id[:6].upper()}"
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    init_status = DutyStatus.UNASSIGNED.value
    if req.driver_id and req.vehicle_id:
        init_status = DutyStatus.ASSIGNED.value

    await conn.execute(
        """
        INSERT INTO duties (
            id, duty_number, booking_id, driver_id, vehicle_id, 
            scheduled_start_time, scheduled_end_time, status, notes, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            duty_id,
            duty_num,
            str(req.booking_id),
            str(req.driver_id) if req.driver_id else None,
            str(req.vehicle_id) if req.vehicle_id else None,
            req.scheduled_start_time.strftime("%Y-%m-%d %H:%M:%S"),
            req.scheduled_end_time.strftime("%Y-%m-%d %H:%M:%S"),
            init_status,
            req.notes,
            now_str,
            now_str
        )
    )

    await _log_duty_event(conn, duty_id, str(ctx.user_id), "DUTY_CREATED", None, init_status)

    await ws_manager.broadcast_to_org(
        ctx.organisation_id,
        "duty.created",
        {"duty_id": duty_id, "duty_number": duty_num, "booking_id": str(req.booking_id)},
    )

    async with conn.execute("SELECT * FROM duties WHERE id = ?", (duty_id,)) as cursor:
        row = await cursor.fetchone()
        return DutyResponse.model_validate(_row_to_response(dict(row), ctx.organisation_id))


async def list_duties(
    ctx: TenantContext,
    status_filter: Optional[DutyStatus] = None,
    driver_id: Optional[uuid.UUID] = None,
    vehicle_id: Optional[uuid.UUID] = None,
    skip: int = 0,
    limit: int = 50,
) -> list[DutyResponse]:
    conn = await ctx.d1.get_connection()
    
    query = "SELECT * FROM duties WHERE 1=1"
    params = []
    
    if status_filter:
        query += " AND status = ?"
        params.append(status_filter.value)
    if driver_id:
        query += " AND driver_id = ?"
        params.append(str(driver_id))
    if vehicle_id:
        query += " AND vehicle_id = ?"
        params.append(str(vehicle_id))
        
    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, skip])
    
    async with conn.execute(query, tuple(params)) as cursor:
        rows = await cursor.fetchall()
        return [DutyResponse.model_validate(_row_to_response(dict(r), ctx.organisation_id)) for r in rows]


async def get_duty(
    ctx: TenantContext,
    duty_id: uuid.UUID,
) -> DutyResponse:
    conn = await ctx.d1.get_connection()
    async with conn.execute("SELECT * FROM duties WHERE id = ?", (str(duty_id),)) as cursor:
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Duty not found")
        return DutyResponse.model_validate(_row_to_response(dict(row), ctx.organisation_id))


async def assign_duty(
    ctx: TenantContext,
    duty_id: uuid.UUID,
    req: DutyAssignRequest,
) -> DutyResponse:
    conn = await ctx.d1.get_connection()
    
    async with conn.execute("SELECT * FROM duties WHERE id = ?", (str(duty_id),)) as cursor:
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Duty not found")
        
        duty_dict = dict(row)

    if duty_dict.get("status") not in (DutyStatus.UNASSIGNED.value, DutyStatus.CANCELLED.value):
        # We allow reassigning if they are just ASSIGNED, maybe. But if dispatched, block.
        if duty_dict.get("status") not in (DutyStatus.ASSIGNED.value, DutyStatus.DRIVER_ACCEPTANCE_PENDING.value):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Cannot assign driver to duty in status {duty_dict.get('status')}")
            
    # Verify driver and vehicle
    async with conn.execute("SELECT id FROM drivers WHERE id = ?", (str(req.driver_id),)) as cursor:
        if not await cursor.fetchone():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")
            
    async with conn.execute("SELECT id FROM vehicles WHERE id = ?", (str(req.vehicle_id),)) as cursor:
        if not await cursor.fetchone():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")

    new_status = DutyStatus.ASSIGNED.value
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    await conn.execute(
        "UPDATE duties SET driver_id = ?, vehicle_id = ?, status = ?, updated_at = ? WHERE id = ?",
        (str(req.driver_id), str(req.vehicle_id), new_status, now_str, str(duty_id))
    )
    
    await _log_duty_event(conn, str(duty_id), str(ctx.user_id), "DUTY_ASSIGNED", duty_dict.get("status"), new_status)

    await ws_manager.broadcast_to_org(
        ctx.organisation_id,
        "duty.assigned",
        {"duty_id": str(duty_id), "duty_number": duty_dict.get("duty_number")},
    )

    async with conn.execute("SELECT * FROM duties WHERE id = ?", (str(duty_id),)) as cursor:
        updated_row = await cursor.fetchone()
        return DutyResponse.model_validate(_row_to_response(dict(updated_row), ctx.organisation_id))


async def _update_duty_status(ctx: TenantContext, duty_id: uuid.UUID, target_status: DutyStatus, allowed_previous_states: list[str]) -> DutyResponse:
    conn = await ctx.d1.get_connection()
    async with conn.execute("SELECT * FROM duties WHERE id = ?", (str(duty_id),)) as cursor:
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Duty not found")
        duty_dict = dict(row)
        
    current_status = duty_dict.get("status")
    if current_status not in allowed_previous_states:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Invalid transition from {current_status} to {target_status.value}",
        )
        
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await conn.execute(
        "UPDATE duties SET status = ?, updated_at = ? WHERE id = ?",
        (target_status.value, now_str, str(duty_id))
    )
    
    await _log_duty_event(conn, str(duty_id), str(ctx.user_id), f"DUTY_{target_status.value}", current_status, target_status.value)
    
    await ws_manager.broadcast_to_org(
        ctx.organisation_id,
        f"duty.{target_status.value.lower()}",
        {"duty_id": str(duty_id), "duty_number": duty_dict.get("duty_number")},
    )

    async with conn.execute("SELECT * FROM duties WHERE id = ?", (str(duty_id),)) as cursor:
        updated_row = await cursor.fetchone()
        return DutyResponse.model_validate(_row_to_response(dict(updated_row), ctx.organisation_id))


async def dispatch_duty(ctx: TenantContext, duty_id: uuid.UUID) -> DutyResponse:
    return await _update_duty_status(ctx, duty_id, DutyStatus.DISPATCHED, [DutyStatus.ASSIGNED.value, DutyStatus.ACCEPTED.value])

async def driver_accept_duty(ctx: TenantContext, duty_id: uuid.UUID) -> DutyResponse:
    return await _update_duty_status(ctx, duty_id, DutyStatus.ACCEPTED, [DutyStatus.ASSIGNED.value, DutyStatus.DRIVER_ACCEPTANCE_PENDING.value])

async def update_duty_milestone(ctx: TenantContext, duty_id: uuid.UUID, target_status: DutyStatus) -> DutyResponse:
    allowed = []
    if target_status == DutyStatus.ARRIVED_PICKUP:
        allowed = [DutyStatus.DISPATCHED.value]
    elif target_status == DutyStatus.IN_TRANSIT:
        allowed = [DutyStatus.ARRIVED_PICKUP.value]
    elif target_status == DutyStatus.ARRIVED_DROP:
        allowed = [DutyStatus.IN_TRANSIT.value]
    elif target_status == DutyStatus.DUTY_COMPLETED:
        allowed = [DutyStatus.ARRIVED_DROP.value]
        
    return await _update_duty_status(ctx, duty_id, target_status, allowed)

async def driver_reject_duty(ctx: TenantContext, duty_id: uuid.UUID, reason: Optional[str]) -> DutyResponse:
    # Actually just unassign it and put back to unassigned
    conn = await ctx.d1.get_connection()
    async with conn.execute("SELECT * FROM duties WHERE id = ?", (str(duty_id),)) as cursor:
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Duty not found")
        duty_dict = dict(row)
        
    current_status = duty_dict.get("status")
    if current_status not in (DutyStatus.ASSIGNED.value, DutyStatus.DRIVER_ACCEPTANCE_PENDING.value, DutyStatus.DISPATCHED.value):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cannot reject at this stage.")
        
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await conn.execute(
        "UPDATE duties SET status = ?, driver_id = NULL, vehicle_id = NULL, updated_at = ? WHERE id = ?",
        (DutyStatus.UNASSIGNED.value, now_str, str(duty_id))
    )
    
    await _log_duty_event(conn, str(duty_id), str(ctx.user_id), "DUTY_REJECTED", current_status, DutyStatus.UNASSIGNED.value, f'{{"reason": "{reason}"}}')
    
    async with conn.execute("SELECT * FROM duties WHERE id = ?", (str(duty_id),)) as cursor:
        updated_row = await cursor.fetchone()
        return DutyResponse.model_validate(_row_to_response(dict(updated_row), ctx.organisation_id))
