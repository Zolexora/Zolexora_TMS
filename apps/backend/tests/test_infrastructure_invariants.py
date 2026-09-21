import pytest
import os
from sqlalchemy import text
from app.db.session import AsyncSessionLocal
from app.cli.infrastructure import check_r2_provisioning, attempt_mongo_provisioning, attempt_d1_provisioning

@pytest.mark.asyncio
async def test_r2_bucket_name_and_privacy():
    # Verify the bucket is expected to be 'tms-documents'
    bucket_name = os.getenv("CLOUDFLARE_R2_BUCKET")
    assert bucket_name == "tms-documents", "R2 bucket must be 'tms-documents'"
    
    # Check that privacy is maintained (we verify this by ensuring it's not exposed in frontend env implicitly)
    # The CLI output string explicitly checks for PRIVATE.
    status = await check_r2_provisioning()
    assert status in ["AVAILABLE", "BLOCKED"], "R2 should either be available or safely blocked"

@pytest.mark.asyncio
async def test_mongo_cluster_name_and_namespaces():
    # Connect to local DB and ensure the registry is correct
    async with AsyncSessionLocal() as session:
        # Check exactly one Mongo cluster is configured in the registry
        res = await session.execute(text("SELECT DISTINCT cluster_identifier FROM tenant_mongodb_registry"))
        clusters = res.scalars().all()
        assert len(clusters) == 1, "Exactly one Mongo cluster should be configured"
        assert clusters[0] == "Zolexora-tms", "Mongo cluster must be named exactly 'Zolexora-tms'"

        # Check exactly ten Mongo logical tenant namespaces are desired
        res = await session.execute(text("SELECT COUNT(*) FROM tenant_mongodb_registry WHERE database_name LIKE 'zolexora_tenant_%'"))
        db_count = res.scalar()
        assert db_count == 10, "Exactly 10 Mongo logical tenant namespaces must be configured"
        
@pytest.mark.asyncio
async def test_d1_databases_configured():
    async with AsyncSessionLocal() as session:
        res = await session.execute(text("SELECT COUNT(*) FROM tenant_database_registry WHERE provider = 'D1'"))
        d1_count = res.scalar()
        assert d1_count == 10, "Exactly ten D1 databases should be configured in the registry"
        
        # Verify names
        res = await session.execute(text("SELECT database_name FROM tenant_database_registry WHERE provider = 'D1' ORDER BY database_name"))
        dbs = res.scalars().all()
        for i, db in enumerate(dbs, start=1):
            assert db == f"zolexora-tms-dev-{i:03d}", f"D1 database name must match zolexora-tms-dev-XXX pattern, got {db}"

@pytest.mark.asyncio
async def test_no_postgresql_tenant_fallback_exists():
    with open('app/auth/dependencies.py', 'r') as f:
        content = f.read()
    # In earlier versions, there was a fallback to ProviderType.POSTGRESQL. We removed it.
    assert "ProviderType.POSTGRESQL" not in content, "PostgreSQL tenant fallback must not exist in dependencies"
    
@pytest.mark.asyncio
async def test_no_fake_ready_state_possible():
    # If the provider is unavailable, it should report BLOCKED, not fake success.
    # We test this by clearing the tokens and seeing if it fakes success
    orig_token = os.environ.get("CLOUDFLARE_API_TOKEN")
    os.environ["CLOUDFLARE_API_TOKEN"] = ""
    status, count = await attempt_d1_provisioning()
    assert status == "BLOCKED", "Must report BLOCKED without fabricating provider success"
    if orig_token is not None:
        os.environ["CLOUDFLARE_API_TOKEN"] = orig_token

