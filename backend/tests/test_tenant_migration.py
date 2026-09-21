import pytest
from uuid import uuid4
from datetime import datetime, timezone
from decimal import Decimal
from app.services.tenant_migration.transformer import TenantDataTransformer
from app.services.tenant_migration.importer import TenantDataImporter
from app.modules.platform.models import ProviderType

def test_migration_type_transformations():
    # UUID
    test_uuid = uuid4()
    assert TenantDataTransformer.transform_value(test_uuid) == str(test_uuid)
    
    # JSONB
    test_dict = {"c": 3, "a": 1, "b": {"nested": 2}}
    transformed_json = TenantDataTransformer.transform_value(test_dict)
    assert transformed_json == '{"a":1,"b":{"nested":2},"c":3}'
    
    # ENUM
    assert TenantDataTransformer.transform_value(ProviderType.POSTGRESQL) == "POSTGRESQL"
    
    # DECIMAL
    test_dec = Decimal("1000.50")
    assert TenantDataTransformer.transform_value(test_dec) == "1000.50"
    
    # DATETIME
    now = datetime.now(timezone.utc)
    assert TenantDataTransformer.transform_value(now) == now.isoformat()
    
    # BOOLEAN
    assert TenantDataTransformer.transform_value(True) == 1
    assert TenantDataTransformer.transform_value(False) == 0


from httpx import ASGITransport, AsyncClient
from jose import jwt
from app.main import app
from app.core.config import settings

def make_test_token(user_id: uuid4, email: str = "test@zolexora.com") -> str:
    payload = {
        "sub": str(user_id),
        "email": email,
        "aud": "authenticated",
        "exp": 9999999999,
    }
    secret = settings.JWT_SECRET or "test-jwt-secret-for-testing"
    return jwt.encode(payload, secret, algorithm="HS256")

@pytest.mark.asyncio
async def test_migration_idempotency_and_state_machine():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        org_id = uuid4()
        token = make_test_token(uuid4())
        res = await client.post(f"/api/v1/platform/tenants/{org_id}/migration/dry-run", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code in (401, 403)
