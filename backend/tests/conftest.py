"""
Shared pytest fixtures for all test levels.
"""

import pytest
import sys
import asyncio
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import os
os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@localhost:5432/chargeback"

from httpx import ASGITransport, AsyncClient

from app.config.settings import settings
settings.database_url = settings.database_url.replace("postgres:5432", "localhost:5432")
TEST_DATABASE_URL = settings.database_url

from app.main import app

import pytest_asyncio
@pytest_asyncio.fixture(scope="function", loop_scope="function")
async def client() -> AsyncClient:
    """Async HTTP client targeting the FastAPI app directly (no server needed)."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker




from sqlalchemy.pool import NullPool

@pytest_asyncio.fixture(scope="function", loop_scope="function", autouse=True)
async def db_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)
    
    # OVERRIDE the global app engine to use the test engine.
    # This ensures that FastAPI and background tasks use the SAME event loop 
    # as the tests, and the engine is properly disposed at session end.
    import app.db.session
    app.db.session.engine = engine
    app.db.session.AsyncSessionLocal.configure(bind=engine)
    
    # Override any standalone usages
    import app.evidence.services.evidence_verification_service
    app.evidence.services.evidence_verification_service.AsyncSessionLocal.configure(bind=engine)
    import app.decision.services.decision_service
    app.decision.services.decision_service.AsyncSessionLocal.configure(bind=engine)
    
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture(scope="function", loop_scope="function")
async def db_session(db_engine):
    async_session = sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
