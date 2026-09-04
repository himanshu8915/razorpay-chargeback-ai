import pytest
import time
import asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.session import get_db

@pytest.mark.asyncio
async def test_performance_get_case(db_session):
    from sqlalchemy import text
    # Fetch up to 100 actual dispute IDs
    result = await db_session.execute(text("SELECT dispute_id FROM disputes LIMIT 100"))
    rows = result.fetchall()
    
    if not rows:
        pytest.skip("No disputes found in test database")
        
    dispute_ids = [row[0] for row in rows]
    latencies = []
    
    # Override get_db to use db_session
    async def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        for d_id in dispute_ids:
            start_time = time.perf_counter()
            resp = await client.get(f"/api/v1/disputes/{d_id}")
            end_time = time.perf_counter()
            assert resp.status_code == 200
            latencies.append((end_time - start_time) * 1000) # ms
            
    app.dependency_overrides.clear()
            
    latencies.sort()
    count = len(latencies)
    
    p50 = latencies[int(count * 0.50)]
    p95 = latencies[int(count * 0.95)]
    p99 = latencies[int(count * 0.99)] if count > 99 else latencies[-1]
    
    print(f"Performance Metrics over {count} requests:")
    print(f"P50: {p50:.2f} ms")
    print(f"P95: {p95:.2f} ms")
    print(f"P99: {p99:.2f} ms")
    
    # We just ensure it runs successfully, we don't enforce an artificial SLA.
    assert True
