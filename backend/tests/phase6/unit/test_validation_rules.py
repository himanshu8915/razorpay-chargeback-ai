import pytest
from app.representment.rules.validation_rules import validate_unsupported_claims, validate_format
from app.representment.models.representation import RepresentationDraft, FactualArgument, PolicyArgument, StructuredValue

def test_unsupported_claims_detection():
    draft = RepresentationDraft(
        summary="Summary",
        claim_response="Response",
        conclusion="Conclusion",
        factual_arguments=[
            FactualArgument(statement="Claim with evidence", evidence_ids=["E1"]),
            FactualArgument(statement="Claim without evidence", evidence_ids=[])
        ],
        policy_arguments=[]
    )
    
    is_valid, errors = validate_unsupported_claims(draft)
    assert not is_valid
    assert len(errors) == 1
    assert "lacks evidence references" in errors[0]

def test_format_validation():
    draft = RepresentationDraft(
        summary="Short",
        claim_response="Short",
        conclusion="Short",
        factual_arguments=[],
        policy_arguments=[]
    )
    is_valid, errors = validate_format(draft)
    assert not is_valid
    assert any("Summary is missing or too short" in e for e in errors)
    assert any("Claim response is missing or too short" in e for e in errors)
    assert any("Conclusion is missing or too short" in e for e in errors)
    
def test_valid_format():
    draft = RepresentationDraft(
        summary="This is a reasonably long summary.",
        claim_response="This is a reasonably long claim response.",
        conclusion="This is a reasonably long conclusion.",
        factual_arguments=[],
        policy_arguments=[]
    )
    is_valid, errors = validate_format(draft)
    assert is_valid
    assert len(errors) == 0
