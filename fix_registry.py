import asyncio
from app.db.session import AsyncSessionLocal
from sqlalchemy import text
from app.modules.platform.models import RegistryStatus

async def fix():
    async with AsyncSessionLocal() as session:
        # Reset everything to AVAILABLE for testing
        await session.execute(text("UPDATE tenant_database_registry SET status = 'AVAILABLE', assigned_organisation_id = NULL"))
        await session.execute(text("UPDATE tenant_mongodb_registry SET status = 'AVAILABLE'"))
        await session.execute(text("DELETE FROM organisation_members"))
        await session.execute(text("DELETE FROM organisation_database_assignments"))
        await session.execute(text("DELETE FROM organisation_mongodb_assignments"))
        await session.execute(text("DELETE FROM organisations"))
        await session.commit()
        print("Reset tenant databases and mongodb to AVAILABLE.")

if __name__ == "__main__":
    asyncio.run(fix())
