from typing import List, Dict, Any
from datetime import datetime
import uuid
from app.schemas.canonical_case import CanonicalCase
from app.evidence.models.evidence_item import EvidenceItem
from app.agents.evidence_discovery.schemas import CaseEvidencePlan
from app.evidence.structured.field_registry import ALLOWED_CASE_FIELDS

class StructuredEvidenceRetriever:
    """
    Safely retrieves fields from the CanonicalCase object based on the
    LLM's CaseEvidencePlan, strictly validating against the ALLOWED_CASE_FIELDS registry.
    """
    
    def retrieve(self, case: CanonicalCase, plan: CaseEvidencePlan) -> List[EvidenceItem]:
        evidence_items = []
        
        for field_path in plan.relevant_fields:
            parts = field_path.split('.')
            if len(parts) != 2:
                continue
                
            entity_name, field_name = parts[0], parts[1]
            
            # 1. Validate against registry
            if entity_name not in ALLOWED_CASE_FIELDS:
                continue
            if field_name not in ALLOWED_CASE_FIELDS[entity_name]:
                continue
                
            # 2. Extract value from CanonicalCase safely
            entity_obj = getattr(case, entity_name, None)
            if not entity_obj:
                continue
                
            # For lists like transactions or deliveries, we might need to handle them differently.
            # In CanonicalCase:
            # - transaction: TransactionSchema (single)
            # - order: OrderSchema
            # - delivery: DeliverySchema (single or list depending on case logic, usually single in chargeback)
            # - customer: CustomerSchema
            # - merchant: MerchantSchema
            
            # Check if it's a list (e.g., if there are multiple transactions or deliveries)
            if isinstance(entity_obj, list):
                for obj in entity_obj:
                    val = getattr(obj, field_name, None)
                    if val is not None:
                        evidence_items.append(
                            self._create_evidence_item(entity_name, field_name, val, obj)
                        )
            else:
                val = getattr(entity_obj, field_name, None)
                if val is not None:
                    evidence_items.append(
                        self._create_evidence_item(entity_name, field_name, val, entity_obj)
                    )
                    
        return evidence_items
        
    def _create_evidence_item(self, entity_name: str, field_name: str, value: Any, entity_obj: Any) -> EvidenceItem:
        # Determine source_id based on entity
        source_id = "unknown"
        if entity_name == "transaction" and hasattr(entity_obj, "transaction_id"):
            source_id = entity_obj.transaction_id
        elif entity_name == "order" and hasattr(entity_obj, "order_id"):
            source_id = entity_obj.order_id
        elif entity_name == "delivery" and hasattr(entity_obj, "delivery_id"):
            source_id = entity_obj.delivery_id
        elif entity_name == "customer" and hasattr(entity_obj, "customer_id"):
            source_id = entity_obj.customer_id
        elif entity_name == "merchant" and hasattr(entity_obj, "merchant_id"):
            source_id = entity_obj.merchant_id
            
        # Determine appropriate table name
        table_map = {
            "transaction": "transactions",
            "order": "orders",
            "delivery": "deliveries",
            "customer": "customers",
            "merchant": "merchants"
        }
            
        return EvidenceItem(
            evidence_id=f"EV-STRUCT-{uuid.uuid4().hex[:8]}",
            evidence_type=f"field_{field_name}",
            source_type="postgresql",
            source_id=source_id,
            content={field_name: value},
            relevance_score=1.0,  # Structured factual retrieval is exactly relevant
            timestamp=datetime.utcnow(),
            provenance={
                "source_type": "postgresql",
                "table": table_map.get(entity_name, entity_name),
                "record_id": source_id,
                "field": field_name
            }
        )
