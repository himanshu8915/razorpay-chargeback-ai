import logging
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.evidence_discovery.schemas import PolicyEvidencePlan
from app.evidence.models.evidence_item import EvidenceItem
from app.evidence.policy.hybrid_search import HybridRetriever

from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class PolicyEvidenceRetriever:
    """
    Orchestrates the hybrid search and reranking based on the PolicyEvidencePlan.
    """
    def __init__(self, db_session: AsyncSession):
        self.hybrid_retriever = HybridRetriever(db_session)
        self.reranker = None
        
    def _load_reranker(self):
        pass
        
    async def retrieve(self, plan: PolicyEvidencePlan, top_k: int = 5) -> List[EvidenceItem]:
        all_candidates = []
        
        # Execute hybrid retrieval for each query in the plan
        # We process them sequentially or concurrently, here sequentially for simplicity
        for query in plan.search_queries:
            # 1. Get query embedding
            try:
                q_emb = await self.hybrid_retriever.get_embedding(query)
            except Exception as e:
                logger.error(f"Failed to generate embedding for query '{query}': {e}")
                continue
                
            # 2. Hybrid retrieve top 15 candidates per query
            candidates = await self.hybrid_retriever.retrieve(query, q_emb, limit=15)
            all_candidates.extend(candidates)
            
        if not all_candidates:
            return []
            
        # Deduplicate candidates before reranking
        seen_chunks = set()
        unique_candidates = []
        for c in all_candidates:
            if c["chunk_id"] not in seen_chunks:
                unique_candidates.append(c)
                seen_chunks.add(c["chunk_id"])
                
        # 3. Rerank unique candidates against a combined representation of the queries
        # Or against the primary topics. We'll use a joined string of the queries as the overarching intent.
        combined_query = " ".join(plan.search_queries)
        
        # 3. No local neural reranking per architectural simplifications.
        # RRF (Reciprocal Rank Fusion) from the hybrid search is deterministic and used as the final score.
        unique_candidates.sort(key=lambda x: x.get("rrf_score", 0), reverse=True)
        reranked = unique_candidates[:top_k]
            
        # 4. Map to EvidenceItems
        evidence_items = []
        for doc in reranked:
            score = doc.get("rerank_score", doc.get("rrf_score", 0.0))
            
            # Extract relevant metadata
            policy_id = doc["policy_id"]
            chunk_id = doc["chunk_id"]
            title = doc.get("title", "Unknown Policy")
            version = doc.get("version", "Unknown")
            
            item = EvidenceItem(
                evidence_id=f"EV-POL-{uuid.uuid4().hex[:8]}",
                evidence_type="policy_chunk",
                source_type="policy",
                source_id=chunk_id,
                content={
                    "text": doc["content"],
                    "policy_id": policy_id,
                    "title": title,
                    "version": version
                },
                relevance_score=score,
                timestamp=datetime.utcnow(),
                provenance={
                    "document_id": policy_id,
                    "chunk_id": chunk_id,
                    "section": title,
                    "version": version
                }
            )
            evidence_items.append(item)
            
        return evidence_items
