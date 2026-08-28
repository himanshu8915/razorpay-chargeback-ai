"""
Health and readiness endpoints.

GET /health  — liveness probe: is the process running?
GET /ready   — readiness probe: are required dependencies available?
"""

from fastapi import APIRouter
from sqlalchemy import text

from app.db.session import AsyncSessionLocal
from app.logging import get_logger

router = APIRouter(tags=["health"])
logger = get_logger("api.health")


@router.get("/health")
async def health() -> dict:
    """Liveness probe. Returns ok if the process is running."""
    return {"status": "ok"}


@router.get("/ready")
async def ready() -> dict:
    """
    Readiness probe.
    Checks that PostgreSQL is reachable before reporting ready.
    Phase 1 will extend this with dataset initialization state.
    """
    db_ok = False
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        db_ok = True
    except Exception as exc:
        logger.warning("Database not ready: %s", exc)

    if not db_ok:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "database": "unavailable",
            },
        )

    return {
        "status": "ready",
        "database": "ok",
    }
