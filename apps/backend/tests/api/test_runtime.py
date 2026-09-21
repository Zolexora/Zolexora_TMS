import pytest
from httpx import AsyncClient, ASGITransport
import uuid
from app.main import app
from app.db.session import AsyncSessionLocal
from sqlalchemy import text
from jose import jwt
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
async def test_runtime_isolation():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create Org A
        user_a = uuid.uuid4()
        token_a = make_test_token(user_a, "user_a@test.com")
        res_a = await client.post("/api/v1/onboarding", json={"name": "Org A", "organisation_type": "Private Limited Company"}, headers={"Authorization": f"Bearer {token_a}"})
        assert res_a.status_code == 201
        
        # Create Org B
        user_b = uuid.uuid4()
        token_b = make_test_token(user_b, "user_b@test.com")
        res_b = await client.post("/api/v1/onboarding", json={"name": "Org B", "organisation_type": "Private Limited Company"}, headers={"Authorization": f"Bearer {token_b}"})
        assert res_b.status_code == 201

        # Fetch runtime for A
        run_a = await client.get("/api/v1/application/runtime", headers={"Authorization": f"Bearer {token_a}"})
        assert run_a.status_code == 200
        data_a = run_a.json()
        assert data_a["application"]["name"] == "Org A TMS"
        assert data_a["application"]["type"] == "STANDARD"
        assert data_a["modules"]["bookings"]["enabled"] is True # Safe default

        # Fetch runtime for B
        run_b = await client.get("/api/v1/application/runtime", headers={"Authorization": f"Bearer {token_b}"})
        assert run_b.status_code == 200
        data_b = run_b.json()
        assert data_b["application"]["name"] == "Org B TMS"
        
        # Verify isolation: Token A gets A, Token B gets B
        assert data_a["application"]["id"] != data_b["application"]["id"]
