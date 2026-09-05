# Chargeback AI

### Evidence-driven, multi-agent chargeback decisioning for merchants.

**Chargeback AI** is a decision system for merchant chargebacks. It investigates a dispute using verified transactional evidence and applicable policy, evaluates confidence, risk and economics, and routes the case to:

`CONTEST` · `ACCEPT` · `NEEDS_EVIDENCE` · `ESCALATE`

> **We didn't build an AI that simply writes chargeback rebuttals. We built the decision layer that determines whether a dispute should be fought, why, and what evidence justifies that decision.**

Built for **Razorpay AI Risk Manager — Track 02**.

---

## 1. The Problem

Chargeback operations have two forms of leakage:

- **Under-contesting:** merchants leave potentially recoverable disputes undisputed.
- **Over-investigation:** teams spend time and money investigating cases that are weak or not worth pursuing.

Industry research used for our problem framing reports:

| Signal | Industry evidence |
|---|---:|
| Projected annual chargeback value by 2029 | **$46.1B** |
| Projected chargeback transactions/year by 2029 | **359M** |
| Average cost per chargeback | **~$128** |
| Merchants leaving at least 40% of chargebacks undisputed | **~60%** |
| Merchants calling chargeback management too time-consuming, complex and manual | **55%** |

*Sources: Mastercard / Datos Insights; Riskified + Paladin.*

Existing chargeback infrastructure already handles much of the workflow: dispute intake, evidence collection, deadlines and submission.

The harder problem is the **decision layer**:

- Should we fight this dispute?
- What evidence supports or contradicts the claim?
- What policy requirements apply?
- Is the expected recovery worth the operational cost?
- When should the system stop and ask a human?

That is the gap Chargeback AI targets.

---

## 2. What We Built

A dispute moves through an evidence-driven workflow:

```text
DISPUTE
   │
   ▼
CASE RECONSTRUCTION
   │
   ▼
EVIDENCE PLAN
   │
   ├───────────────┐
   ▼               ▼
STRUCTURED       POLICY
EVIDENCE          RAG
   │               │
   └───────┬───────┘
           ▼
   EVIDENCE REASONING
           │
           ▼
    CONFIDENCE + RISK
           │
           ▼
       ECONOMICS
           │
           ▼
   DETERMINISTIC DECISION
      /      |       \
     /       |        \
CONTEST    ACCEPT   ESCALATE
                    /
             NEEDS_EVIDENCE
           │
           ▼
   REPRESENTMENT + CRITIC
```

### A concrete example

For a **₹1,249 Product Not Received** dispute, the system can establish:

```text
Delivery status       → DELIVERED
Delivery timestamp    → Apr 13
Dispute claim         → Product not received
Refund status         → NO REFUND
```

The evidence engine turns these records into addressable `EvidenceItem`s.

The reasoning layer determines whether each item:

- supports the merchant,
- contradicts the claim,
- does not address the claim,
- or exposes missing/conflicting evidence.

The decision layer then combines evidence strength, confidence, risk and expected economics before routing the case.

**Generation comes after decisioning — not before it.**

### System at a glance

| Decision stage | System responsibility | Control |
|---|---|---|
| **Understand** | Build the canonical case from verified records | SQL + constrained planning |
| **Retrieve** | Find structured evidence and applicable policy | Evidence IDs + hybrid RAG |
| **Reason** | Assess support, contradiction, gaps and conflicts | Structured outputs + grounding validation |
| **Assess** | Score strength, confidence, risk and economics | Deterministic post-processing |
| **Decide** | Route to contest, accept, evidence request or escalation | Deterministic decision engine |
| **Act** | Generate and validate representment when justified | Agent + critic + HITL |

---

## 3. Architecture

### Multi-agent workflow

| Component | Responsibility |
|---|---|
| **Case Understanding Agent** | Determines what case information is required |
| **Evidence Retrieval Agent** | Plans and retrieves relevant structured evidence |
| **Policy Evidence Agent** | Retrieves applicable policy/rule context |
| **Evidence Reasoning Agent** | Maps evidence to the dispute claim |
| **Decision Supervisor** | Evaluates strength, confidence, risk and economics |
| **Representment Agent** | Generates the response only for justified contests |
| **Critic / Review Agent** | Checks the generated response against evidence and requirements |
| **LangGraph** | Orchestrates state, routing, retries and workflow recovery |

The agents do not independently invent facts or directly control the final decision.

### Data and knowledge separation

**Structured merchant data → PostgreSQL / SQL**

Transaction, order, delivery, payment, customer and dispute records are assembled into a canonical case.

**Unstructured policy knowledge → RAG**

Policy and procedural documents are chunked and retrieved separately.

This keeps the fundamental distinction explicit:

> **SQL establishes what happened. RAG establishes what rules apply. The agents reason over both.**

---

## 4. Hybrid RAG

