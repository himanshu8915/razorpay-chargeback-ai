# System Architecture

## Two-Track Initialization

```
docker compose up
       │
  ┌────┴────────────────────┐
  │                         │
CRITICAL PATH          BACKGROUND PATH
  │                         │
PostgreSQL           Policy documents (8 POL-*.*)
Dataset download     Chunking
Dataset import       Embeddings → pgvector
  │                         │
STRUCTURED READY     VECTOR_INDEX_READY
  │                         │
DASHBOARD ◄──────────────── ┘ (background, non-blocking)
```

### Track A — Critical (blocks dashboard)
`NOT_STARTED → DATABASE_STARTING → DATASET_INITIALIZING → STRUCTURED_DATA_READY → APPLICATION_READY`

### Track B — Background (non-blocking)
`RAG_INITIALIZATION → DOCUMENT_LOADING → CHUNKING → EMBEDDING → VECTOR_INDEX_READY`

## Services (Docker Compose)

| Service | Purpose |
|---------|---------|
| `postgres` | PostgreSQL 16 + pgvector — structured data + vector store |
| `dataset-init` | One-shot: download Kaggle dataset → import into PostgreSQL |
| `backend` | FastAPI application, agents, LangGraph workflows |
| `frontend` | Next.js merchant dashboard |

## Data Architecture

### Structured Data (PostgreSQL)
- Entities: customers, merchants, orders, transactions, deliveries, disputes
- Operational: cases, case_evidence, decisions, human_reviews, agent_runs, audit_events
- Agent reads via repository layer — never raw SQL from agent code

### Policy Knowledge (pgvector)
- 8 policy documents chunked and embedded
- Metadata-filtered hybrid retrieval
- RAG readiness checked before every retrieval

## Agent Architecture

```
LangGraph Orchestrator
         │
    ┌────┴─────────────────────────┐
    │                              │
Case Understanding          Evidence Discovery
    │                         Supervisor
    │                      ┌────┴────┐
    │                      │         │
    │                  Structured Knowledge
    │                  Evidence    Evidence
    │                      │         │
    │                      └────┬────┘
    │                           │
Evidence Verification ──────────┘
    │
Policy Retrieval (RAG)
    │
Decision Agent
    │
 ┌──┼──┐
 │  │  │
CON REV ACC
    │
Explanation Agent
    │
Representment Agent
    │
Deterministic Validation
```

## Non-negotiable Architectural Rules

1. PostgreSQL is the canonical structured-data source.
2. LLMs reason; they do not invent database facts.
3. RAG is for knowledge/policy, not everything.
4. Embeddings must never block initial dashboard startup.
5. Before using RAG, explicitly check whether the vector index is ready.
6. Initialization must be idempotent.
7. Every important operation produces progress information.
8. Every agent has its own modular folder.
9. LangGraph orchestrates; agents perform focused responsibilities.
10. AI recommendation and human final decision are separate states.
11. Final representations undergo deterministic validation.
12. Every decision must be explainable through evidence and policy.
