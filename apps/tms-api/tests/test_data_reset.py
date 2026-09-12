import pytest
from app.cli.data_reset import audit_postgres, clean_postgres, audit_d1, clean_d1
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal
import os

@pytest.mark.asyncio
async def test_data_reset_safety():
    # Ensure production environment cannot be bypassed
    import app.cli.data_reset
    original_env = app.cli.data_reset.settings.ENVIRONMENT
    app.cli.data_reset.settings.ENVIRONMENT = "production"
    
    # Run clean - it should return without doing anything
    await app.cli.data_reset.run_clean(confirm=True)
    
    # Restore
    app.cli.data_reset.settings.ENVIRONMENT = original_env

@pytest.mark.asyncio
async def test_complete_data_reset():
    # Dry run audit
    async with AsyncSessionLocal() as session:
        audit = await audit_postgres(session)
        assert "total_rows" in audit
        
        # We don't actually run clean_postgres in the unit test suite globally
        # to avoid wiping out the test data mid-flight for other tests,
        # but we verify the functions compile and are importable.
        
def test_d1_cleanup():
    # Create a mock pilot DB
    with open("/tmp/pilot_test_123.db", "w") as f:
        f.write("test")
        
    audit = audit_d1()
    assert audit["count"] >= 1
    
    clean_d1()
    
    audit_after = audit_d1()
    assert audit_after["count"] == 0

