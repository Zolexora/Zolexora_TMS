import pytest
from httpx import AsyncClient, ASGITransport
import uuid
from app.main import app
from jose import jwt
from app.core.config import settings

def make_test_token(user_id: uuid.UUID, email: str) -> str:
    payload = {
        "sub": str(user_id),
        "email": email,
        "aud": "authenticated",
        "exp": 9999999999,
    }
    return jwt.encode(payload, settings.JWT_SECRET or "test-jwt-secret-for-testing", algorithm="HS256")

@pytest.mark.asyncio
async def test_commander_transfer_flow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create Org with User A
        user_a = uuid.uuid4()
        token_a = make_test_token(user_a, "user_a@test.com")
        res_a = await client.post("/api/v1/onboarding", json={"name": "Org A", "organisation_type": "Private Limited Company"}, headers={"Authorization": f"Bearer {token_a}"})
        assert res_a.status_code == 201
        org_id = res_a.json()["organisation"]["id"]

        # Fetch me to verify Commander
        me_a = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_a}"})
        assert me_a.status_code == 200
        assert me_a.json()["is_commander"] is True
        
        # User A invites User B (or we bypass and just create membership, let's use the DB)
        user_b = uuid.uuid4()
        from app.db.session import AsyncSessionLocal
        from sqlalchemy import text
        async with AsyncSessionLocal() as session:
            await session.execute(text("INSERT INTO organisation_members (id, organisation_id, user_id, status, is_creator, is_commander, created_at, updated_at) VALUES (:id, :oid, :uid, 'ACTIVE', false, false, now(), now())"), {"id": uuid.uuid4(), "oid": org_id, "uid": user_b})
            await session.commit()
            
        token_b = make_test_token(user_b, "user_b@test.com")
        
        # Check B is not commander
        me_b = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_b}", "X-Organization-Id": str(org_id)})
        assert me_b.status_code == 200
        assert me_b.json()["is_commander"] is False
        
        # B tries to transfer (fails)
        fail_res = await client.post("/api/v1/organisations/commander/transfer", json={"new_commander_user_id": str(user_a), "former_commander_role": "ADMIN"}, headers={"Authorization": f"Bearer {token_b}", "X-Organization-Id": str(org_id)})
        assert fail_res.status_code == 403
        
        # A transfers to B
        transfer_res = await client.post("/api/v1/organisations/commander/transfer", json={"new_commander_user_id": str(user_b), "former_commander_role": "ADMIN"}, headers={"Authorization": f"Bearer {token_a}", "X-Organization-Id": str(org_id)})
        assert transfer_res.status_code == 200
        
        # Check A is not commander
        me_a_after = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_a}", "X-Organization-Id": str(org_id)})
        assert me_a_after.json()["is_commander"] is False
        
        # Check B is commander
        me_b_after = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_b}", "X-Organization-Id": str(org_id)})
        assert me_b_after.json()["is_commander"] is True