Policy retrieval combines lexical and semantic retrieval:

```text
Policy corpus
     │
     ├── BM25 lexical search
     │
     └── pgvector semantic search
              │
              ▼
       RRF fusion / ranking
              │
              ▼
        Policy context
```

Current implementation:

- **809** pre-seeded policy chunks
- `gemini-embedding-001` embeddings
- **768-dimensional** pgvector representation
- BM25 lexical retrieval
- Reciprocal Rank Fusion (RRF)
- Policy metadata used to constrain relevant context

Transactional records are **not** unnecessarily embedded; they remain structured data.

---

## 5. Guardrails and Failure Handling

The LLM is not the final authority.

### Grounding

Every retrieved evidence item receives an `Evidence ID`.

The reasoning agent can only cite evidence present in the actual `EvidenceBundle`.

If an invalid evidence reference is produced:

```text
Invalid Evidence ID
       ↓
Grounding validation fails
       ↓
Retry
```

### Deterministic decisioning

Critical decision conditions are enforced outside the LLM:

```text
Critical conflict       → ESCALATE
Policy ambiguity        → ESCALATE
Missing critical data   → NEEDS_EVIDENCE
Low confidence          → ESCALATE
Positive net value      → CONTEST
Otherwise               → ACCEPT
```

### Workflow recovery

| Failure / condition | System response |
|---|---|
| Invalid structured output | Retry |
| Invalid evidence reference | Grounding validation → retry |
| Missing critical evidence | `NEEDS_EVIDENCE` |
| Conflicting evidence | `ESCALATE` |
| Policy ambiguity | `ESCALATE` |
| Low confidence | `ESCALATE` |
| Critic identifies an issue | Revise and re-check |
| Workflow timeout | Fail safely |

This is deliberate: **a good risk system is not one that always decides. It knows when not to decide.**

---

## 6. Decision Economics

The system does not treat every dispute as equally worth pursuing.

It calculates:

```text
Recoverable Amount
    = Dispute Amount × Recovery Rate

Expected Recovery
    = Success Likelihood × Recoverable Amount

Net Expected Value
    = Expected Recovery − Operational Cost
```

Success likelihood incorporates evidence completeness, case strength, policy alignment and confidence.

The final decision combines:

- dispute amount
- recoverable amount
- evidence completeness
- case strength
- confidence
- policy alignment
- risk flags
- deadline risk
- operational cost
- expected recovery

This lets the system answer not only:

> **“Can we fight this?”**

but:

> **“Is fighting this case economically justified?”**

---

## 7. Human-in-the-Loop

Cases with uncertainty are not forced through automation.

Human review is triggered by conditions such as:

- conflicting evidence
- missing critical evidence
- policy ambiguity
- low confidence
- other high-risk conditions

The reviewer can:

- approve the recommendation
- edit the decision
- request evidence
- escalate the case

Human actions and overrides are persisted so that:

`AI recommendation ≠ final decision`

when human review is required.

---

## 8. Representment + Critic

Only after a `CONTEST` decision does the system generate the representment response.

The response is grounded in:

- verified case evidence
- evidence IDs
- applicable policy
- dispute-specific requirements

The critic checks for:

- unsupported claims
- incorrect evidence references
- contradictions
- missing requirements
- factual inconsistencies
- completeness

If the critic finds a problem, the workflow can revise and re-check the response.

**The rebuttal is the final artifact. The decision is the product.**

---

## 9. Observability and Auditability

Every investigation produces a traceable decision path:

```text
Claim
  → Canonical Case
  → Evidence
  → Policy
  → Reasoning
  → Confidence
  → Economics
  → Decision
  → Human Action
```

**LangSmith** provides workflow observability across LangGraph execution, agent calls, retries, latency, failures and LLM usage.

The application also persists decision artifacts including:

- decision
- confidence
- case strength
- expected recovery
- recoverable amount
- operational cost
- evidence references
- rationale / reason codes
- token usage and cost
- workflow status
- human review / overrides

The result is an answer to:

> **“Why did the system make this recommendation?”**

rather than only a final LLM response.

---

## 10. Evaluation

Evaluation is being finalized on a held-out benchmark.

### Metrics

We will report four primary groups:

| Metric | What it measures |
|---|---|
| **Decision Quality** | Whether the system makes the right contest / accept / escalation decisions |
| **Evidence Grounding Rate** | Whether reasoning is supported by retrieved evidence |
| **HITL Quality** | Whether uncertain/high-risk cases are routed to humans appropriately |
| **Economics** | Recovery value relative to operational / model cost |

### Results

**Evaluation run in progress — final numbers will be added here before submission.**

> We will report measured results on the held-out benchmark rather than presenting synthetic benchmark characteristics as industry statistics.

---

## 11. Dataset

The system uses a synthetic benchmark and a frozen demo portfolio.

