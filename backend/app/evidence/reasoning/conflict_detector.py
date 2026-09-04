from typing import List
from app.evidence.models.evidence_bundle import EvidenceBundle
from app.evidence.models.evidence_conflict import EvidenceConflict

def detect_conflicts(bundle: EvidenceBundle) -> List[EvidenceConflict]:
    """
    Deterministically detects factual conflicts in the EvidenceBundle.
    """
    conflicts: List[EvidenceConflict] = []
    
    # Simple deterministic rule base for demonstration based on the PRD examples
    
    # Find order status
    order_items = [i for i in bundle.structured_evidence if "order" in i.provenance.get("field", "").lower() or i.evidence_type == "field_status"]
    # We can also just look at the raw content dictionary
    
    order_status = None
    order_item_id = None
    
    delivery_status = None
    delivery_item_id = None
    
    for item in bundle.structured_evidence:
        content = item.content
        if "order_status" in content:
            order_status = content["order_status"]
            order_item_id = item.evidence_id
        if "delivery_state" in content or "status" in content:
            # handle both naming conventions
            status_val = content.get("delivery_state", content.get("status"))
            if status_val in ["delivered", "shipped", "pending"]:
                delivery_status = status_val
                delivery_item_id = item.evidence_id
                
    if order_status == "cancelled" and delivery_status == "delivered":
        conflicts.append(EvidenceConflict(
            evidence_ids=[order_item_id, delivery_item_id],
            topic="fulfillment_status",
            description="Order is marked cancelled while delivery record indicates delivered.",
            severity="high"
        ))
        
    # Another example: refund completed vs pending
    refund_statuses = []
    refund_ids = []
    for item in bundle.structured_evidence:
        content = item.content
        if "refund_status" in content:
            refund_statuses.append(content["refund_status"])
            refund_ids.append(item.evidence_id)
            
    if "completed" in refund_statuses and "pending" in refund_statuses:
        conflicts.append(EvidenceConflict(
            evidence_ids=refund_ids,
            topic="refund_status",
            description="Conflicting refund statuses found (completed vs pending).",
            severity="high"
        ))
        
    return conflicts
