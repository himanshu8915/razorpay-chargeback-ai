import logging
from typing import List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.db.models import PolicyChildChunk, PolicyDocument, PolicyParentChunk
from rank_bm25 import BM25Okapi

logger = logging.getLogger(__name__)

class HybridRetriever:
    """
    Performs hybrid retrieval using lexical search (BM25) and semantic search (pgvector).
    Fuses the candidate sets deterministically.
    """
    def __init__(self, db_session: AsyncSession, embedding_model_name: str = "models/gemini-embedding-001"):
        self.db = db_session
        self.embedding_model_name = embedding_model_name
        self.embedder = None
        
    def _load_embedder(self):
        if self.embedder is None:
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
            from app.config.settings import settings
            logger.info(f"Loading Google Gemini embedding model: {self.embedding_model_name}")
            self.embedder = GoogleGenerativeAIEmbeddings(
                model=self.embedding_model_name,
                task_type="RETRIEVAL_QUERY",
                google_api_key=settings.llm_api_key  # Assuming LLM API key can be reused for Gemini, or add a specific one
            )
        
    async def get_embedding(self, query: str) -> List[float]:
        self._load_embedder()
        # GoogleGenerativeAIEmbeddings returns a list of floats directly
        emb = await self.embedder.aembed_query(query)
        # Gemini embeddings can return up to 3072 dimensions, but our DB expects 768.
        # We truncate to 768 dimensions (valid for Matryoshka embeddings).
        return emb[:768]

    async def retrieve(self, query: str, query_embedding: List[float], limit: int = 30) -> List[Dict[str, Any]]:
        # 1. Fetch from Vector (Semantic Search)
        vector_candidates = await self._vector_search(query_embedding, limit)
        
        # 2. Fetch from BM25 (Lexical Search)
        # Note: In a production system at scale, we wouldn't fetch all chunks into memory.
        # But since we have < 1000 chunks (359 chunks precisely as per Phase 1 docs),
        # an in-memory BM25 over the entire corpus is perfectly acceptable and extremely fast.
        bm25_candidates = await self._bm25_search(query, limit)
        
        # 3. Fuse Candidates (Reciprocal Rank Fusion - RRF)
        fused = self._rrf_fusion(vector_candidates, bm25_candidates, top_k=limit)
        
        return fused

    async def _vector_search(self, embedding: List[float], limit: int) -> List[Dict[str, Any]]:
        # pgvector L2 distance operator is <->, Cosine is <=>, Inner Product is <#>
        # We use cosine distance.
        stmt = (
            select(
                PolicyChildChunk.child_chunk_id,
                PolicyChildChunk.policy_id,
                PolicyChildChunk.parent_chunk_id,
                PolicyChildChunk.content,
                PolicyDocument.title,
                PolicyDocument.version,
                PolicyChildChunk.embedding.cosine_distance(embedding).label('distance')
            )
            .join(PolicyDocument, PolicyChildChunk.policy_id == PolicyDocument.policy_id)
            .order_by(PolicyChildChunk.embedding.cosine_distance(embedding))
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        candidates = []
        for row in result:
            candidates.append({
                "chunk_id": row.child_chunk_id,
                "policy_id": row.policy_id,
                "parent_chunk_id": row.parent_chunk_id,
                "content": row.content,
                "title": row.title,
                "version": row.version,
                "score": 1.0 - float(row.distance) # Convert distance to similarity
            })
        return candidates

    async def _bm25_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        # Fetch all chunks (it's only 359 chunks, so completely fine to load into memory)
        stmt = select(
            PolicyChildChunk.child_chunk_id,
            PolicyChildChunk.policy_id,
            PolicyChildChunk.parent_chunk_id,
            PolicyChildChunk.content,
            PolicyDocument.title,
            PolicyDocument.version
        ).join(PolicyDocument, PolicyChildChunk.policy_id == PolicyDocument.policy_id)
        
        result = await self.db.execute(stmt)
        rows = list(result.all())
        
        if not rows:
            return []
            
        corpus = [row.content for row in rows]
        tokenized_corpus = [doc.lower().split(" ") for doc in corpus]
        
        bm25 = BM25Okapi(tokenized_corpus)
        tokenized_query = query.lower().split(" ")
        doc_scores = bm25.get_scores(tokenized_query)
        
        # Get top 'limit' indices
        top_indices = sorted(range(len(doc_scores)), key=lambda i: doc_scores[i], reverse=True)[:limit]
        
        candidates = []
        for idx in top_indices:
            row = rows[idx]
            candidates.append({
                "chunk_id": row.child_chunk_id,
                "policy_id": row.policy_id,
                "parent_chunk_id": row.parent_chunk_id,
                "content": row.content,
                "title": row.title,
                "version": row.version,
                "score": float(doc_scores[idx])
            })
        return candidates

    def _rrf_fusion(self, vector_results: List[Dict], bm25_results: List[Dict], top_k: int, k_const: int = 60) -> List[Dict]:
        """
        Reciprocal Rank Fusion.
        score = 1 / (k + rank_vector) + 1 / (k + rank_bm25)
        """
        ranks = {}
        
        # Helper to map chunk_id to its full object
        chunk_map = {}
        
        for rank, item in enumerate(vector_results):
            cid = item["chunk_id"]
            chunk_map[cid] = item
            if cid not in ranks:
                ranks[cid] = {"vector_rank": rank + 1, "bm25_rank": float('inf')}
            else:
                ranks[cid]["vector_rank"] = rank + 1
                
        for rank, item in enumerate(bm25_results):
            cid = item["chunk_id"]
            if cid not in chunk_map:
                chunk_map[cid] = item
            if cid not in ranks:
                ranks[cid] = {"vector_rank": float('inf'), "bm25_rank": rank + 1}
            else:
                ranks[cid]["bm25_rank"] = rank + 1
                
        fused = []
        for cid, rank_info in ranks.items():
            vr = rank_info["vector_rank"]
            br = rank_info["bm25_rank"]
            
            score = 0.0
            if vr != float('inf'):
                score += 1.0 / (k_const + vr)
            if br != float('inf'):
                score += 1.0 / (k_const + br)
                
            item = chunk_map[cid].copy()
            item["rrf_score"] = score
            fused.append(item)
            
        fused.sort(key=lambda x: x["rrf_score"], reverse=True)
        return fused[:top_k]
