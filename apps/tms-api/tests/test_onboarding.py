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


@pytest.mark.asyncio
async def test_complete_onboarding_assigns_commander():
    user_id = uuid.uuid4()
    token = make_test_token(user_id, email="commander1@zolexora.com")
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Step 1: Execute onboarding
        payload = {
            "name": f"Apex Logistics {uuid.uuid4().hex[:6]}",
            "organisation_type": "Private Limited Company",
        }
        res = await client.post(
            "/api/v1/onboarding",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 201, res.text
        data = res.json()
        assert data["role_code"] == "COMMANDER"
        assert data["organisation"]["name"] == payload["name"]
        assert data["organisation"]["organisation_type"] == payload["organisation_type"]
        assert data["organisation"]["status"] == "ACTIVE"
        org_id = data["organisation"]["id"]

        # Step 2: Verify /auth/me returns Commander role
        me_res = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_res.status_code == 200
        me_data = me_res.json()
        assert me_data["role_code"] == "COMMANDER"
        assert me_data["organisation_id"] == org_id
        assert len(me_data["permissions"]) > 0
        assert "organisation.manage" in me_data["permissions"]

        # Step 3: Verify subsequent onboarding by same user returns existing workspace
        dup_res = await client.post(
            "/api/v1/onboarding",
            json={"name": "Duplicate Org", "organisation_type": "Partnership Firm"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert dup_res.status_code == 201
        dup_data = dup_res.json()
        assert dup_data["organisation"]["id"] == org_id


@pytest.mark.asyncio
async def test_cannot_invite_member_as_commander():
    user_id = uuid.uuid4()
    token = make_test_token(user_id, email="commander2@zolexora.com")
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Onboard organisation
        onb_res = await client.post(
            "/api/v1/onboarding",
            json={"name": f"Security Org {uuid.uuid4().hex[:6]}", "organisation_type": "Limited Liability Partnership (LLP)"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert onb_res.status_code == 201

        # Attempt to invite another user as COMMANDER (should fail validation)
        invite_res = await client.post(
            "/api/v1/organisations/members/invite",
            json={"email": "intruder@zolexora.com", "role_code": "COMMANDER"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert invite_res.status_code == 422  # Unprocessable Entity (validation rejected)

        # Invite with valid non-commander role (e.g. DISPATCHER)
        valid_invite = await client.post(
            "/api/v1/organisations/members/invite",
            json={"email": "dispatcher@zolexora.com", "role_code": "DISPATCHER"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert valid_invite.status_code == 201
        inv_data = valid_invite.json()
        assert inv_data["role_code"] == "DISPATCHER"
        assert inv_data["status"] == "INVITED"
