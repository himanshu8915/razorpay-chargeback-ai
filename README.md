# Chargeback AI

### Evidence-driven, multi-agent chargeback decisioning for merchants.

**Chargeback AI** is a decision system for merchant chargebacks. It investigates disputes using verified transactional evidence and applicable policy, evaluates confidence, risk and economics, and routes cases to:

`CONTEST` · `ACCEPT` · `NEEDS_EVIDENCE` · `ESCALATE`

> **We didn't build an AI that simply writes chargeback rebuttals. We built the decision layer that determines whether a dispute should be fought, why, and what evidence justifies that decision.**

Built for **Razorpay AI Risk Manager — Track 02**.

---

## 1. The Problem — Where Merchants Bleed Money

Chargeback operations have two forms of leakage:

- **Under-contesting:** potentially recoverable disputes are left undisputed.
- **Over-investigation:** teams spend time investigating cases that are weak or not worth pursuing.

Industry research used for our problem framing reports:

| Signal | Industry evidence |
|---|---:|
| Projected annual chargeback value by 2029 | **$46.1B** |
| Projected chargeback transactions/year by 2029 | **359M** |
| Average cost per chargeback | **~$128** |
| Merchants leaving at least 40% of chargebacks undisputed | **~60%** |
| Merchants calling chargeback management too time-consuming, complex and manual | **55%** |

*Sources: Mastercard / Datos Insights; Riskified + Paladin.*

The existing workflow already handles dispute intake, evidence collection, deadlines and submission.

The harder problem is the **decision layer**:

1. Should we fight this dispute?
2. Why do we believe we can win?
3. What evidence supports or contradicts the claim?
4. What should happen next, and is pursuing the case economically justified?

**That is the gap Chargeback AI targets.**

---

## 2. What We Built

Chargeback AI is a **stateful multi-agent investigation and decision workflow**, not a single LLM prompt.

A dispute is converted into a structured case, evidence is retrieved from verified data sources, applicable policy is retrieved through hybrid RAG, evidence is reasoned over and verified, economics are calculated, and a deterministic decision engine routes the case.

The response is generated **only after** the system decides that the case should be contested.

---

## 3. Architecture

### System Architecture — End-to-End Decision Flow

The complete production flow from dispute intake to the final auditable decision artifact:

![Chargeback AI — System Architecture](docs/architecture.png)

*Figure 1 — End-to-end Chargeback AI architecture. The diagram shows case understanding, evidence and policy retrieval, evidence reasoning, deterministic verification, decisioning, action routing, human review, and the final decision artifact.*

### How to read the architecture

The left side establishes the case and retrieves two forms of truth: structured merchant data and applicable policy. The middle validates and reasons over evidence. The right side performs deterministic decisioning, then routes the case to contest, accept, evidence collection, or human review.

### Architectural principle

**SQL establishes what happened.**  
**RAG establishes what rules apply.**  
**Agents reason over evidence.**  
**Deterministic controls verify grounding, risk and economics.**  
**Humans handle ambiguity and high-risk cases.**

The LLM is therefore **one component of the decision system, not the final authority**.

---

## 4. Decision Flow

### Case understanding → evidence planning

The Case Understanding Agent identifies the claim type, requested resolution and evidence requirements. The Evidence Planner creates a structured plan of allowed sources and fields. The LLM does not freely query the database.

### Evidence + policy

Structured evidence comes from PostgreSQL:

`customers · merchants · orders · transactions · deliveries · disputes`

Policy evidence comes from:

`BM25 → pgvector semantic search → RRF fusion`

One path establishes **what happened**; the other establishes **what rules apply**.

### Evidence reasoning + verification

The Evidence Reasoning Agent classifies evidence as:

`SUPPORTS · CONTRADICTS · MISSING · NON_PROBATIVE`

Every evidence item receives an `Evidence ID` and provenance.

A deterministic verification layer then checks grounding, critical evidence completeness, contradictory findings and policy coverage.

### Decisioning

The Decision Supervisor evaluates:

`case strength · confidence · risk · deadline risk · expected recovery · operational cost`

The final routing is deterministic:

```text
Critical conflict      → ESCALATE
Policy ambiguity       → ESCALATE
Missing critical data  → NEEDS_EVIDENCE
Low confidence         → ESCALATE
Positive net value     → CONTEST
Otherwise              → ACCEPT
```

Only `CONTEST` reaches the Representment Agent. The Critic then validates the generated response and can send it back for revision.

---

## 5. Decision Economics

```text
Recoverable Amount
    = Dispute Amount × Recovery Rate

Expected Recovery
    = Success Likelihood × Recoverable Amount

Net Expected Value
    = Expected Recovery − Operational Cost
```

The objective is not to contest everything. It is to identify cases where **evidence, probability and economics justify the effort**.

---

## 6. Evaluation & Expected Performance

The evaluation framework covers decision quality, evidence quality, workflow reliability, safety and economics.

