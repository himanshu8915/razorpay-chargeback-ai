from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict

class StructuredValue(BaseModel):
    field_type: str = Field(description="E.g., 'date', 'amount', 'status', 'identifier'")
    value: Any = Field(description="The parsed value (e.g., '2026-08-20', 150.00, 'delivered')")

class FactualArgument(BaseModel):
    statement: str = Field(description="The natural language claim.")
    evidence_ids: List[str] = Field(description="Evidence IDs supporting this claim.")
    structured_values: Dict[str, StructuredValue] = Field(
        default_factory=dict, 
        description="Extracted key values mapped for deterministic validation."
    )

class PolicyArgument(BaseModel):
    statement: str = Field(description="The policy-aligned argument.")
    policy_source_ids: List[str] = Field(description="Policy IDs supporting this argument.")

class RepresentationDraft(BaseModel):
    summary: str = Field(description="High-level summary of the merchant's position.")
    claim_response: str = Field(description="Direct response to the dispute claim.")
    factual_arguments: List[FactualArgument] = Field(default_factory=list)
    policy_arguments: List[PolicyArgument] = Field(default_factory=list)
    conclusion: str = Field(description="Final conclusion statement.")
    evidence_references: List[str] = Field(default_factory=list, description="All evidence IDs cited.")

class FinalRepresentation(BaseModel):
    original_ai_draft: RepresentationDraft
    human_edited_draft: Optional[RepresentationDraft] = None
    final_text_payload: str = Field(description="The flattened string representation to be submitted to the bank/processor.")
    is_human_edited: bool = Field(default=False)
