from typing import List, Dict, Any
from app.evidence.models.evidence_item import EvidenceItem
from app.evidence.models.evidence_bundle import EvidenceBundle

class EvidenceAggregator:
    """
    Aggregates structured and policy evidence into a single EvidenceBundle.
    Responsible for normalization, deduplication, sorting, and identifying missing evidence.
    """
    def aggregate(
        self,
        dispute_id: str,
        structured_evidence: List[EvidenceItem],
        policy_evidence: List[EvidenceItem],
        expected_categories: List[str],
        metadata: Dict[str, Any]
    ) -> EvidenceBundle:
        
        # Deduplicate structured evidence (e.g. same field fetched multiple times)
        unique_structured = self._deduplicate(structured_evidence)
        # Deduplicate policy evidence
        unique_policy = self._deduplicate(policy_evidence)
        
        # Sort policy evidence by relevance
        unique_policy.sort(key=lambda x: x.relevance_score or 0.0, reverse=True)
        
        # Identify missing categories based on the expected_categories from the Case Evidence Plan
        found_categories = set()
        for item in unique_structured:
            # We map field prefixes to categories if possible, or assume it's met if we have any structured data
            # For a more rigorous check, we'd need the field-to-category mapping.
            # We'll just do a basic check here for demonstration.
            # The Case Planner outputs 'evidence_categories'.
            pass
            
        # In a real rigorous system, we'd check if the fetched fields fulfill the expected_categories.
        # Here we just mark categories with 0 evidence items as missing.
        missing_evidence = []
        if not unique_structured:
            missing_evidence.append("Structured data is entirely missing or null.")
            
        if not unique_policy:
            missing_evidence.append("Policy documents for this allegation are missing.")

        return EvidenceBundle(
            dispute_id=dispute_id,
            structured_evidence=unique_structured,
            policy_evidence=unique_policy,
            missing_evidence=missing_evidence,
            retrieval_metadata=metadata
        )

    def _deduplicate(self, items: List[EvidenceItem]) -> List[EvidenceItem]:
        seen = set()
        unique = []
        for item in items:
            # Create a unique key based on source_type, source_id, and field/chunk
            # For structured: it's the DB record ID + field name
            # For policy: it's the chunk ID
            
            key = None
            if item.source_type == "postgresql":
                field = item.provenance.get("field", "")
                key = f"{item.source_type}:{item.source_id}:{field}"
            elif item.source_type == "policy":
                key = f"{item.source_type}:{item.source_id}"
                
            if key and key not in seen:
                seen.add(key)
                unique.append(item)
            elif not key:
                unique.append(item)
                
        return unique
