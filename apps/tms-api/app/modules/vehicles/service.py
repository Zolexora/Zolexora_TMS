
import uuid
import datetime
import json
from decimal import Decimal
from typing import Optional
from fastapi import HTTPException, status

from app.core.tenant import TenantContext
from app.core.providers.database import D1TenantProvider
from app.core.storage import upload_document_to_r2
from app.modules.vehicles.models import (
    VehicleBodyType,
    VehicleOperationalStatus,
    VehicleOwnershipType,
)
from app.modules.vehicles.schemas import VehicleCreate, VehicleResponse, VehicleUpdate


def _row_to_response(row: dict, org_id: uuid.UUID) -> VehicleResponse:
    docs = row.get("documents")
    if isinstance(docs, str):
        try:
            docs = json.loads(docs)
        except:
            docs = {}
    elif not docs:
        docs = {}
    
    return VehicleResponse(
        id=uuid.UUID(row["id"]),
        organisation_id=org_id,
        vendor_id=uuid.UUID(row["vendor_id"]) if row.get("vendor_id") else None,
        registration_number=row["registration_number"],
        vehicle_type=VehicleBodyType(row["vehicle_type"]) if row.get("vehicle_type") else VehicleBodyType.TRUCK,
        ownership_type=VehicleOwnershipType(row["ownership_type"]) if row.get("ownership_type") else VehicleOwnershipType.OWNED,
        make=row.get("make"),
        model=row.get("model"),
        year=row.get("year"),
        fuel_type=row.get("fuel_type") or "DIESEL",
        payload_capacity_kg=Decimal(str(row["payload_capacity_kg"])) if row.get("payload_capacity_kg") is not None else None,
        volume_cft=Decimal(str(row["volume_cft"])) if row.get("volume_cft") is not None else None,
        odometer_km=Decimal(str(row["odometer_km"])) if row.get("odometer_km") is not None else Decimal("0.0"),
        fastag_id=row.get("fastag_id"),
        gps_device_id=row.get("gps_device_id"),
        rc_number=row.get("rc_number"),
        rc_expiry=datetime.datetime.strptime(row["rc_expiry"][:10], "%Y-%m-%d").date() if row.get("rc_expiry") else None,
        fitness_expiry=datetime.datetime.strptime(row["fitness_expiry"][:10], "%Y-%m-%d").date() if row.get("fitness_expiry") else None,
        permit_expiry=datetime.datetime.strptime(row["permit_expiry"][:10], "%Y-%m-%d").date() if row.get("permit_expiry") else None,
        insurance_expiry=datetime.datetime.strptime(row["insurance_expiry"][:10], "%Y-%m-%d").date() if row.get("insurance_expiry") else None,
        puc_expiry=datetime.datetime.strptime(row["puc_expiry"][:10], "%Y-%m-%d").date() if row.get("puc_expiry") else None,
        status=VehicleOperationalStatus(row["status"]) if row.get("status") else VehicleOperationalStatus.AVAILABLE,
        documents=docs,
        created_at=datetime.datetime.strptime(row["created_at"], "%Y-%m-%d %H:%M:%S") if row.get("created_at") else datetime.datetime.now(),
        updated_at=datetime.datetime.strptime(row["updated_at"], "%Y-%m-%d %H:%M:%S") if row.get("updated_at") else datetime.datetime.now(),
    )


