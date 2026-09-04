import pytest
from unittest.mock import AsyncMock, MagicMock
from app.data_access.repositories.dispute_repository import DisputeRepository
from app.db.models import Dispute

@pytest.mark.asyncio
async def test_dispute_repository_get_by_id():
    mock_session = AsyncMock()
    mock_result = MagicMock()
    
    mock_dispute = Dispute(dispute_id="DSP1")
    mock_result.scalars().first.return_value = mock_dispute
    mock_session.execute.return_value = mock_result
    
    repo = DisputeRepository(mock_session)
    result = await repo.get_by_id("DSP1")
    
    assert result is not None
    assert result.dispute_id == "DSP1"

@pytest.mark.asyncio
async def test_dispute_repository_not_found():
    mock_session = AsyncMock()
    mock_result = MagicMock()
    
    mock_result.scalars().first.return_value = None
    mock_session.execute.return_value = mock_result
    
    repo = DisputeRepository(mock_session)
    result = await repo.get_by_id("FAKE_DSP")
    
    assert result is None
