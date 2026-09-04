# Phase 7: Observability & Data Materialization (STATUS: FROZEN)

## 1. Objective
Phase 7 finalized the core backend architecture (Phases 1-6) by completely hardening the LLM telemetry pipeline and securely establishing the data boundary for Phase 8 (Merchant Operations Console).

## 2. Telemetry & Observability Fixes
Phase 7 implemented cross-phase LLM token tracking and dynamic economic calculation to form a pristine data foundation:
1. **LangGraph Reducer**: Implemented an `Annotated` reducer in `DecisionState` to securely accumulate inputs/outputs across all parallel/sequential nodes (Case Strength, Risk, Confidence, Explanation) without destructive overwriting.
2. **Phase 3/4 Propagation**: Wired prior phase token counts directly into `DecisionService.analyze_dispute()`.
3. **Phase 6 Appends**: Authored `DecisionService.append_token_usage()` so if Phase 6 executes, it re-queries the completed `DecisionArtifact`, appends the new Phase 6 tokens, and recalculates the final `EstimatedOperationalCost` and `NetExpectedValue`.
4. **Dynamic Centralized Pricing**: Decoupled cost calculations from magic numbers by mapping `EstimatedOperationalCost` dynamically via `.env` configured token pricing.

## 3. Demo Portfolio Materialization
To support the dashboard without executing 10,000 cases sequentially (and hitting Groq's 8,000 TPM rate limits), Phase 7 materialized a deterministic data boundary:
1. **Deterministic Merchant Scoring**: A python script (`backend/scripts/phase7_demo_materializer.py`) queried the DB (without LLMs) to select exactly 5 top merchants based on:
   - Volume (target ~150-200 cases per merchant)
   - Diversity of `dispute_type`
   - Complete Data (non-null required fields)
2. **Stratified 50/50 Allocation**: Selected cases were bucketed into deterministic strata (`dispute_type` + `amount_bucket`), then split exactly 50/50 (`index % 2`) into two operational pools:
   - **PRECOMPUTED**: Deterministic rows were directly inserted into the `decision_artifacts` table to instantly populate the dashboard on load.
   - **LIVE_DEMO**: Genuine source disputes left utterly untouched, reserved exclusively for real-time one-by-one execution through Phase 3-6 when a user clicks "Run" in Phase 8.
3. **Pristine Schema Maintained**: No artificial tags or flags were injected into the `DecisionArtifactModel` schema.

## 4. Phase 8 Data Contract (`demo_portfolio_manifest.json`)
The source of truth for the entire dashboard is securely outputted to `backend/results/phase7/demo_portfolio_manifest.json`.
It dictates exactly which 5 merchants were selected, and which precise IDs belong to the PRECOMPUTED vs. LIVE_DEMO pools. Phase 8 MUST consume this file to instantiate its UI.

## 5. Reset Protocol (`reset_demo.py`)
Phase 7 provides `backend/scripts/reset_demo.py`. This utility gracefully flushes only `LIVE_DEMO` artifacts from the database, instantly returning the system to its initial unprocessed state for repeated presentations, completely preserving the `PRECOMPUTED` dataset.

## 6. Current State
- **Status**: FROZEN.
- The entire LLM orchestration (Phases 1-6) and the Data Boundary (Phase 7) are locked.
- The next step is Phase 8 frontend implementation.
