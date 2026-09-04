# Phase 3 Status: Evidence Discovery Implementation

## Overall Status: 🟢 COMPLETE & VERIFIED

All code and architecture for Phase 3 has been fully scaffolded, implemented, and rigorously tested against the Phase 1, Phase 2, and Phase 3 integration and regression suites. The system successfully performs end-to-end evidence discovery (Case Planning -> Structured Retrieval -> Policy Planning -> Hybrid Retrieval -> Reranking -> Aggregation) and flawlessly produces a hydrated `EvidenceBundle` from a real PostgreSQL database `CanonicalCase`.

### Final Architecture & Completed Components

1. **LLM Gateway (`app/llm/gateway.py`)**
   - **Pivoted Architecture**: Removed `LiteLLM` routing logic to reduce abstraction complexity. 
   - Wired to map directly to native LangChain providers (`ChatGoogleGenerativeAI` and `ChatGroq`) via the `.env` file configuration.
   - Tested and fully working with `gemma-4-31b-it`.

2. **Data Models (`app/evidence/models/`)**
   - `EvidenceItem`: Enforces strict provenance linking (`source_type`, `record_id`, `chunk_id`).
   - `EvidenceBundle`: Structures the final aggregated output passed back to the client or downstream Phase 4 components.

3. **Planners (`app/agents/evidence_discovery/`)**
   - **Case Evidence Planner**: Uses a 1-shot JSON format template and robust Regex-to-JSON extraction to bypass Google SDK array/function-calling bugs, outputting `CaseEvidencePlan`.
   - **Policy Evidence Planner**: Uses the same robust JSON extraction methodology to formulate targeted semantic search queries.

4. **Retrieval Pipelines (`app/evidence/structured/` & `app/evidence/policy/`)**
   - **Structured Retriever**: Safely and deterministically extracts data directly from the `CanonicalCase` based on the strict `ALLOWED_CASE_FIELDS` registry, mapping them to `EvidenceItem`.
   - **Hybrid Policy Retriever**: Performs in-memory lexical search (`rank_bm25`) + semantic vector search (`pgvector`) fused deterministically via Reciprocal Rank Fusion (RRF).
   - **Reranker**: Implements `BAAI/bge-reranker-small` via a local Cross-Encoder to guarantee high-precision document relevance.

5. **Orchestration (`app/evidence/services/evidence_discovery_service.py`)**
   - Acts as the central nervous system bridging the planners, retrievers, and aggregators sequentially, measuring timing telemetry along the way.
   - **(Phase 5 Upgrade)**: The service and its planners were instrumented to return `tuple[EvidenceBundle, TokenUsage]`, propagating LLM token consumption up to the caller for cross-phase operational cost accounting.

### Verification Results

- **Unit Tests**: All planners, models, and retrievers pass their unit tests.
- **Integration Test (`test_evidence_discovery.py`)**: Passed with 0 failures. The pipeline executed end-to-end natively and reliably.
- **Regression Suite**: The entire full regression test suite (Phase 2 canonical cases, services, API logic) ran and verified that zero regressions were introduced.

Phase 3 is fully frozen and ready to act as the direct, stable dependency for Phase 4 (Evidence Verification).
