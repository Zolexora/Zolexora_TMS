import datetime
from decimal import Decimal
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


async def setup_test_workspace(client: AsyncClient, email: str, org_name: str) -> tuple[str, str, uuid.UUID]:
    user_id = uuid.uuid4()
    token = make_test_token(user_id, email=email)
    res = await client.post(
        "/api/v1/onboarding",
        json={"name": org_name, "organisation_type": "Private Limited Company"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201, res.text
    org_id = res.json()["organisation"]["id"]
    return token, org_id, user_id


async def create_test_customer(client: AsyncClient, token: str) -> str:
    res = await client.post(
        "/api/v1/customers",
        json={
            "name": f"Enterprise Customer {uuid.uuid4().hex[:6]}",
            "contact_person": "Operations Lead",
            "email": f"ops_{uuid.uuid4().hex[:6]}@client.com",
            "phone": "+919876543210",
            "billing_address": "BKC Complex, Mumbai",
            "gstin": "27AAACT2727Q1ZW",
            "pan": "AAACT2727Q",
            "payment_terms_days": 30,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201, res.text
    return res.json()["id"]


async def create_test_driver(
    client: AsyncClient,
    token: str,
    license_expired: bool = False,
) -> str:
    today = datetime.date.today()
    expiry = today - datetime.timedelta(days=30) if license_expired else today + datetime.timedelta(days=365)
    res = await client.post(
        "/api/v1/drivers",
        json={
            "full_name": f"Driver {uuid.uuid4().hex[:6]}",
            "phone": f"+9198{uuid.uuid4().int % 100000000:08d}",
            "license_number": f"DL{uuid.uuid4().hex[:10].upper()}",
            "license_type": "HMV",
            "license_expiry": expiry.isoformat(),
            "driver_type": "PERMANENT",
            "aadhaar_last4": "1234",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201, res.text
    return res.json()["id"]


async def create_test_vehicle(
    client: AsyncClient,
    token: str,
    status: str = "AVAILABLE",
) -> str:
    res = await client.post(
        "/api/v1/vehicles",
        json={
            "registration_number": f"MH{uuid.uuid4().hex[:2].upper()}{uuid.uuid4().int % 10000:04d}",
            "vehicle_type": "TRUCK",
            "ownership_type": "OWNED",
            "make": "Tata",
            "model": "Signa",
            "fuel_type": "DIESEL",
            "payload_capacity_kg": "16000.00",
            "odometer_km": "50000.00",
            "rc_number": f"RC-{uuid.uuid4().hex[:6].upper()}",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201, res.text
    veh_id = res.json()["id"]
    if status != "AVAILABLE":
        patch_res = await client.patch(
            f"/api/v1/vehicles/{veh_id}",
            json={"status": status},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert patch_res.status_code == 200, patch_res.text
    return veh_id


@pytest.mark.asyncio
async def test_booking_requests_to_authoritative_booking():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token, org_id, user_id = await setup_test_workspace(
            client, "ops_admin@zolexora.com", f"Zolexora Express {uuid.uuid4().hex[:6]}"
        )
        cust_id = await create_test_customer(client, token)

        now = datetime.datetime.now(datetime.timezone.utc)
        pickup_time = now + datetime.timedelta(hours=4)

        # 1. Create draft booking request
        req_payload = {
            "customer_id": cust_id,
            "booking_type": "SPOT",
            "service_type": "CARGO",
            "pickup_address": "Warehouse 4, Bhiwandi, Maharashtra",
            "drop_address": "Distribution Hub, JNPT Port, Navi Mumbai",
            "pickup_datetime": pickup_time.isoformat(),
            "cargo_info": {"weight_kg": 5000, "material": "Electronics"},
            "vehicle_requirements": {"type": "TRUCK", "capacity_tons": 7},
            "source": "WEB_PORTAL",
            "estimated_pricing": "18500.00",
        }
        create_res = await client.post(
            "/api/v1/booking-requests",
            json=req_payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert create_res.status_code == 201, create_res.text
        req_data = create_res.json()
        req_id = req_data["id"]
        assert req_data["request_number"].startswith("BR-")
        assert req_data["status"] == "DRAFT"

        # 2. Submit request
        submit_res = await client.post(
            f"/api/v1/booking-requests/{req_id}/submit",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert submit_res.status_code == 200
        assert submit_res.json()["status"] == "REQUESTED"

        # 3. Confirm request -> Generates authoritative Booking
        confirm_res = await client.post(
            f"/api/v1/booking-requests/{req_id}/confirm",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert confirm_res.status_code == 200, confirm_res.text
        booking_data = confirm_res.json()
        assert booking_data["booking_number"].startswith("BK-")
        assert booking_data["status"] == "CONFIRMED"
        assert booking_data["booking_request_id"] == req_id
        assert booking_data["customer_id"] == cust_id
        assert booking_data["pickup_address"] == req_payload["pickup_address"]
        booking_id = booking_data["id"]

        # 4. Request status is updated to CONFIRMED
        req_after = await client.get(
            f"/api/v1/booking-requests/{req_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert req_after.status_code == 200
        assert req_after.json()["status"] == "CONFIRMED"

        # 5. Fetch booking directly
        fetch_booking = await client.get(
            f"/api/v1/bookings/{booking_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert fetch_booking.status_code == 200
        assert fetch_booking.json()["id"] == booking_id


@pytest.mark.asyncio
async def test_duty_allocation_and_compliance_checks():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token, org_id, user_id = await setup_test_workspace(
            client, "dispatch_ops@zolexora.com", f"Trans Logistics {uuid.uuid4().hex[:6]}"
        )
        cust_id = await create_test_customer(client, token)
        driver_id = await create_test_driver(client, token)
        vehicle_id = await create_test_vehicle(client, token)

        now = datetime.datetime.now(datetime.timezone.utc)
        pickup_time = now + datetime.timedelta(hours=2)

        # 1. Create authoritative booking directly
        booking_res = await client.post(
            "/api/v1/bookings",
            json={
                "customer_id": cust_id,
                "booking_type": "CONTRACT",
                "service_type": "CARGO",
                "pickup_address": "Sector 18, Gurugram, Haryana",
                "drop_address": "Indira Gandhi Airport Cargo Terminal, New Delhi",
                "pickup_datetime": pickup_time.isoformat(),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert booking_res.status_code == 201, booking_res.text
        booking_id = booking_res.json()["id"]

        # 2. Create Duty from Booking
        duty_start = pickup_time
        duty_end = pickup_time + datetime.timedelta(hours=5)
        duty_res = await client.post(
            f"/api/v1/bookings/{booking_id}/create-duty",
            json={
                "scheduled_start_time": duty_start.isoformat(),
                "scheduled_end_time": duty_end.isoformat(),
                "notes": "Handle fragile electronic consignments with care",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert duty_res.status_code == 201, duty_res.text
        duty_data = duty_res.json()
        duty_id = duty_data["id"]
        assert duty_data["duty_number"].startswith("DT-")
        assert duty_data["status"] == "ALLOCATED"

        # 3. Assign Driver and Vehicle
        assign_res = await client.post(
            f"/api/v1/duties/{duty_id}/assign",
            json={"driver_id": driver_id, "vehicle_id": vehicle_id},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert assign_res.status_code == 200, assign_res.text
        assigned_duty = assign_res.json()
        assert assigned_duty["driver_id"] == driver_id
        assert assigned_duty["vehicle_id"] == vehicle_id

        # 4. Conflict Check 1: Double-assign driver during overlapping time window
        # Create second booking and duty in same time slot
        booking2_res = await client.post(
            "/api/v1/bookings",
            json={
                "customer_id": cust_id,
                "booking_type": "SPOT",
                "service_type": "CARGO",
                "pickup_address": "Noida Sector 62",
                "drop_address": "Faridabad Industrial Area",
                "pickup_datetime": (pickup_time + datetime.timedelta(hours=1)).isoformat(),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        duty2_res = await client.post(
            f"/api/v1/bookings/{booking2_res.json()['id']}/create-duty",
            json={
                "scheduled_start_time": (duty_start + datetime.timedelta(hours=1)).isoformat(),
                "scheduled_end_time": (duty_end + datetime.timedelta(hours=1)).isoformat(),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        duty2_id = duty2_res.json()["id"]

        other_veh_id = await create_test_vehicle(client, token)
        driver_conflict_res = await client.post(
            f"/api/v1/duties/{duty2_id}/assign",
            json={"driver_id": driver_id, "vehicle_id": other_veh_id},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert driver_conflict_res.status_code == 409
        assert "DRIVER_ALREADY_ASSIGNED" in driver_conflict_res.text

        # 5. Conflict Check 2: Double-assign vehicle during overlapping time window
        other_driver_id = await create_test_driver(client, token)
        veh_conflict_res = await client.post(
            f"/api/v1/duties/{duty2_id}/assign",
            json={"driver_id": other_driver_id, "vehicle_id": vehicle_id},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert veh_conflict_res.status_code == 409
        assert "VEHICLE_ALREADY_ASSIGNED" in veh_conflict_res.text

        # 6. Compliance Check: Assign driver with expired licence
        expired_driver_id = await create_test_driver(client, token, license_expired=True)
        expired_assign_res = await client.post(
            f"/api/v1/duties/{duty2_id}/assign",
            json={"driver_id": expired_driver_id, "vehicle_id": other_veh_id},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert expired_assign_res.status_code == 400
        assert "DRIVER_LICENSE_EXPIRED" in expired_assign_res.text

        # 7. Compliance Check: Assign vehicle undergoing maintenance
        maint_vehicle_id = await create_test_vehicle(client, token, status="MAINTENANCE")
        maint_assign_res = await client.post(
            f"/api/v1/duties/{duty2_id}/assign",
            json={"driver_id": other_driver_id, "vehicle_id": maint_vehicle_id},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert maint_assign_res.status_code == 400
        assert "VEHICLE_NOT_OPERATIONAL" in maint_assign_res.text


@pytest.mark.asyncio
async def test_duty_dispatch_and_execution_lifecycle():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token, org_id, user_id = await setup_test_workspace(
            client, "fleet_commander@zolexora.com", f"Apex Fleet {uuid.uuid4().hex[:6]}"
        )
        cust_id = await create_test_customer(client, token)
        driver_id = await create_test_driver(client, token)
        vehicle_id = await create_test_vehicle(client, token)

        now = datetime.datetime.now(datetime.timezone.utc)
        pickup_time = now + datetime.timedelta(hours=1)

        # 1. Booking & Duty setup
        b_res = await client.post(
            "/api/v1/bookings",
            json={
                "customer_id": cust_id,
                "booking_type": "AIRPORT",
                "service_type": "PASSENGER",
                "pickup_address": "Taj Lands End, Bandra, Mumbai",
                "drop_address": "Chhatrapati Shivaji International Airport T2",
                "pickup_datetime": pickup_time.isoformat(),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        b_id = b_res.json()["id"]

        d_res = await client.post(
            f"/api/v1/bookings/{b_id}/create-duty",
            json={
                "scheduled_start_time": pickup_time.isoformat(),
                "scheduled_end_time": (pickup_time + datetime.timedelta(hours=3)).isoformat(),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        duty_id = d_res.json()["id"]

        # 2. Assign
        await client.post(
            f"/api/v1/duties/{duty_id}/assign",
            json={"driver_id": driver_id, "vehicle_id": vehicle_id},
            headers={"Authorization": f"Bearer {token}"},
        )

        # 3. Dispatch
        dispatch_res = await client.post(
            f"/api/v1/duties/{duty_id}/dispatch",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert dispatch_res.status_code == 200
        assert dispatch_res.json()["status"] == "DISPATCHED"

        # 4. Driver Acceptance
        accept_res = await client.post(
            f"/api/v1/duties/{duty_id}/accept",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert accept_res.status_code == 200

        # 5. Arrived Pickup
        arrived_pk_res = await client.post(
            f"/api/v1/duties/{duty_id}/arrived-pickup",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert arrived_pk_res.status_code == 200
        assert arrived_pk_res.json()["status"] == "ARRIVED_PICKUP"

        # 6. In Transit
        in_transit_res = await client.post(
            f"/api/v1/duties/{duty_id}/in-transit",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert in_transit_res.status_code == 200
        assert in_transit_res.json()["status"] == "IN_TRANSIT"

        # 7. Arrived Drop
        arrived_dp_res = await client.post(
            f"/api/v1/duties/{duty_id}/arrived-drop",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert arrived_dp_res.status_code == 200
        assert arrived_dp_res.json()["status"] == "ARRIVED_DROP"


@pytest.mark.asyncio
async def test_trip_execution_and_odometer_enforcement():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token, org_id, user_id = await setup_test_workspace(
            client, "trip_ops@zolexora.com", f"Transit Rail {uuid.uuid4().hex[:6]}"
        )
        cust_id = await create_test_customer(client, token)
        driver_id = await create_test_driver(client, token)
        vehicle_id = await create_test_vehicle(client, token)

        now = datetime.datetime.now(datetime.timezone.utc)
        pickup_time = now + datetime.timedelta(minutes=30)

        # 1. Setup duty and assign
        b_res = await client.post(
            "/api/v1/bookings",
            json={
                "customer_id": cust_id,
                "booking_type": "LOCAL",
                "service_type": "CARGO",
                "pickup_address": "Whitefield, Bengaluru",
                "drop_address": "Electronic City, Bengaluru",
                "pickup_datetime": pickup_time.isoformat(),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        b_id = b_res.json()["id"]

        d_res = await client.post(
            f"/api/v1/bookings/{b_id}/create-duty",
            json={
                "scheduled_start_time": pickup_time.isoformat(),
                "scheduled_end_time": (pickup_time + datetime.timedelta(hours=4)).isoformat(),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        duty_id = d_res.json()["id"]

        await client.post(
            f"/api/v1/duties/{duty_id}/assign",
            json={"driver_id": driver_id, "vehicle_id": vehicle_id},
            headers={"Authorization": f"Bearer {token}"},
        )

        # 2. Start Trip with initial odometer reading
        start_trip_res = await client.post(
            f"/api/v1/trips/duties/{duty_id}/start",
            json={
                "start_odometer": "62400.00",
                "start_location": {"lat": 12.9698, "lng": 77.7500, "address": "Whitefield Hub"},
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert start_trip_res.status_code == 201, start_trip_res.text
        trip_data = start_trip_res.json()
        trip_id = trip_data["id"]
        assert trip_data["trip_number"].startswith("TR-")
        assert Decimal(str(trip_data["start_odometer"])) == Decimal("62400.00")
        assert trip_data["status"] == "IN_TRANSIT"

        # 3. Add operational toll receipt
        receipt_res = await client.post(
            f"/api/v1/trips/{trip_id}/receipts",
            json={
                "receipt_type": "toll",
                "amount": "145.00",
                "receipt_url": "https://r2.zolexora.com/receipts/toll_001.pdf",
                "notes": "BETL Elevated Expressway Toll",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert receipt_res.status_code == 200
        updated_trip = receipt_res.json()
        assert len(updated_trip["operational_receipts"]) == 1
        assert updated_trip["operational_receipts"][0]["type"] == "toll"

        # 4. Attempt trip completion with INVALID odometer (ending < starting)
        invalid_comp_res = await client.post(
            f"/api/v1/trips/{trip_id}/complete",
            json={
                "end_odometer": "62350.00",  # Less than 62400.00!
                "end_location": {"lat": 12.8452, "lng": 77.6602, "address": "Electronic City Gate 1"},
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert invalid_comp_res.status_code == 400
        assert "ODOMETER_INVALID" in invalid_comp_res.text

        # 5. Complete trip with VALID odometer
        valid_comp_res = await client.post(
            f"/api/v1/trips/{trip_id}/complete",
            json={
                "end_odometer": "62445.50",
                "end_location": {"lat": 12.8452, "lng": 77.6602, "address": "Electronic City Gate 1"},
                "toll_amount": "145.00",
                "fuel_amount": "1200.00",
                "parking_amount": "100.00",
                "waiting_minutes": 25,
                "notes": "Delivered successfully with verified gate pass",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert valid_comp_res.status_code == 200, valid_comp_res.text
        completed_trip = valid_comp_res.json()
        assert completed_trip["status"] == "COMPLETED"
        assert Decimal(str(completed_trip["total_distance_km"])) == Decimal("45.50")
        assert Decimal(str(completed_trip["toll_amount"])) == Decimal("145.00")

        # 6. Verify associated Duty is also marked DUTY_COMPLETED
        duty_check = await client.get(
            f"/api/v1/duties/{duty_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert duty_check.status_code == 200
        assert duty_check.json()["status"] == "DUTY_COMPLETED"


@pytest.mark.asyncio
async def test_operational_tenant_isolation_boundary():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Org 1
        token_1, org_1_id, _ = await setup_test_workspace(
            client, "tenant1_commander@zolexora.com", f"Org1 Transport {uuid.uuid4().hex[:6]}"
        )
        # Org 2
        token_2, org_2_id, _ = await setup_test_workspace(
            client, "tenant2_commander@zolexora.com", f"Org2 Transport {uuid.uuid4().hex[:6]}"
        )

        cust_1 = await create_test_customer(client, token_1)
        driver_1 = await create_test_driver(client, token_1)
        driver_2 = await create_test_driver(client, token_2)
        veh_1 = await create_test_vehicle(client, token_1)
        veh_2 = await create_test_vehicle(client, token_2)

        now = datetime.datetime.now(datetime.timezone.utc)
        pickup_time = now + datetime.timedelta(hours=2)

        # 1. Org 1 creates Booking Request & Booking
        req_res = await client.post(
            "/api/v1/booking-requests",
            json={
                "customer_id": cust_1,
                "pickup_address": "Chennai Port, Tamil Nadu",
                "drop_address": "Sri City SEZ, Andhra Pradesh",
                "pickup_datetime": pickup_time.isoformat(),
            },
            headers={"Authorization": f"Bearer {token_1}"},
        )
        req_1_id = req_res.json()["id"]

        book_res = await client.post(
            "/api/v1/bookings",
            json={
                "customer_id": cust_1,
                "pickup_address": "Chennai Port, Tamil Nadu",
                "drop_address": "Sri City SEZ, Andhra Pradesh",
                "pickup_datetime": pickup_time.isoformat(),
            },
            headers={"Authorization": f"Bearer {token_1}"},
        )
        book_1_id = book_res.json()["id"]

        duty_res = await client.post(
            f"/api/v1/bookings/{book_1_id}/create-duty",
            json={
                "scheduled_start_time": pickup_time.isoformat(),
                "scheduled_end_time": (pickup_time + datetime.timedelta(hours=6)).isoformat(),
            },
            headers={"Authorization": f"Bearer {token_1}"},
        )
        duty_1_id = duty_res.json()["id"]

        # 2. Org 2 attempts to list Org 1's booking requests -> isolated!
        org2_reqs = await client.get(
            "/api/v1/booking-requests",
            headers={"Authorization": f"Bearer {token_2}"},
        )
        assert org2_reqs.status_code == 200
        assert not any(r["id"] == req_1_id for r in org2_reqs.json())

        # 3. Org 2 attempts to fetch Org 1's booking directly -> 404
        org2_fetch_book = await client.get(
            f"/api/v1/bookings/{book_1_id}",
            headers={"Authorization": f"Bearer {token_2}"},
        )
        assert org2_fetch_book.status_code == 404

        # 4. Org 2 attempts to fetch Org 1's duty directly -> 404
        org2_fetch_duty = await client.get(
            f"/api/v1/duties/{duty_1_id}",
            headers={"Authorization": f"Bearer {token_2}"},
        )
        assert org2_fetch_duty.status_code == 404

        # 5. Org 1 attempts to assign Org 2's driver to Org 1's duty -> 404 (driver not in org)
        cross_assign_res = await client.post(
            f"/api/v1/duties/{duty_1_id}/assign",
            json={"driver_id": driver_2, "vehicle_id": veh_1},
            headers={"Authorization": f"Bearer {token_1}"},
        )
        assert cross_assign_res.status_code == 404
        assert "DRIVER_NOT_FOUND" in cross_assign_res.text

        # 6. Org 1 attempts to assign Org 2's vehicle to Org 1's duty -> 404 (vehicle not in org)
        cross_veh_res = await client.post(
            f"/api/v1/duties/{duty_1_id}/assign",
            json={"driver_id": driver_1, "vehicle_id": veh_2},
            headers={"Authorization": f"Bearer {token_1}"},
        )
        assert cross_veh_res.status_code == 404
        assert "VEHICLE_NOT_FOUND" in cross_veh_res.text
