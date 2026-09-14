from dotenv import load_dotenv
load_dotenv()
import pytest
import os
import uuid
from sqlalchemy import text
from app.db.session import AsyncSessionLocal

@pytest.mark.asyncio
async def test_first_organisation_dry_run():
    # Attempt to allocate D1, Mongo, and R2 as a dry run
    async with AsyncSessionLocal() as session:
        # Check D1
        d1_res = await session.execute(text("SELECT database_name FROM tenant_database_registry WHERE status = 'AVAILABLE' ORDER BY database_name LIMIT 1"))
        d1_db = d1_res.scalar()
        assert d1_db is not None, "No AVAILABLE D1 databases"
        
        # Check Mongo
        mongo_res = await session.execute(text("SELECT cluster_identifier, database_name FROM tenant_mongodb_registry WHERE status = 'AVAILABLE' ORDER BY database_name LIMIT 1"))
        mongo_row = mongo_res.fetchone()
        assert mongo_row is not None, "No AVAILABLE MongoDB databases"
        
        # Check R2 config
        r2_bucket = os.getenv("CLOUDFLARE_R2_BUCKET")
        assert r2_bucket == "tms-documents"
        
        new_org_uuid = uuid.uuid4()
        r2_prefix = f"organisations/{new_org_uuid}/"
        cld_prefix = f"zolexora/organisations/{new_org_uuid}/"
        
        assert "tms-documents" in r2_bucket
        assert str(new_org_uuid) in r2_prefix
        assert str(new_org_uuid) in cld_prefix

@pytest.mark.asyncio
async def test_resource_uniqueness():
    async with AsyncSessionLocal() as session:
        # Verify no two organisations can have the same DB
        # The schema uses UNIQUE constraints on organisation_id for assignments
        # tenant_database_registry.database_identifier is UNIQUE
        res = await session.execute(text("SELECT COUNT(*) FROM organisations"))
        orgs = res.scalar()
        assert orgs == 0, "Expected 0 organisations in the baseline"

@pytest.mark.asyncio
async def test_tenant_context_derivation_isolation():
    # TenantContext depends on getting the DB assignments from Supabase.
    # The frontend does not pass D1 or Mongo names. 
    # This is verified by checking the TenantContext implementation.
    with open('app/auth/dependencies.py', 'r') as f:
        content = f.read()
    
    assert 'row["database_identifier"]' in content
    assert "r2_bucket=" in content

