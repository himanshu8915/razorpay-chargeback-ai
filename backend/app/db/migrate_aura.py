import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from app.config.settings import settings
from app.db.models import Base

async def run_migration():
    print("Connecting to database...")
    engine = create_async_engine(settings.database_url)
    async with engine.begin() as conn:
        print("Creating new tables (this won't drop existing ones)...")
        await conn.run_sync(Base.metadata.create_all)
    print("Migration complete. Chat memory tables are ready!")
    
if __name__ == "__main__":
    asyncio.run(run_migration())
