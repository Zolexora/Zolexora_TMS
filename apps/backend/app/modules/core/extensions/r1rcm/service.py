import uuid
import csv
import io
import json
from datetime import datetime
from typing import List, Dict, Any
from fastapi import HTTPException, UploadFile

from app.auth.dependencies import TenantContext
from app.modules.core.extensions.r1rcm.schemas import (
    R1ExcelRow, ValidationResult, R1ImportPreviewResponse, R1ConfirmImportRequest
)
from app.modules.operations.bookings.schemas import BookingCreate
from app.modules.operations.bookings import service as booking_service

# In-memory store for staging batches. In production, store this in MongoDB or D1 staging table.
_import_batches = {}

async def process_excel_upload(
    ctx: TenantContext,
    file: UploadFile,
    customer_id: uuid.UUID,
    location: str
) -> R1ImportPreviewResponse:
    content = await file.read()
    
    # Simple CSV parser to simulate Excel
    try:
        text = content.decode('utf-8')
        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid CSV format")

    results = []
    valid_count = 0
    error_count = 0
    warning_count = 0
    
    batch_id = uuid.uuid4()
    
    for idx, row in enumerate(rows):
        errors = []
        warnings = []
        
        # Clean keys
        clean_row = {k.strip().lower(): v.strip() for k, v in row.items() if k}
        
        r1_row = R1ExcelRow(
            date=clean_row.get("date", ""),
            trip_id=clean_row.get("trip_id", ""),
            employee_id=clean_row.get("employee_id", ""),
            employee_name=clean_row.get("employee_name", ""),
            shift=clean_row.get("shift", ""),
            location=clean_row.get("location", ""),
            pickup=clean_row.get("pickup", ""),
            drop=clean_row.get("drop", ""),
            route_number=clean_row.get("route_number", ""),
            cab_type=clean_row.get("cab_type", ""),
            vendor=clean_row.get("vendor", ""),
            vehicle_number=clean_row.get("vehicle_number", ""),
            rate=clean_row.get("rate", ""),
        )
        
        if not r1_row.employee_id:
            errors.append("Missing Employee ID")
        if not r1_row.trip_id:
            errors.append("Missing Trip ID")
        if not r1_row.vehicle_number:
            warnings.append("Vehicle Number not provided - will require manual assignment")
            
        # Add basic D1 duplicate checking logic (mocked for preview)
        # conn = await ctx.d1.get_connection()
        # async with conn.execute("SELECT id FROM bookings WHERE ...")
            
        is_valid = len(errors) == 0
        if is_valid:
            valid_count += 1
        else:
            error_count += 1
            
        if warnings:
            warning_count += 1
            
        results.append(ValidationResult(
            row_index=idx + 1,
            row_data=r1_row,
            is_valid=is_valid,
            errors=errors,
            warnings=warnings
        ))
        
    _import_batches[str(batch_id)] = {
        "customer_id": customer_id,
        "location": location,
        "results": results
    }
    
    return R1ImportPreviewResponse(
        batch_id=batch_id,
        total_rows=len(results),
        valid_count=valid_count,
        error_count=error_count,
        warning_count=warning_count,
        results=results
    )

async def confirm_import(
    ctx: TenantContext,
    req: R1ConfirmImportRequest
) -> Dict[str, Any]:
    batch = _import_batches.get(str(req.batch_id))
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found or expired")
        
    if str(batch["customer_id"]) != str(req.customer_id) or batch["location"] != req.location:
        raise HTTPException(status_code=403, detail="Batch does not match customer and location scope")
        
    results = batch["results"]
    valid_results = [r for r in results if r.is_valid]
    
    created = 0
    conn = await ctx.d1.get_connection()
    
    for r in valid_results:
        # Map R1ExcelRow to D1 Bookings and Duties
        booking_id = str(uuid.uuid4())
        
        # Insert booking
        await conn.execute(
            """INSERT INTO bookings (id, customer_id, pickup_location, dropoff_location, scheduled_at, status)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (booking_id, str(req.customer_id), r.row_data.pickup, r.row_data.drop, r.row_data.date, 'PENDING')
        )
        
        # Insert Duty
        duty_id = str(uuid.uuid4())
        await conn.execute(
            """INSERT INTO duties (id, booking_id, status) VALUES (?, ?, ?)""",
            (duty_id, booking_id, 'UNASSIGNED')
        )
        created += 1
        
    del _import_batches[str(req.batch_id)]
    
    return {"status": "success", "created_bookings": created}
