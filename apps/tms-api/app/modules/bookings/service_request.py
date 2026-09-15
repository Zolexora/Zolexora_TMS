import datetime
import uuid
import json
from decimal import Decimal
from typing import Optional
from fastapi import HTTPException, status

from app.auth.dependencies import TenantContext
from app.core.geocoding import geocoding_service
from app.core.websocket import ws_manager
from app.modules.bookings.schemas_request import (
    BookingRequestCreate,
    BookingRequestResponse,
)
from app.modules.bookings.enums import BookingRequestStatus, BookingStatus
from app.modules.bookings.schemas import BookingResponse

def _row_to_request_response(row: dict, org_id: uuid.UUID) -> dict:
    for json_col in ["passenger_info", "cargo_info", "vehicle_requirements"]:
        if json_col in row and isinstance(row[json_col], str):
            try:
                row[json_col] = json.loads(row[json_col])
            except:
                row[json_col] = {}
    row["organisation_id"] = org_id
    if "booking_request_number" in row:
        row["request_number"] = row["booking_request_number"]
    if "special_requirements" in row:
        row["special_instructions"] = row["special_requirements"]
    if row.get("estimated_pricing") is not None:
        row["estimated_pricing"] = Decimal(str(row["estimated_pricing"]))
    return row

async def create_booking_request(ctx: TenantContext, req: BookingRequestCreate) -> BookingRequestResponse:
    conn = await ctx.d1.get_connection()
    async with conn.execute("SELECT id FROM customers WHERE id = ?", (str(req.customer_id),)) as cursor:
        if not await cursor.fetchone():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found in organisation")

    req_id = str(uuid.uuid4())
    req_num = f"REQ-{datetime.datetime.now().year}-{req_id[:6].upper()}"
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    await conn.execute(
        """
        INSERT INTO booking_requests (
            id, booking_request_number, customer_id, service_type, pickup_address, drop_address, pickup_datetime,
            passenger_info, vehicle_requirements, special_requirements, status, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            req_id, req_num, str(req.customer_id), req.service_type.value, req.pickup_address, req.drop_address,
            req.pickup_datetime.strftime("%Y-%m-%d %H:%M:%S"), json.dumps(req.passenger_info),
            json.dumps(req.vehicle_requirements), req.special_instructions, BookingRequestStatus.DRAFT.value,
            now_str, now_str
        )
    )

    await ws_manager.broadcast_to_org(
        ctx.organisation_id, "booking_request.created", {"request_id": req_id}
    )

    async with conn.execute("SELECT * FROM booking_requests WHERE id = ?", (req_id,)) as cursor:
        row = await cursor.fetchone()
        return BookingRequestResponse.model_validate(_row_to_request_response(dict(row), ctx.organisation_id))

async def list_booking_requests(
    ctx: TenantContext,
    status_filter: Optional[BookingRequestStatus] = None,
    customer_id: Optional[uuid.UUID] = None,
    skip: int = 0,
    limit: int = 50,
) -> list[BookingRequestResponse]:
    conn = await ctx.d1.get_connection()
    query = "SELECT * FROM booking_requests WHERE 1=1"
    params = []
    
    if status_filter:
        query += " AND status = ?"
        params.append(status_filter.value)
    if customer_id:
        query += " AND customer_id = ?"
        params.append(str(customer_id))
        
    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, skip])
    
    async with conn.execute(query, tuple(params)) as cursor:
        rows = await cursor.fetchall()
        return [BookingRequestResponse.model_validate(_row_to_request_response(dict(r), ctx.organisation_id)) for r in rows]

async def get_booking_request(ctx: TenantContext, request_id: uuid.UUID) -> BookingRequestResponse:
    conn = await ctx.d1.get_connection()
    async with conn.execute("SELECT * FROM booking_requests WHERE id = ?", (str(request_id),)) as cursor:
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking request not found")
        return BookingRequestResponse.model_validate(_row_to_request_response(dict(row), ctx.organisation_id))

async def submit_booking_request(ctx: TenantContext, request_id: uuid.UUID) -> BookingRequestResponse:
    conn = await ctx.d1.get_connection()
    async with conn.execute("SELECT * FROM booking_requests WHERE id = ?", (str(request_id),)) as cursor:
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
        req_dict = dict(row)

    if req_dict.get("status") != BookingRequestStatus.DRAFT.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Can only submit DRAFT requests")

    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await conn.execute(
        "UPDATE booking_requests SET status = ?, updated_at = ? WHERE id = ?",
        (BookingRequestStatus.REQUESTED.value, now_str, str(request_id))
    )

    await ws_manager.broadcast_to_org(ctx.organisation_id, "booking_request.submitted", {"request_id": str(request_id)})
    
    async with conn.execute("SELECT * FROM booking_requests WHERE id = ?", (str(request_id),)) as cursor:
        updated_row = await cursor.fetchone()
        return BookingRequestResponse.model_validate(_row_to_request_response(dict(updated_row), ctx.organisation_id))

async def confirm_booking_request(ctx: TenantContext, request_id: uuid.UUID) -> BookingResponse:
    conn = await ctx.d1.get_connection()
    async with conn.execute("SELECT * FROM booking_requests WHERE id = ?", (str(request_id),)) as cursor:
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
        req_dict = dict(row)

    if req_dict.get("status") not in (BookingRequestStatus.REQUESTED.value, BookingRequestStatus.DRAFT.value):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot confirm request from this status")

    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await conn.execute(
        "UPDATE booking_requests SET status = ?, updated_at = ? WHERE id = ?",
        (BookingRequestStatus.CONFIRMED.value, now_str, str(request_id))
    )
    
    # Create the Booking!
    from app.modules.bookings.service import _row_to_response
    booking_id = str(uuid.uuid4())
    booking_num = f"BK-{datetime.datetime.now().year}-{booking_id[:6].upper()}"

    await conn.execute(
        """
        INSERT INTO bookings (
            id, booking_number, booking_request_id, customer_id, service_type,
            pickup_address, drop_address, pickup_datetime, passenger_info, vehicle_requirements,
            status, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            booking_id, booking_num, str(request_id), req_dict["customer_id"], req_dict["service_type"],
            req_dict["pickup_address"], req_dict["drop_address"], req_dict["pickup_datetime"],
            req_dict["passenger_info"], req_dict["vehicle_requirements"],
            BookingStatus.CONFIRMED.value, now_str, now_str
        )
    )

    await ws_manager.broadcast_to_org(ctx.organisation_id, "booking_request.confirmed", {"request_id": str(request_id)})
    
    async with conn.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,)) as cursor:
        booking_row = await cursor.fetchone()
        return BookingResponse.model_validate(_row_to_response(dict(booking_row), ctx.organisation_id))


async def cancel_booking_request(ctx: TenantContext, request_id: uuid.UUID, reason: Optional[str]) -> BookingRequestResponse:
    conn = await ctx.d1.get_connection()
    async with conn.execute("SELECT * FROM booking_requests WHERE id = ?", (str(request_id),)) as cursor:
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
        req_dict = dict(row)

    if req_dict.get("status") in (BookingRequestStatus.CANCELLED.value, BookingRequestStatus.CONFIRMED.value):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot cancel from this status")

    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await conn.execute(
        "UPDATE booking_requests SET status = ?, updated_at = ? WHERE id = ?",
        (BookingRequestStatus.CANCELLED.value, now_str, str(request_id))
    )

    await ws_manager.broadcast_to_org(ctx.organisation_id, "booking_request.cancelled", {"request_id": str(request_id)})
    
    async with conn.execute("SELECT * FROM booking_requests WHERE id = ?", (str(request_id),)) as cursor:
        updated_row = await cursor.fetchone()
        return BookingRequestResponse.model_validate(_row_to_request_response(dict(updated_row), ctx.organisation_id))

