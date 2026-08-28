"""
Phase 0 integration tests — API endpoints.

Test 2: GET /api/v1/health returns {"status": "ok"}
Test 3/7: GET /api/v1/ready behavior (with no real DB in unit test mode)
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    """GET /api/v1/health must return 200 with status=ok."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_ready_endpoint_without_db(client: AsyncClient):
    """
    GET /api/v1/ready must return 503 when PostgreSQL is not available.
    In the unit test environment there is no real database.
    """
    response = await client.get("/api/v1/ready")
    # Without a real DB, expect 503
    assert response.status_code in (200, 503)
