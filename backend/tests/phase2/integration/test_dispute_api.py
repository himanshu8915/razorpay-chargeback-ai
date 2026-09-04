import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.session import get_db

@pytest.mark.asyncio
async def test_get_dispute_integration(db_session):
    # This test will run against the test DB (which should have some data populated from Phase 1)
    # We fetch an actual dispute ID from the DB to test with
    from sqlalchemy import text
    result = await db_session.execute(text("SELECT dispute_id FROM disputes LIMIT 1"))
    row = result.fetchone()
    
    if not row:
        pytest.skip("No disputes found in test database")
        
    dispute_id = row[0]
    
    # Override get_db to use db_session
    async def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(f"/api/v1/disputes/{dispute_id}")
        
    app.dependency_overrides.clear()
        
    assert response.status_code == 200
    data = response.json()
    assert "case" in data
    assert data["case"]["dispute"]["dispute_id"] == dispute_id
    assert data["case"]["transaction"] is not None
    assert data["case"]["order"] is not None
    assert data["case"]["customer"] is not None
    # Note: merchant might be None for some orders due to Kaggle dataset nullability.
    # But we assert that the keys exist.
    assert "customer" in data["case"]
    assert "merchant" in data["case"]
    assert "deadline" in data["case"]
