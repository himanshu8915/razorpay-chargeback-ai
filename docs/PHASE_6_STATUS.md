# Phase 6: Automated Representment (STATUS: FROZEN)

## 1. Objective
Phase 6 handles the automated drafting of representment packages for disputes where Phase 5 recommended a `CONTEST` action. The goal is to select the strongest evidence, map it to specific policy requirements (MVO), draft a compelling representment letter, and validate the output before yielding to human review or automated submission.

## 2. Architecture & Components
Phase 6 is orchestrated via a LangGraph state machine (`app.agents.representment.supervisor.py`).

### Nodes:
1. **Entry Validation**: Strictly gates execution. If the `DecisionArtifact` action is NOT `CONTEST`, the graph immediately raises a ValueError.
2. **Evidence Selection**: Analyzes the evidence bundle and the prior Phase 4 evidence assessment to curate the optimal subset of evidence documents. It maps these documents to specific card network policy requirements.
3. **Representation Drafting**: Instructs the LLM to write a formal, professional representment letter defending the merchant, referencing the specific selected evidence.
4. **Validation**: An automated validation service (`ValidationService`) inspects the generated draft against constraints (e.g., tone, required fields, hallucination checks). 
   - **PASS**: Yields to `human_review`.
   - **FAIL**: Routes back to `representation` for a retry (maximum 2 retries). If it persistently fails, it routes to `human_review` with a `FAILED_VALIDATION` flag.

## 3. Data Boundary & Telemetry
- **Token Aggregation**: Phase 6 actively tracks LLM token consumption. The token usage from evidence selection and drafting is accumulated.
- **Integration with Phase 5**: Upon successful execution, the Phase 6 orchestration script dynamically invokes `DecisionService.append_token_usage()`. This extracts the existing Phase 5 `DecisionArtifact`, appends the new Phase 6 tokens, dynamically re-prices the operational cost using system settings, and recalculates the `Net Expected Value` in the database.

## 4. Current State
- **Status**: FROZEN.
- **Constraints**: 
  - Phase 6 requires a valid `CONTEST` recommendation from Phase 5 to trigger.
  - The telemetry correctly bubbles up and persists in the final artifact.
  - The outputs are prepared to be consumed by the Merchant Operations Console (Phase 8).
