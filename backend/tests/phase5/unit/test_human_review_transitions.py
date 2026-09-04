import pytest
from unittest.mock import patch, MagicMock
from app.decision.services.human_review_service import HumanReviewService
from app.db.models import DecisionArtifactModel

import pytest_asyncio
from unittest.mock import patch, MagicMock, AsyncMock

@pytest_asyncio.fixture
def mock_db():
    with patch("app.decision.services.human_review_service.AsyncSessionLocal") as mock:
        session = AsyncMock()
        mock.return_value = session
        yield session

@pytest.mark.asyncio
async def test_invalid_transition(mock_db):
    artifact = DecisionArtifactModel(
        decision_artifact_id="DA-123",
        dispute_id="DSP-1",
        workflow_status="FINAL_DECISION" # Invalid starting state for review
    )
    # Mocking async scalar_one_or_none
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = artifact
    mock_db.execute.return_value = result_mock
    
    service = HumanReviewService()
    
    with pytest.raises(ValueError, match="Invalid workflow state for review"):
        await service.process_review(
            dispute_id="DSP-1",
            action="APPROVE",
            reviewer_id="user1"
        )

@pytest.mark.asyncio
async def test_ai_recommendation_is_preserved(mock_db):
    artifact = DecisionArtifactModel(
        decision_artifact_id="DA-123",
        dispute_id="DSP-1",
        workflow_status="NEEDS_REVIEW",
        ai_recommendation={"action": "CONTEST"},
        confidence={"confidence": 0.9},
        explanation={"summary": "test"}
    )
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = artifact
    mock_db.execute.return_value = result_mock
    
    service = HumanReviewService()
    await service.process_review(
        dispute_id="DSP-1",
        action="EDIT",
        reviewer_id="user1",
        edited_decision="ACCEPT"
    )
    
    # Assert AI recommendation on artifact was not modified
    assert artifact.ai_recommendation["action"] == "CONTEST"
