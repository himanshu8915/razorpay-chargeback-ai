import pytest
from app.evidence.reasoning.confidence import calculate_confidence
from app.agents.evidence_reasoning.schemas import AgentEvidenceAssessment
from app.evidence.models.evidence_finding import EvidenceFinding
from app.evidence.models.evidence_conflict import EvidenceConflict

def get_base_assessment(conf: float = 0.95):
    return AgentEvidenceAssessment(
        evidence_findings=[
            EvidenceFinding(
                evidence_id="1", relationship="supports", claim_aspect="del",
                finding="ok", policy_basis=["POL1"], confidence=conf
            )
        ],
        overall_assessment="ok"
    )

def test_1_valid_assessment_no_failure():
    assessment = get_base_assessment(0.95)
    conf = calculate_confidence(assessment, "complete", [], has_grounding_failure=False)
    assert conf == 0.95

def test_2_valid_assessment_with_failure():
    assessment = get_base_assessment(0.95)
    conf_no_failure = calculate_confidence(assessment, "complete", [], has_grounding_failure=False)
    conf_with_failure = calculate_confidence(assessment, "complete", [], has_grounding_failure=True)
    assert conf_with_failure < conf_no_failure
    assert conf_with_failure == pytest.approx(0.65) # 0.95 - 0.30

def test_3_failure_with_high_raw_confidence():
    assessment = get_base_assessment(0.95)
    conf = calculate_confidence(assessment, "complete", [], has_grounding_failure=True)
    assert conf < 0.95

def test_4_failure_with_low_raw_confidence():
    assessment = get_base_assessment(0.10)
    conf = calculate_confidence(assessment, "complete", [], has_grounding_failure=True)
    assert conf == 0.0 # Bounded to 0

def test_5_multiple_validation_errors():
    assessment = get_base_assessment(0.95)
    # The flag has_grounding_failure represents multiple errors mapping to one boolean flag
    # so the penalty is applied exactly once (-0.30)
    conf = calculate_confidence(assessment, "complete", [], has_grounding_failure=True)
    assert conf == pytest.approx(0.65)

def test_6_no_validation_errors():
    assessment = get_base_assessment(0.95)
    conf = calculate_confidence(assessment, "complete", [], has_grounding_failure=False)
    assert conf == 0.95

def test_calculate_confidence_penalties():
    assessment = AgentEvidenceAssessment(
        evidence_findings=[
            EvidenceFinding(
                evidence_id="1", relationship="supports", claim_aspect="del",
                finding="ok", policy_basis=[], confidence=0.8 # missing policy basis penalizes by 0.05
            )
        ],
        overall_assessment="ok"
    )
    conflict = EvidenceConflict(
        evidence_ids=["1"], topic="t", description="d", severity="high"
    )
    
    conf = calculate_confidence(assessment, "partial", [conflict], has_grounding_failure=True)
    # base 0.8
    # partial -0.15 = 0.65
    # high conflict -0.2 = 0.45
    # unsupported finding -0.05 = 0.40
    # grounding failure -0.30 = 0.10
    assert conf == pytest.approx(0.10)

def test_confidence_upper_bound():
    assessment = get_base_assessment(1.0)
    conf = calculate_confidence(assessment, "complete", [], has_grounding_failure=False)
    assert conf == 1.0
