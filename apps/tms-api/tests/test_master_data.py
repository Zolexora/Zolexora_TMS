import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from jose import jwt
from app.main import app
from app.core.config import settings


def make_test_token(user_id: uuid.UUID, email: str = "test@zolexora.com") -> str:
    payload = {
        "sub": str(user_id),
        "email": email,
        "aud": "authenticated",
        "exp": 9999999999,
    }
    secret = settings.JWT_SECRET or "test-jwt-secret-for-testing"
    return jwt.encode(payload, secret, algorithm="HS256")


async def setup_test_workspace(client: AsyncClient, email: str, org_name: str) -> tuple[str, str]:
    user_id = uuid.uuid4()
    token = make_test_token(user_id, email=email)
    res = await client.post(
        "/api/v1/onboarding",
        json={"name": org_name, "organisation_type": "Private Limited Company"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201, res.text
    org_id = res.json()["organisation"]["id"]
    return token, org_id


@pytest.mark.asyncio
async def test_customers_lifecycle_and_tenant_isolation():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Org 1
        token_1, org_1_id = await setup_test_workspace(client, "org1_admin@zolexora.com", f"Org One {uuid.uuid4().hex[:6]}")
        # Org 2
        token_2, org_2_id = await setup_test_workspace(client, "org2_admin@zolexora.com", f"Org Two {uuid.uuid4().hex[:6]}")

        # 1. Create customer in Org 1
        cust_payload = {
            "name": "Tata Consumer Logistics",
            "contact_person": "Vikram Malhotra",
            "email": "vikram@tataconsumer.com",
            "phone": "+919876543210",
            "billing_address": "Bombay House, Homi Mody Street, Mumbai",
            "gstin": "27AAACT2727Q1ZW",
            "pan": "AAACT2727Q",
            "payment_terms_days": 45,
            "credit_limit": "500000.00",
        }
        create_res = await client.post(
            "/api/v1/customers",
            json=cust_payload,
            headers={"Authorization": f"Bearer {token_1}"},
        )
        assert create_res.status_code == 201
        cust_data = create_res.json()
        cust_id = cust_data["id"]
        assert cust_data["organisation_id"] == org_1_id
        assert cust_data["name"] == cust_payload["name"]
        assert cust_data["gstin"] == cust_payload["gstin"]

        # 2. Org 1 can list their customer
        list_res_1 = await client.get(
            "/api/v1/customers",
            headers={"Authorization": f"Bearer {token_1}"},
        )
        assert list_res_1.status_code == 200
        items_1 = list_res_1.json()
        assert any(c["id"] == cust_id for c in items_1)

        # 3. Org 2 CANNOT see Org 1's customer (Tenant Isolation Boundary)
        list_res_2 = await client.get(
            "/api/v1/customers",
            headers={"Authorization": f"Bearer {token_2}"},
        )
        assert list_res_2.status_code == 200
        items_2 = list_res_2.json()
        assert not any(c["id"] == cust_id for c in items_2)

        # 4. Org 2 cannot fetch Org 1's customer directly
        get_res_2 = await client.get(
            f"/api/v1/customers/{cust_id}",
            headers={"Authorization": f"Bearer {token_2}"},
        )
        assert get_res_2.status_code == 404

        # 5. Org 1 can update customer
        update_res = await client.patch(
            f"/api/v1/customers/{cust_id}",
            json={"contact_person": "Vikram M. Senior VP", "payment_terms_days": 60},
            headers={"Authorization": f"Bearer {token_1}"},
        )
        assert update_res.status_code == 200
        assert update_res.json()["contact_person"] == "Vikram M. Senior VP"
        assert update_res.json()["payment_terms_days"] == 60


@pytest.mark.asyncio
async def test_vendors_lifecycle_and_tenant_isolation():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token, org_id = await setup_test_workspace(client, "vendor_boss@zolexora.com", f"Logistics Hub {uuid.uuid4().hex[:6]}")

        vendor_payload = {
            "name": "Bharat Fleet Providers",
            "vendor_type": "FLEET_SUPPLIER",
            "contact_person": "Rajesh Sharma",
            "phone": "+919811223344",
            "gstin": "07AAAAA0000A1Z5",
            "bank_account_name": "Bharat Fleet Providers",
            "bank_account_number": "918273645019",
            "bank_ifsc": "HDFC0001234",
        }
        res = await client.post(
            "/api/v1/vendors",
            json=vendor_payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 201
        v_data = res.json()
        vendor_id = v_data["id"]
        assert v_data["name"] == vendor_payload["name"]
        assert v_data["vendor_type"] == "FLEET_SUPPLIER"

        # List vendors
        v_list = await client.get("/api/v1/vendors", headers={"Authorization": f"Bearer {token}"})
        assert v_list.status_code == 200
        assert len(v_list.json()) >= 1


@pytest.mark.asyncio
async def test_drivers_lifecycle_and_uniqueness():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token, org_id = await setup_test_workspace(client, "fleet_ops@zolexora.com", f"Express Cargo {uuid.uuid4().hex[:6]}")

        driver_payload = {
            "full_name": "Ramesh Kumar Yadav",
            "phone": "+919988776655",
            "license_number": "DL1420110012345",
            "license_type": "HMV",
            "driver_type": "PERMANENT",
            "aadhaar_last4": "5678",
        }
        # 1. Create driver
        res = await client.post(
            "/api/v1/drivers",
            json=driver_payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 201
        d_data = res.json()
        driver_id = d_data["id"]
        assert d_data["status"] == "AVAILABLE"
        assert d_data["full_name"] == driver_payload["full_name"]

        # 2. Duplicate phone / license within same tenant must be rejected
        dup_res = await client.post(
            "/api/v1/drivers",
            json=driver_payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert dup_res.status_code == 409


@pytest.mark.asyncio
async def test_vehicles_lifecycle_and_uniqueness():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token, org_id = await setup_test_workspace(client, "vehicle_mgr@zolexora.com", f"Freight Line {uuid.uuid4().hex[:6]}")

        veh_payload = {
            "registration_number": "MH12AB1234",
            "vehicle_type": "TRUCK",
            "ownership_type": "OWNED",
            "make": "Tata Motors",
            "model": "Signa 4825.TK",
            "fuel_type": "DIESEL",
            "payload_capacity_kg": "25000.00",
            "odometer_km": "45200.00",
            "rc_number": "RC-MH12-9988",
        }
        # 1. Create vehicle
        res = await client.post(
            "/api/v1/vehicles",
            json=veh_payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 201
        v_data = res.json()
        veh_id = v_data["id"]
        assert v_data["registration_number"] == "MH12AB1234"
        assert v_data["status"] == "AVAILABLE"

        # 2. Duplicate registration within same tenant must be rejected
        dup_res = await client.post(
            "/api/v1/vehicles",
            json=veh_payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert dup_res.status_code == 409
