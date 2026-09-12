import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from jose import jwt
from app.main import app
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
async def test_cross_tenant_isolation_boundary():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create Organisation A with User A
        user_a = uuid.uuid4()
        token_a = make_test_token(user_a, "user_a@tenant-a.com")
        res_a = await client.post(
            "/api/v1/onboarding",
            json={"name": f"Tenant Alpha {uuid.uuid4().hex[:6]}", "organisation_type": "Private Limited Company"},
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert res_a.status_code == 201
        org_a_id = res_a.json()["organisation"]["id"]

        # Create Organisation B with User B
        user_b = uuid.uuid4()
        token_b = make_test_token(user_b, "user_b@tenant-b.com")
        res_b = await client.post(
            "/api/v1/onboarding",
            json={"name": f"Tenant Beta {uuid.uuid4().hex[:6]}", "organisation_type": "Sole Proprietorship / Proprietor"},
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert res_b.status_code == 201
        org_b_id = res_b.json()["organisation"]["id"]

        assert org_a_id != org_b_id

        # 1. User A can access Organisation A
        my_org_a = await client.get(
            "/api/v1/organisations/me",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert my_org_a.status_code == 200
        assert my_org_a.json()["id"] == org_a_id

        # 2. User B can access Organisation B
        my_org_b = await client.get(
            "/api/v1/organisations/me",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert my_org_b.status_code == 200
        assert my_org_b.json()["id"] == org_b_id

        # 3. User A queries members of Organisation A (authorized)
        members_a = await client.get(
            "/api/v1/organisations/members",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert members_a.status_code == 200
        for m in members_a.json():
            assert m["organisation_id"] == org_a_id

        # 4. User B queries members of Organisation B (authorized)
        members_b = await client.get(
            "/api/v1/organisations/members",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert members_b.status_code == 200
        for m in members_b.json():
            assert m["organisation_id"] == org_b_id

async def test_tenant_context_resolution(client: AsyncClient, token_commander: str):
    # This just ensures that hitting an endpoint resolves the tenant correctly without crashing.
    response = await client.get("/api/v1/health", headers={"Authorization": f"Bearer {token_commander}"})
    assert response.status_code == 200

async def test_platform_admin_apis_forbidden_for_commander(client: AsyncClient, token_commander: str):
    # Tenant commander should NOT have PLATFORM_ADMIN permission
    response = await client.post("/api/v1/platform/tenants/databases", json={
        "provider": "D1",
        "database_identifier": "test_d1",
        "database_name": "test_d1_name"
    }, headers={"Authorization": f"Bearer {token_commander}"})
    assert response.status_code == 403
    assert "Platform Administrators" in response.json()["detail"]
