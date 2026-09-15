import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from jose import jwt
from app.main import app
import os
from dotenv import load_dotenv
load_dotenv()
from app.core.config import settings

def make_test_token(user_id: uuid.UUID, email: str) -> str:
    payload = {
        "sub": str(user_id),
        "email": email,
        "aud": "authenticated",
        "exp": 9999999999,
    }
    secret = settings.JWT_SECRET or "test-jwt-secret-for-testing"
    return jwt.encode(payload, secret, algorithm="HS256")

@pytest.mark.asyncio
async def test_booking_to_duty_lifecycle():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create Organisation A with User A
        user_a = uuid.uuid4()
        token_a = make_test_token(user_a, "user_a_lifecycle@tenant-a.com")
        res_a = await client.post(
            "/api/v1/onboarding",
            json={"name": f"Lifecycle Tenant {uuid.uuid4().hex[:6]}", "organisation_type": "Private Limited Company"},
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert res_a.status_code == 201, res_a.text
        
        headers = {"Authorization": f"Bearer {token_a}"}
        
        from app.db.session import AsyncSessionLocal
        from sqlalchemy import text
        from app.core.providers.database import D1TenantProvider
        
        
        async with AsyncSessionLocal() as session:
            # Get organisation to get tenant database
            org = await session.execute(text(f"SELECT database_registry_id FROM organisation_database_assignments WHERE organisation_id = '{res_a.json()['organisation']['id']}'"))
            tenant_db_id = org.scalar_one()
            
            reg = await session.execute(text(f"SELECT database_identifier FROM tenant_database_registry WHERE id = '{tenant_db_id}'"))
            d1_uuid = reg.scalar_one()
            
        provider = D1TenantProvider(d1_uuid)
        conn = await provider.get_connection()
        
        cust_id = str(uuid.uuid4())
        await conn.execute("INSERT INTO customers (id, name, email) VALUES (?, ?, ?)", (cust_id, "Test Customer", "cust@test.com"))
        driver_id = str(uuid.uuid4())
        await conn.execute("INSERT INTO drivers (id, name, status) VALUES (?, ?, ?)", (driver_id, "Test Driver", "AVAILABLE"))
        vehicle_id = str(uuid.uuid4())
        await conn.execute("INSERT INTO vehicles (id, registration_number, status) VALUES (?, ?, ?)", (vehicle_id, "KA01AB1234", "AVAILABLE"))

        # 1. Create Booking Request
        req_payload = {
            "customer_id": cust_id,
            "booking_type": "SPOT",
            "service_type": "CARGO",
            "pickup_address": "Test Pickup",
            "drop_address": "Test Drop",
            "pickup_datetime": "2026-10-01T10:00:00Z"
        }
        res = await client.post("/api/v1/booking-requests", json=req_payload, headers=headers)
        assert res.status_code == 201, res.text
        req_id = res.json()["id"]

        # 2. Submit Booking Request
        res = await client.post(f"/api/v1/booking-requests/{req_id}/submit", headers=headers)
        assert res.status_code == 200, res.text
        assert res.json()["status"] == "REQUESTED"

        # 3. Confirm Booking Request -> Creates Booking
        res = await client.post(f"/api/v1/booking-requests/{req_id}/confirm", headers=headers)
        assert res.status_code == 200, res.text
        booking = res.json()
        assert booking["status"] == "CONFIRMED"
        booking_id = booking["id"]

        # 4. Create Duty from Booking
        duty_payload = {
            "scheduled_start_time": "2026-10-01T10:00:00Z",
            "scheduled_end_time": "2026-10-01T18:00:00Z"
        }
        res = await client.post(f"/api/v1/bookings/{booking_id}/create-duty", json=duty_payload, headers=headers)
        assert res.status_code == 201, res.text
        duty = res.json()
        assert duty["status"] == "UNASSIGNED"
        duty_id = duty["id"]

        # 5. Assign Driver & Vehicle
        res = await client.post(f"/api/v1/duties/{duty_id}/assign", json={"driver_id": driver_id, "vehicle_id": vehicle_id}, headers=headers)
        assert res.status_code == 200, res.text
        assert res.json()["status"] == "ASSIGNED"

        # 6. Dispatch Duty
        res = await client.post(f"/api/v1/duties/{duty_id}/dispatch", headers=headers)
        assert res.status_code == 200, res.text
        assert res.json()["status"] == "DISPATCHED"
        
        # 7. Milestone updates
        res = await client.post(f"/api/v1/duties/{duty_id}/arrived-pickup", headers=headers)
        assert res.status_code == 200, res.text
        assert res.json()["status"] == "ARRIVED_PICKUP"

        res = await client.post(f"/api/v1/duties/{duty_id}/in-transit", headers=headers)
        assert res.status_code == 200, res.text
        assert res.json()["status"] == "IN_TRANSIT"

        res = await client.post(f"/api/v1/duties/{duty_id}/arrived-drop", headers=headers)
        assert res.status_code == 200, res.text
        assert res.json()["status"] == "ARRIVED_DROP"
        
        res = await client.post(f"/api/v1/duties/{duty_id}/complete", headers=headers)
        assert res.status_code == 200, res.text
        assert res.json()["status"] == "DUTY_COMPLETED"
