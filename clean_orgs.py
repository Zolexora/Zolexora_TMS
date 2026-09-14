import asyncio
from sqlalchemy import text
from app.db.session import AsyncSessionLocal

async def clean():
    async with AsyncSessionLocal() as session:
        await session.execute(text('DELETE FROM organisation_members'))
        await session.execute(text('DELETE FROM organisations'))
        await session.commit()
    print('Cleaned')

asyncio.run(clean())