### Dataset materialization

| Stage | Scale | Purpose |
|---|---:|---|
| **Original synthetic benchmark** | **3,095 merchants** | Full benchmark population |
|  | **10,000 disputes** | Dispute cases |
|  | **325,863 entity rows** | Relational data across the benchmark |
| **Frozen demo portfolio** | **5 merchants** | Deterministic demo selection |
|  | **836 associated disputes** | Full dispute portfolio for selected merchants |
| **Live / analyzable demo pool** | **390 cases** | Cases currently exposed for analysis in the product |

The benchmark is **synthetic and controlled**. Its class distribution should not be interpreted as industry prevalence.

### Dispute classes

| Dispute type | Cases |
|---|---:|
| Fraud | 2,000 |
| Product not received | 1,500 |
| Unauthorized transaction | 1,500 |
| Duplicate charge | 1,000 |
| Product not as described | 1,000 |
| Refund not received | 1,000 |
| Processing error | 1,000 |
| Other | 1,000 |
| **Total** | **10,000** |

The policy knowledge base contains **809 pre-seeded policy chunks** used by the hybrid retrieval layer.

---

## 12. Tech Stack

| Layer | Technology | Role |
|---|---|---|
| **Frontend** | Next.js · React · TypeScript · Tailwind CSS | Merchant dashboard and case workspace |
| **API** | Python · FastAPI · Pydantic | Backend APIs and typed request/response contracts |
| **Data** | PostgreSQL · SQLAlchemy | Structured merchant, transaction and dispute data |
| **Vector Search** | pgvector | Semantic policy retrieval |
| **Retrieval** | BM25 + semantic search + RRF | Hybrid policy retrieval |
| **Agent Orchestration** | LangGraph | Stateful workflow, branching and retries |
| **Agent / LLM Framework** | LangChain ecosystem | LLM integration, structured generation and agent tooling |
| **Reasoning** | Google Gemini · `gemini-3.5-flash-lite` | Agent reasoning and structured outputs |
| **Embeddings** | `gemini-embedding-001` | Policy embeddings |
| **Evaluation** | pytest · DeepEval | Unit, workflow and RAG evaluation |
| **Observability** | LangSmith / LangChain ecosystem | Agent traces, retrieval traces, latency, failures and LLM usage |
| **Runtime** | Docker · Docker Compose | Reproducible local deployment |

> **Core AI stack:** LangGraph + LangChain + Gemini + pgvector + BM25/RRF + LangSmith.  
> **Evaluation stack:** pytest + DeepEval.

---

## 13. Run Locally

### Repository

```text
backend/       → FastAPI + LangGraph + decision pipeline
frontend/      → Next.js merchant dashboard
data/          → benchmark / seed data
docker/        → container configuration
docker-compose → local orchestration
```

### Requirements

- Docker Desktop
- Google Gemini API key

### Start

```bash
cp .env.example .env
```

Add the required credentials to `.env`, then:

```bash
docker compose up --build
```

The application starts the PostgreSQL database, initializes the required data and launches the backend and frontend.

Open the frontend at:

```text
http://localhost:3000
```

Backend:

```text
http://localhost:8000
```

Check `.env.example` for the exact environment variables required by the current implementation.

---

## 14. What Is Built

### Built

- End-to-end dispute investigation
- LangGraph orchestration
- SQL-backed canonical case reconstruction
- Structured evidence planning and retrieval
- Hybrid policy RAG
- BM25 + pgvector + RRF
- Structured outputs
- Evidence-ID grounding validation
- Deterministic confidence and decision routing
- Risk and economics calculations
- Human-in-the-loop review
- Representment generation
- Critic / revision loop
- LangSmith observability
- Decision audit trail
- Dockerized local execution

### Remaining

- Final held-out evaluation results
- Merchant-specific calibration from historical outcomes
- Live payment-network submission integration

---

## 15. Limitations

This is a hackathon MVO, not a production payment-network system.

Current limitations include:

- synthetic benchmark data
- bounded policy corpus
- deterministic economic assumptions
- limited historical outcome feedback
- no live network representment submission

The architecture is intentionally designed so these can be replaced or extended without changing the core decision workflow.

---

## Final

**Chargeback AI is not an LLM wrapped around a chargeback form.**

It is an evidence-driven decision system:

```text
Facts       → SQL
Policies    → Hybrid RAG
Evidence    → Structured + grounded
Reasoning   → Specialized agents
Risk        → Deterministic checks
Economics   → Expected recovery
Decision    → Deterministic routing
Uncertainty → Human review
Response    → Agent + critic
Audit       → LangSmith + persisted artifacts
```

**The goal is simple: fight the disputes worth fighting, stop wasting effort on the ones that aren't, and never hide uncertainty behind an LLM-generated answer.**

Built for **Razorpay AI Risk Manager — Track 02**.
