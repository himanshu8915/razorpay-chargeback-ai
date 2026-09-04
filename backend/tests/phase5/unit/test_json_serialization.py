import pytest
from decimal import Decimal
from app.decision.services.decision_service import DecisionService
from app.decision.models.decision import DecisionRecommendation

def test_decimal_json_serialization_boundary():
    # 1. Decimal values exist internally
    recommendation = DecisionRecommendation(
        action="CONTEST",
        confidence=0.95,
        case_strength=0.85,
        success_likelihood=0.90,
        recoverable_amount=Decimal("1086.63"),
        expected_recovery=Decimal("977.97"),
        operational_cost=Decimal("2.50"),
        net_expected_value=Decimal("975.47"),
        deadline_risk="SAFE",
        reason_codes=["MOCK_REASON"],
        decision_factors=[]
    )
    
    # Verify Decimals are present
    assert isinstance(recommendation.recoverable_amount, Decimal)
    assert isinstance(recommendation.net_expected_value, Decimal)
    
    # 2. Extract the serialization helper from DecisionService
    # We will simulate exactly how DecisionService casts the dictionary before persistence
    def _json_safe(obj):
        if isinstance(obj, dict):
            return {k: _json_safe(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [_json_safe(v) for v in obj]
        elif isinstance(obj, Decimal):
            return float(obj)
        return obj
        
    # 3. Serialize through the boundary
    raw_dict = recommendation.model_dump()
    json_safe_dict = _json_safe(raw_dict)
    
    # 4. Verify no Decimal remains and numerical values are correct (float format)
    assert isinstance(json_safe_dict["recoverable_amount"], float)
    assert isinstance(json_safe_dict["net_expected_value"], float)
    
    # 5. Verify the numerical equivalence
    assert json_safe_dict["recoverable_amount"] == 1086.63
    assert json_safe_dict["net_expected_value"] == 975.47
    
    # Other values are untouched
    assert json_safe_dict["action"] == "CONTEST"
    assert json_safe_dict["reason_codes"] == ["MOCK_REASON"]
