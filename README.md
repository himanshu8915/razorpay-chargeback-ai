# Chargeback Intelligence

An evidence-driven chargeback decision system that answers four fundamental merchant questions per dispute:

1. **Should I fight this dispute?**
2. **Why do we believe we can win?**
3. **What evidence proves or contradicts the claim?**
4. **What happens next, and who needs to act before the deadline?**

## Overview

The system transforms the manual, fragmented chargeback investigation workflow into an AI-orchestrated evidence-reasoning pipeline with structured human escalation for ambiguous cases.

**Decision outputs:** `CONTEST` / `HUMAN_REVIEW` / `ACCEPT` — each with full, auditable evidence and policy reasoning.

## Architecture

```
docker compose up
       │
  ┌────┴────┐
  │         │
CRITICAL   BACKGROUND
 PATH        PATH
  │         │
PostgreSQL  Policy docs
Dataset     Chunking
Import      Embeddings
  │         Vector index
  ▼         │
DASHBOARD ◄─┘ (non-blocking)
  │
Merchant selects dispute
  │
Canonical Case → Evidence Discovery → Evidence Verification
                                           │
                                    Policy Retrieval (RAG)
                                           │
                                    Decision Engine
                                    CONTEST / REVIEW / ACCEPT
                                           │
                                    Explanation + Representment
                                           │
                                    Deterministic Validation
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, FastAPI, Pydantic |
| ORM | SQLAlchemy (async) |
| Database | PostgreSQL + pgvector |
| Agent orchestration | LangGraph |
| LLM | Provider-agnostic gateway (env-configured) |
| RAG | LangChain, pgvector, hybrid retrieval |
| Observability | LangSmith |
| Frontend | Next.js, React, TypeScript, Tailwind |
| Infrastructure | Docker, Docker Compose |

## Repository Structure

```
razorpay-chargeback-ai/
├── backend/          # FastAPI application, agents, workflows, RAG
├── frontend/         # Next.js merchant dashboard
├── data/             # policies/, raw/ (runtime download), benchmark/
├── docker/           # Per-service Dockerfiles and init scripts
├── docs/             # Architecture, API, and development documentation
├── scripts/          # Utility scripts (bootstrap, database, evaluation)
├── tests/            # Shared test fixtures
└── docker-compose.yml
```

## Local Development

### Prerequisites

- Docker Desktop
- (For local dev without Docker) Python 3.12+, Node.js 20+

### Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Required variables:
- `DATABASE_URL` — PostgreSQL connection string
- `LLM_PROVIDER` / `LLM_API_KEY` — LLM gateway configuration
- `LANGSMITH_API_KEY` — LangSmith observability
- `KAGGLE_CONFIG` — Kaggle API credentials (for dataset download in Phase 1)

### Docker Startup

```bash
docker compose up --build
```

The frontend will be available at [http://localhost:3000](http://localhost:3000).

### Testing

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

## Implementation Phases

| Phase | Scope |
|-------|-------|
| **0** | Project foundation (current) |
| 1 | System initialization & dataset import |
| 2 | Canonical case assembly |
| 3 | Evidence discovery & verification |
| 4 | Policy RAG |
| 5 | Decision intelligence & LangGraph workflow |
| 6 | Agentic routing + human-in-the-loop |
| 7 | Representment & deterministic validation |
| 8 | Frontend merchant dashboard |
| 9 | Evaluation, impact metrics & finalization |