async def create_vehicle(
    org_id: uuid.UUID,
    actor_id: uuid.UUID,
    req: VehicleCreate,
    tenant_ctx: TenantContext,
) -> VehicleResponse:
    reg_clean = req.registration_number.strip().upper().replace(" ", "")

    provider = D1TenantProvider(tenant_ctx.tenant_database_identifier)
    conn = await provider.get_connection()
    
    try:
        async with conn.execute("SELECT id FROM vehicles WHERE registration_number = ?", (reg_clean,)) as cursor:
            if await cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Vehicle '{reg_clean}' is already registered in your organisation",
                )

        vehicle_id = str(uuid.uuid4())
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        docs_json = json.dumps(req.documents)
        
        await conn.execute(
            """
            INSERT INTO vehicles (
                id, vendor_id, registration_number, vehicle_type, ownership_type,
                make, model, year, fuel_type, payload_capacity_kg, volume_cft,
                odometer_km, fastag_id, gps_device_id, rc_number, rc_expiry,
                fitness_expiry, permit_expiry, insurance_expiry, puc_expiry,
                status, documents, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                vehicle_id,
                str(req.vendor_id) if req.vendor_id else None,
                reg_clean,
                req.vehicle_type.value if req.vehicle_type else None,
                req.ownership_type.value if req.ownership_type else None,
                req.make.strip() if req.make else None,
                req.model.strip() if req.model else None,
                req.year,
                req.fuel_type.value if req.fuel_type else None,
                float(req.payload_capacity_kg) if req.payload_capacity_kg else None,
                float(req.volume_cft) if req.volume_cft else None,
                float(req.odometer_km) if req.odometer_km else 0.0,
                req.fastag_id.strip() if req.fastag_id else None,
                req.gps_device_id.strip() if req.gps_device_id else None,
                req.rc_number.strip().upper() if req.rc_number else None,
                req.rc_expiry.strftime("%Y-%m-%d") if req.rc_expiry else None,
                req.fitness_expiry.strftime("%Y-%m-%d") if req.fitness_expiry else None,
                req.permit_expiry.strftime("%Y-%m-%d") if req.permit_expiry else None,
                req.insurance_expiry.strftime("%Y-%m-%d") if req.insurance_expiry else None,
                req.puc_expiry.strftime("%Y-%m-%d") if req.puc_expiry else None,
                VehicleOperationalStatus.AVAILABLE.value,
                docs_json,
                now_str,
                now_str
            )
        )
        await conn.commit()
        
        async with conn.execute("SELECT * FROM vehicles WHERE id = ?", (vehicle_id,)) as cursor:
            row = await cursor.fetchone()
            return _row_to_response(dict(row), org_id)
            
    finally:
        await provider.close()


async def list_vehicles(
    org_id: uuid.UUID,
    tenant_ctx: TenantContext,
    status_filter: Optional[VehicleOperationalStatus] = None,
    vehicle_type: Optional[VehicleBodyType] = None,
    ownership_type: Optional[VehicleOwnershipType] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> list[VehicleResponse]:
    
    provider = D1TenantProvider(tenant_ctx.tenant_database_identifier)
    conn = await provider.get_connection()
    
    try:
        query = "SELECT * FROM vehicles WHERE 1=1"
        params = []
        
        if status_filter:
            query += " AND status = ?"
            params.append(status_filter.value)
            
        if vehicle_type:
            query += " AND vehicle_type = ?"
            params.append(vehicle_type.value)
            
        if ownership_type:
            query += " AND ownership_type = ?"
            params.append(ownership_type.value)
            
        if search:
            query += " AND (registration_number LIKE ? OR make LIKE ? OR model LIKE ?)"
            pat = f"%{search.strip().upper()}%"
            params.extend([pat, pat, pat])
            
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, skip])
        
        async with conn.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [_row_to_response(dict(r), org_id) for r in rows]
            
    finally:
        await provider.close()


async def get_vehicle(
    org_id: uuid.UUID,
    vehicle_id: uuid.UUID,
    tenant_ctx: TenantContext,
) -> VehicleResponse:
    provider = D1TenantProvider(tenant_ctx.tenant_database_identifier)
    conn = await provider.get_connection()
    
    try:
        async with conn.execute("SELECT * FROM vehicles WHERE id = ?", (str(vehicle_id),)) as cursor:
            row = await cursor.fetchone()
            if not row:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
            return _row_to_response(dict(row), org_id)
    finally:
        await provider.close()


async def update_vehicle(
    org_id: uuid.UUID,
    vehicle_id: uuid.UUID,
    actor_id: uuid.UUID,
    req: VehicleUpdate,
    tenant_ctx: TenantContext,
) -> VehicleResponse:
    provider = D1TenantProvider(tenant_ctx.tenant_database_identifier)
    conn = await provider.get_connection()
    
    try:
        async with conn.execute("SELECT * FROM vehicles WHERE id = ?", (str(vehicle_id),)) as cursor:
            row = await cursor.fetchone()
            if not row:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
        
        update_data = req.model_dump(exclude_unset=True)
        if not update_data:
            return _row_to_response(dict(row), org_id)
            
        set_clauses = []
        params = []
        
        if "registration_number" in update_data and update_data["registration_number"]:
            reg_clean = update_data["registration_number"].strip().upper().replace(" ", "")
            set_clauses.append("registration_number = ?")
            params.append(reg_clean)
            
        for field, val in update_data.items():
            if field == "registration_number":
                continue
            
            # Map types
            if isinstance(val, (datetime.date, datetime.datetime)):
                val = val.strftime("%Y-%m-%d")
            elif hasattr(val, "value"): # Enum
                val = val.value
            elif isinstance(val, Decimal):
                val = float(val)
            elif isinstance(val, uuid.UUID):
                val = str(val)
            elif isinstance(val, dict):
                val = json.dumps(val)
            elif isinstance(val, str):
                val = val.strip()
                if field in ("rc_number", "fastag_id", "gps_device_id"):
                    val = val.upper()
                    
            set_clauses.append(f"{field} = ?")
            params.append(val)
            
        if set_clauses:
            set_clauses.append("updated_at = ?")
            params.append(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            
            query = f"UPDATE vehicles SET {', '.join(set_clauses)} WHERE id = ?"
            params.append(str(vehicle_id))
            
            await conn.execute(query, params)
            await conn.commit()
            
        async with conn.execute("SELECT * FROM vehicles WHERE id = ?", (str(vehicle_id),)) as cursor:
            row = await cursor.fetchone()
            return _row_to_response(dict(row), org_id)
            
    finally:
        await provider.close()


async def delete_vehicle(
    org_id: uuid.UUID,
    vehicle_id: uuid.UUID,
    actor_id: uuid.UUID,
    tenant_ctx: TenantContext,
) -> None:
    provider = D1TenantProvider(tenant_ctx.tenant_database_identifier)
    conn = await provider.get_connection()
    
    try:
        async with conn.execute("SELECT id FROM vehicles WHERE id = ?", (str(vehicle_id),)) as cursor:
            if not await cursor.fetchone():
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
        
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        await conn.execute(
            "UPDATE vehicles SET status = ?, updated_at = ? WHERE id = ?",
            (VehicleOperationalStatus.DECOMMISSIONED.value, now_str, str(vehicle_id))
        )
        await conn.commit()
    finally:
        await provider.close()


async def upload_vehicle_doc(
    org_id: uuid.UUID,
    vehicle_id: uuid.UUID,
    doc_type: str,
    file_name: str,
    file_bytes: bytes,
    content_type: str,
    tenant_ctx: TenantContext,
) -> str:
    provider = D1TenantProvider(tenant_ctx.tenant_database_identifier)
    conn = await provider.get_connection()
    
    try:
        async with conn.execute("SELECT documents FROM vehicles WHERE id = ?", (str(vehicle_id),)) as cursor:
            row = await cursor.fetchone()
            if not row:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
            
        url = await upload_document_to_r2(
            file_bytes=file_bytes,
            file_name=file_name,
            content_type=content_type,
            folder=f"tenants/{org_id}/vehicles/{vehicle_id}",
        )
        
        docs_str = row["documents"]
        try:
            docs = json.loads(docs_str) if docs_str else {}
        except:
            docs = {}
            
        docs[doc_type] = url
        
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        await conn.execute(
            "UPDATE vehicles SET documents = ?, updated_at = ? WHERE id = ?",
            (json.dumps(docs), now_str, str(vehicle_id))
        )
        await conn.commit()
        return url
        
    finally:
        await provider.close()

