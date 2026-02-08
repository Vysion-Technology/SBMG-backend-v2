
import asyncio
from sqlalchemy import text
from database import get_db

async def fix():
    async for session in get_db():
        await session.execute(text("UPDATE alembic_version SET version_num = '890c658e3b42'"))
        await session.commit()
        print("Updated alembic_version to 890c658e3b42")
        return

if __name__ == "__main__":
    asyncio.run(fix())
