import asyncio
from sqlalchemy import text
from app.db.session import AsyncSessionLocal

async def destroy():
    async with AsyncSessionLocal() as session:
        # Delete 350 orgs (this cascades to members, assignments, etc.)
        await session.execute(text("DELETE FROM organisations"))
        await session.commit()
        print("Organisations deleted.")

if __name__ == "__main__":
    asyncio.run(destroy())
