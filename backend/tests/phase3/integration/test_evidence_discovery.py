import pytest
import asyncio
from app.db.session import AsyncSessionLocal
from app.evidence.services.evidence_discovery_service import EvidenceDiscoveryService
from app.db.models import Dispute
from sqlalchemy import select

@pytest.mark.asyncio
async def test_evidence_discovery_end_to_end(db_session):
    # Attempt to fetch a real dispute from DB
    result = await db_session.execute(select(Dispute.dispute_id).limit(1))
    dispute_id = result.scalar_one_or_none()
        
    if not dispute_id:
        pytest.skip("No disputes found in database to test Phase 3.")
        
    service = EvidenceDiscoveryService(db_session)
    
    # This will trigger LLMs, RAG, and everything.
    # Note: If sentence-transformers failed to install due to WinError 206, this will raise ImportError.
    try:
        bundle, _ = await service.discover_evidence(dispute_id)
        
        assert bundle is not None
        assert bundle.dispute_id == dispute_id
        
        # Print to stdout so we can visually inspect the JSON dump if needed
        print(bundle.model_dump_json(indent=2))
    except ImportError as e:
        pytest.skip(f"Skipping due to missing dependencies: {e}")