The final external-LLM evaluation run was constrained by API availability. Therefore, **the figures below are explicitly expected/illustrative targets for a 102-case validation run, not measured benchmark results.**

| Metric | Expected / target |
|---|---:|
| Validation cases | **102** |
| Workflow completion | **≥85%** |
| Evidence grounding | **≥90%** |
| Retrieval relevance | **≥92%** |
| Decision accuracy | **~80–85%** |
| Macro-F1 | **~0.85–0.90** |
| Uncertainty / escalation routing | **≥90%** |


## 7. Dataset

| Dataset stage | Scale | Purpose |
|---|---:|---|
| Original synthetic benchmark | **3,095 merchants** | Full benchmark population |
| Disputes | **10,000** | Controlled dispute cases |
| Relational entity rows | **325,863** | Cross-system evidence graph |
| Frozen demo portfolio | **5 merchants** | Deterministic demo selection |
| Associated disputes | **836** | Full portfolio for selected merchants |
| Live/analyzable demo pool | **390 cases** | Cases exposed in the product |

Core entities:

`Customers · Merchants · Orders · Transactions · Deliveries · Disputes`

The dataset is **synthetic and controlled**. Its class distribution is not intended to represent real-world dispute prevalence.

### Policy knowledge base

- **809 pre-seeded policy chunks**
- `gemini-embedding-001`
- **768-dimensional** pgvector representation
- BM25 lexical retrieval
- semantic retrieval
- RRF fusion

---

## 8. Human-in-the-Loop

Uncertain cases are not forced through automation.

Human review is triggered by:

- conflicting evidence
- missing critical evidence
- policy ambiguity
- low confidence
- high-risk conditions

Reviewers can:

`Approve · Edit · Request Evidence · Escalate`

Human actions and overrides are persisted.

**AI recommendation ≠ final decision** when human review is required.

---

## 9. Observability & Auditability

Every investigation follows:

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

Decision artifacts persist:

- decision
- confidence
- case strength
- expected recovery
- operational cost
- evidence IDs
- rationale
- token usage / cost
- workflow state
- human review / override history

LangSmith provides visibility into agent execution, retrieval, retries, latency, failures and LLM usage.

---

## 10. Impact Model

Chargeback AI targets both revenue leakage and operational workload.

### Revenue leakage

Riskified reports that nearly 60% of merchants leave at least 40% of chargebacks undisputed.

Using Mastercard's projected **$46.1B** global chargeback value:

**$46.1B × 1% = $461M**

A 1% improvement in recovered chargeback value therefore represents an **illustrative $461M global annual opportunity**.

### Operational workload

For illustration:

```text
10,000 cases × 10 minutes saved
= 100,000 minutes
≈ 1,667 analyst-hours
```

*Impact figures are illustrative scenarios, not measured Chargeback AI results.*

---

## 11. Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js · React · TypeScript · Tailwind CSS |
| API | Python · FastAPI · Pydantic |
| Database | PostgreSQL · SQLAlchemy |
| Vector Search | pgvector |
| Retrieval | BM25 + semantic search + RRF |
| Agent Orchestration | LangGraph |
| Agent / LLM Framework | LangChain ecosystem |
| Reasoning | Google Gemini · `gemini-3.5-flash-lite` |
| Embeddings | `gemini-embedding-001` |
| Evaluation | pytest · DeepEval |
| Observability | LangSmith |
| Runtime | Docker · Docker Compose |


## 12. Run Locally

### Requirements

- Docker Desktop
- Google Gemini API key

```bash
cp .env.example .env
docker compose up --build
```

Open:

```text
http://localhost:3000
```

Backend:

```text
http://localhost:8000
```

The Docker setup initializes PostgreSQL and launches the backend and frontend.

---

## 13. Current Scope

### Built

- End-to-end dispute investigation
- Stateful LangGraph workflow
- SQL-backed case reconstruction
- Structured evidence planning and retrieval
- Hybrid policy RAG
- Evidence-ID grounding
- Completeness and conflict validation
- Deterministic confidence/risk routing
- Economic decisioning
- Human-in-the-loop review
- Representment generation
- Critic / revision loop
- LangSmith observability
- Decision audit trail
- Dockerized execution

### Future extensions

- Merchant-specific calibration from historical outcomes
- Larger measured held-out evaluation runs
- Live payment-network representment submission
- Feedback loops from actual dispute outcomes

---

## Final

**Chargeback AI is not an LLM wrapped around a chargeback form.**

```text
Facts        → SQL
Policies     → Hybrid RAG
Evidence     → Structured + grounded
Reasoning    → Specialized agents
Verification → Deterministic
Economics    → Expected recovery
Decision     → Deterministic routing
Uncertainty  → Human review
Response     → Agent + critic
Audit        → Decision artifact + traces
```

> **Fight the disputes worth fighting. Stop wasting effort on the ones that aren't. And never hide uncertainty behind an LLM-generated answer.**

Built for **Razorpay AI Risk Manager — Track 02**.
