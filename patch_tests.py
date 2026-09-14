import re

with open('apps/tms-api/tests/test_tenant_isolation.py', 'r') as f:
    content = f.read()

cleanup_code = """
        # Cleanup
        from app.db.session import AsyncSessionLocal
        from sqlalchemy import text
        async with AsyncSessionLocal() as session:
            await session.execute(text(f"DELETE FROM organisations WHERE id = '{org_a_id}'"))
            await session.execute(text(f"DELETE FROM organisations WHERE id = '{org_b_id}'"))
            await session.commit()
"""

# Insert before the second test definition
content = content.replace("from httpx import ASGITransport", cleanup_code + "\nfrom httpx import ASGITransport", 1)

with open('apps/tms-api/tests/test_tenant_isolation.py', 'w') as f:
    f.write(content)
print("patched")
