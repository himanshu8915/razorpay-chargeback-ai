import time
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.case_service import CaseService
from app.evidence.structured.field_registry import ALLOWED_CASE_FIELDS
from app.agents.evidence_discovery.case_evidence_planner import plan_case_evidence
from app.agents.evidence_discovery.policy_evidence_planner import plan_policy_evidence
from app.evidence.structured.retriever import StructuredEvidenceRetriever
from app.evidence.policy.retriever import PolicyEvidenceRetriever
from app.evidence.aggregation.evidence_aggregator import EvidenceAggregator
from app.evidence.models.evidence_bundle import EvidenceBundle
from app.decision.models.factors import TokenUsage
from app.usage.dispute_token_tracker import persist_usage_record

logger = logging.getLogger(__name__)

class EvidenceDiscoveryService:
    """
    Orchestrates Phase 3 Evidence Discovery:
    1. Loads the CanonicalCase.
    2. Runs Case Evidence Planner.
    3. Runs Structured Retrieval.
    4. Runs Policy Evidence Planner (using case context).
    5. Runs Policy Retrieval (Hybrid + Rerank).
    6. Aggregates and returns EvidenceBundle.

    Token usage from Phase 3 LLM planners is collected and returned
    for cross-phase dispute-scoped cost accounting.
    """
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.case_service = CaseService(db_session)
        self.structured_retriever = StructuredEvidenceRetriever()
        self.policy_retriever = PolicyEvidenceRetriever(db_session)
        self.aggregator = EvidenceAggregator()
        
    async def discover_evidence(self, dispute_id: str) -> tuple[EvidenceBundle, TokenUsage]:
        """
        Returns (EvidenceBundle, TokenUsage) where TokenUsage covers Phase 3 LLM planners.
        Callers must persist the TokenUsage for cumulative accounting.
        """
        metadata = {}
        phase3_usage = TokenUsage()  # accumulate Phase 3 planner tokens
        
        # 1. Load Case
        t0 = time.time()
        case = await self.case_service.get_case(dispute_id)
        metadata["t_load_case"] = time.time() - t0
        
        # 2. Case Evidence Planner — now returns (plan, usage)
        t1 = time.time()
        case_plan, case_planner_usage = plan_case_evidence(case, ALLOWED_CASE_FIELDS)
        await persist_usage_record(
            db=self.db,
            dispute_id=dispute_id,
            phase="phase3",
            token_usage=case_planner_usage,
            node="case_evidence_planner"
        )
        phase3_usage = TokenUsage(
            input_tokens=phase3_usage.input_tokens + case_planner_usage.input_tokens,
            output_tokens=phase3_usage.output_tokens + case_planner_usage.output_tokens,
            total_tokens=phase3_usage.total_tokens + case_planner_usage.total_tokens,
            model=case_planner_usage.model
        )
        metadata["t_case_planner"] = time.time() - t1
        
        # 3. Structured Retrieval (no LLM)
        t2 = time.time()
        structured_evidence = self.structured_retriever.retrieve(case, case_plan)
        metadata["t_structured_retrieval"] = time.time() - t2
        
        # 4. Policy Evidence Planner — now returns (plan, usage)
        t3 = time.time()
        relevant_context = {item.provenance.get("field"): item.content for item in structured_evidence}
        policy_plan, policy_planner_usage = plan_policy_evidence(case, relevant_context)
        await persist_usage_record(
            db=self.db,
            dispute_id=dispute_id,
            phase="phase3",
            token_usage=policy_planner_usage,
            node="policy_evidence_planner"
        )
        phase3_usage = TokenUsage(
            input_tokens=phase3_usage.input_tokens + policy_planner_usage.input_tokens,
            output_tokens=phase3_usage.output_tokens + policy_planner_usage.output_tokens,
            total_tokens=phase3_usage.total_tokens + policy_planner_usage.total_tokens,
            model=policy_planner_usage.model
        )
        metadata["t_policy_planner"] = time.time() - t3
        
        # 5. Policy Retrieval (no LLM — hybrid BM25+vector)
        t4 = time.time()
        policy_evidence = await self.policy_retriever.retrieve(policy_plan)
        metadata["t_policy_retrieval_hybrid_rerank"] = time.time() - t4
        
        # 6. Aggregation (no LLM)
        t5 = time.time()
        bundle = self.aggregator.aggregate(
            dispute_id=dispute_id,
            structured_evidence=structured_evidence,
            policy_evidence=policy_evidence,
            expected_categories=case_plan.evidence_categories,
            metadata=metadata
        )
        metadata["t_aggregation"] = time.time() - t5
        
        metadata["t_total_phase3"] = time.time() - t0
        
        logger.info(
            f"Evidence discovery complete for {dispute_id} "
            f"in {metadata['t_total_phase3']:.2f}s, "
            f"Phase 3 LLM tokens: {phase3_usage.total_tokens}"
        )
        return bundle, phase3_usage
