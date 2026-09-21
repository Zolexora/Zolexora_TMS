import datetime
import uuid
import json
from typing import Optional
from fastapi import HTTPException, status

from app.auth.dependencies import TenantContext
from app.core.geocoding import geocoding_service
from app.core.websocket import ws_manager
from app.modules.bookings.schemas import BookingCreate, BookingResponse, BookingUpdate, BookingStatus


def _row_to_response(row: dict, org_id: uuid.UUID) -> dict:
    # Handle JSON fields
    for json_col in ["passenger_info", "cargo_info", "vehicle_requirements", "driver_requirements", "commercial_terms", "metadata_"]:
        if json_col in row and isinstance(row[json_col], str):
            try:
                row[json_col] = json.loads(row[json_col])
            except:
                row[json_col] = {}
                
    row["organisation_id"] = org_id
    if "metadata" in row and "metadata_" not in row:
        row["metadata_"] = row.get("metadata", {})
        
    return row


async def create_booking(
    ctx: TenantContext,
    req: BookingCreate,
) -> BookingResponse:
    conn = await ctx.d1.get_connection()
    
    # 1. Verify customer exists in tenant
    async with conn.execute("SELECT id FROM customers WHERE id = ?", (str(req.customer_id),)) as cursor:
        c_res = await cursor.fetchone()
        if not c_res:
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

    booking_id = str(uuid.uuid4())
    booking_num = f"BK-{datetime.datetime.now().year}-{booking_id[:6].upper()}"
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    await conn.execute(
        """
        INSERT INTO bookings (
            id, booking_number, booking_request_id, customer_id, service_type,
            pickup_address, pickup_lat, pickup_lng, drop_address, drop_lat, drop_lng,
            pickup_datetime, expected_completion_datetime, passenger_info, vehicle_requirements,
            commercial_terms, operational_instructions, status, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            booking_id,
            booking_num,
            str(req.booking_request_id) if req.booking_request_id else None,
            str(req.customer_id),
            req.service_type.value,
            req.pickup_address.strip(),
            p_lat,
            p_lng,
            req.drop_address.strip(),
            d_lat,
            d_lng,
            req.pickup_datetime.strftime("%Y-%m-%d %H:%M:%S") if req.pickup_datetime else None,
            req.expected_completion_datetime.strftime("%Y-%m-%d %H:%M:%S") if req.expected_completion_datetime else None,
            json.dumps(req.passenger_info),
            json.dumps(req.vehicle_requirements),
            json.dumps(req.commercial_terms),
            req.operational_instructions,
            BookingStatus.CONFIRMED.value,
            now_str,
            now_str
        )
    )

    # TODO: Add audit log to MongoDB

    await ws_manager.broadcast_to_org(
        ctx.organisation_id,
        "booking.created",
        {"booking_id": booking_id, "booking_number": booking_num, "customer_id": str(req.customer_id)},
    )

    async with conn.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,)) as cursor:
        row = await cursor.fetchone()
        return BookingResponse.model_validate(_row_to_response(dict(row), ctx.organisation_id))


async def list_bookings(
    ctx: TenantContext,
    status_filter: Optional[BookingStatus] = None,
    customer_id: Optional[uuid.UUID] = None,
    skip: int = 0,
    limit: int = 50,
) -> list[BookingResponse]:
    conn = await ctx.d1.get_connection()
    
    query = "SELECT * FROM bookings WHERE 1=1"
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
        return [BookingResponse.model_validate(_row_to_response(dict(r), ctx.organisation_id)) for r in rows]


async def get_booking(
    ctx: TenantContext,
    booking_id: uuid.UUID,
) -> BookingResponse:
    conn = await ctx.d1.get_connection()
    async with conn.execute("SELECT * FROM bookings WHERE id = ?", (str(booking_id),)) as cursor:
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
        return BookingResponse.model_validate(_row_to_response(dict(row), ctx.organisation_id))


async def cancel_booking(
    ctx: TenantContext,
    booking_id: uuid.UUID,
    reason: Optional[str],
) -> BookingResponse:
    conn = await ctx.d1.get_connection()
    async with conn.execute("SELECT * FROM bookings WHERE id = ?", (str(booking_id),)) as cursor:
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
            
        booking_dict = dict(row)
        current_status = booking_dict.get("status")

    if current_status in (BookingStatus.COMPLETED.value, BookingStatus.CANCELLED.value):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel booking with status '{current_status}'.",
        )

    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await conn.execute(
        "UPDATE bookings SET status = ?, updated_at = ? WHERE id = ?",
        (BookingStatus.CANCELLED.value, now_str, str(booking_id))
    )

    # TODO: Log audit to mongo

    await ws_manager.broadcast_to_org(
        ctx.organisation_id,
        "booking.cancelled",
        {"booking_id": str(booking_id), "booking_number": booking_dict.get("booking_number")},
    )

    async with conn.execute("SELECT * FROM bookings WHERE id = ?", (str(booking_id),)) as cursor:
        updated_row = await cursor.fetchone()
        return BookingResponse.model_validate(_row_to_response(dict(updated_row), ctx.organisation_id))

