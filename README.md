# Chargeback Intelligence (Razorpay Hackathon Submission)

An evidence-driven, agentic chargeback decision system that answers four fundamental merchant questions per dispute:

1. **Should I fight this dispute?**
2. **Why do we believe we can win?**
3. **What evidence proves or contradicts the claim?**
4. **What happens next, and who needs to act before the deadline?**

## Overview

The system transforms the manual, fragmented chargeback investigation workflow into an AI-orchestrated evidence-reasoning pipeline with structured human escalation for ambiguous cases.

**Decision outputs:** `CONTEST` / `HUMAN_REVIEW` / `ACCEPT` — each with full, auditable evidence and policy reasoning.

## Final Hackathon Architecture

This submission has been rigorously optimized for a highly deterministic, self-contained evaluation environment.

*   **100% PyTorch-Free:** We completely excised heavy local ML dependencies (Transformers, SentenceTransformers). All semantic reasoning and embeddings are powered exclusively by Google Gemini (`gemini-1.5-pro` for reasoning, `gemini-embedding-001` for vector representations).
*   **Zero External Dependencies:** The application requires no external data downloads at runtime. The dataset and pre-computed embeddings are packaged directly into a deterministic PostgreSQL seed (`demo_seed.sql`).
*   **Deterministic Evaluation:** The frontend natively locks to the top 5 active merchants to ensure consistent, highly curated, and reproducible demo flows.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python, FastAPI, Pydantic |
| **ORM** | SQLAlchemy (async) |
| **Database** | PostgreSQL + pgvector |
| **Agent Orchestration** | LangGraph |
| **LLM / Embeddings** | Google Gemini (`gemini-1.5-pro`, `gemini-embedding-001`) |
| **RAG** | LangChain, pgvector, Reciprocal Rank Fusion (BM25 + Vector) |
| **Frontend** | Next.js, React, TypeScript, TailwindCSS |
| **Infrastructure** | Docker, Docker Compose |

## Repository Structure

```text
razorpay-chargeback-ai/
├── backend/          # FastAPI application, LangGraph agents, RRF Hybrid RAG
├── frontend/         # Next.js merchant dashboard
├── data/             # Contains deterministic demo_seed.sql (PostgreSQL dump)
├── docker/           # Per-service Dockerfiles and init scripts
└── docker-compose.yml
```

## 🚀 Local Setup (Evaluator Guide)

We have intentionally packaged the entire stack (Database, Backend, and Next.js Frontend) into a single Docker Compose environment so you can evaluate it instantly without installing local dependencies.

### Prerequisites

- **Docker Desktop** (No Node.js, Python, or PyTorch required locally!)
- A valid Google API Key (for `gemini-1.5-pro` & `gemini-embedding-001`)

### 1. Environment Setup

Copy `.env.example` to `.env` and fill in your Google credentials:

```bash
cp .env.example .env
```

Ensure the following variables are set in `.env`:
- `GOOGLE_API_KEY` — Your Gemini API Key
- `LLM_PROVIDER` — Set to `google`
- `LLM_MODEL` — Set to `gemini-3.5-flash-lite` (or `gemini-1.5-pro`)
- `DATABASE_URL` — (Leave as default)

### 2. Launch the Entire Application

From the root directory, simply run:

```bash
docker compose up --build -d
```

> [!NOTE] 
> **You do NOT need to run any `npm` or `pip` commands.** 
> Docker will automatically build the Next.js frontend, install the FastAPI backend, and boot up PostgreSQL. The PostgreSQL container will also automatically ingest the `demo_seed.sql` on its first run, which contains our 5 merchants, 836 disputes, and 809 pre-computed 768-dimensional Gemini vectors for immediate RAG capabilities.

### 3. Access the Dashboard

Once the containers are running, the frontend is immediately available at:
👉 **[http://localhost:3000](http://localhost:3000)**

## Core AI Workflow (Implementation Phases)

Our LangGraph implementation executes a rigorous, multi-stage reasoning pipeline:

1.  **Canonical Case Assembly:** Aggregates structured transactional facts (Orders, Customers, Deliveries) into a single deterministic schema.
2.  **Evidence Discovery & Verification:** AI agents inspect the canonical case against specific chargeback reason codes to determine if compelling evidence (e.g., AVS match, delivery confirmation) exists.
3.  **Policy RAG (Hybrid Search):** Executes Reciprocal Rank Fusion (RRF), combining lexical BM25 search with semantic `gemini-embedding-001` vectors to extract relevant Razorpay policies.
4.  **Decision Intelligence:** The final LangGraph node synthesizes the verified evidence and retrieved policies to render a `CONTEST`, `ACCEPT`, or `HUMAN_REVIEW` verdict.
5.  **Representment Generation:** For `CONTEST` decisions, the AI automatically drafts a highly professional, evidence-backed representment letter ready for submission.
