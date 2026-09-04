import pytest
from sqlalchemy import text
from app.db.base import Base

@pytest.mark.asyncio
async def test_structured_data_counts(db_session):
    """Verify that the structured data was ingested correctly with exact row counts."""
    
    # These counts map exactly to the Kaggle dataset
    expected_counts = {
        "customers": 10000,
        "merchants": 3095,
        "orders": 99441,
        "transactions": 103886,
        "deliveries": 99441,
        "disputes": 10000
    }
    
    for table, expected in expected_counts.items():
        result = await db_session.execute(text(f"SELECT COUNT(*) FROM {table}"))
        count = result.scalar()
        assert count == expected, f"Table {table} count mismatch. Expected {expected}, got {count}"

@pytest.mark.asyncio
async def test_policy_data_exists(db_session):
    """Verify that the 8 policy PDFs were chunked and embedded."""
    
    # 1. Check policies
    result = await db_session.execute(text("SELECT count(DISTINCT source_file) FROM policy_documents"))
    policy_count = result.scalar()
    assert policy_count == 9, f"Expected 9 policies, got {policy_count}"
    
    # 2. Check chunks exist
    result = await db_session.execute(text("SELECT COUNT(*) FROM policy_parent_chunks"))
    parent_count = result.scalar()
    assert parent_count > 0, "No parent chunks generated."
    
    result = await db_session.execute(text("SELECT COUNT(*) FROM policy_child_chunks"))
    child_count = result.scalar()
    assert child_count > 0, "No child chunks generated."
    assert child_count > parent_count, "Expected more child chunks than parent chunks."

@pytest.mark.asyncio
async def test_vector_extension_active(db_session):
    """Verify that pgvector is active and vectors are 384 dimensions."""
    
    # Query a single vector to check its dimensionality
    result = await db_session.execute(text("SELECT embedding FROM policy_child_chunks LIMIT 1"))
    row = result.fetchone()
    if row:
        embedding = row[0]
        if isinstance(embedding, str):
            import json
            embedding = json.loads(embedding)
        # BAAI/bge-small-en-v1.5 produces 384d vectors
        assert len(embedding) == 384, f"Expected vector dimension 384, got {len(embedding)}"

@pytest.mark.asyncio
async def test_system_ready_state(db_session):
    """Verify idempotency state is marked as READY."""
    result = await db_session.execute(text("SELECT value FROM system_metadata WHERE key = 'status'"))
    state = result.scalar()
    assert state == 'READY', f"System is not marked READY, got {state}"
