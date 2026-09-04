# Phase 4: Evidence Verification
**Status**: VERIFIED & LOCKED
**Date**: August 2026

## Executive Summary
Phase 4 implements the **Evidence Verification** engine. It establishes a robust, deterministic processing layer that ingests the raw evidence from Phase 3 (`EvidenceBundle`), reasons over it with an LLM, rigorously validates the semantic grounding against the exact retrieved IDs, detects conflicts, asserts completeness, and generates a unified, strict `EvidenceAssessment`.

Critically, Phase 4 maintains a strict **separation of intelligence and policy logic**. The LLM is restricted exclusively to evidence classification. It is completely forbidden from making final chargeback decisions (such as CONTEST, ACCEPT, or ESCALATE). That responsibility belongs entirely to Phase 5.

---

## 1. Core Architecture & Schemas

The application backend exposes the Phase 4 logic via the `EvidenceVerificationService`, managed by a highly controlled `LangGraph` pipeline.

- **Pydantic Schemas (`app/evidence/models/evidence_assessment.py`)**: 
  We define strict Pydantic models for the assessment: `EvidenceAssessment`, `EvidenceFinding`, and `EvidenceConflict`.
- **Strict Data Contracts**:
  - The final assessment separates evidence deterministically into `supporting_evidence`, `contradicting_evidence`, and `non_probative_evidence` to prevent duplication.
  - The assessment holds an explicit `completeness` status (`"complete"`, `"partial"`, or `"insufficient"`).
  - The assessment holds a continuous bounded `confidence` score `[0.0, 1.0]`.

## 2. The Verification Pipeline (LangGraph)

We implemented an agentic orchestration system in `backend/app/evidence/services/evidence_verification_service.py` using `LangGraph` to ensure stability, retries, and strict data flow. **(Phase 5 Upgrade)**: The verification service and reasoning agents now accumulate `TokenUsage` metrics across all attempts, returning `tuple[EvidenceAssessment, TokenUsage]` for cumulative cost accounting.

The execution path operates through deterministic nodes:
1. **Reasoning Node**: Calls the LLM to extract semantic claims and classify them (supports/contradicts).
2. **Validation Node**: Employs the `GroundingValidator` to definitively prove that the LLM did not hallucinate. It asserts that every `evidence_id` and `policy_basis` outputted by the LLM exactly matches the IDs present in the `EvidenceBundle`.
3. **Completeness Node**: Evaluates exactly what evidence is critically missing to map out structural blindspots.
4. **Conflict Node**: Evaluates the structured evidence data to find logical domain conflicts (e.g., cancelled but delivered).
5. **Confidence Node**: Dynamically and deterministically calculates the overall reasoning confidence based on LLM certainty, completeness penalties, conflict penalties, and grounding failure penalties.
6. **Build Node**: Aggregates all deterministic features and risk flags into the final `EvidenceAssessment`.

## 3. Grounding, Provenance & Validation

One of the most complex achievements in Phase 4 is ensuring that the LLM's conclusions are undeniably rooted in the actual retrieved artifacts.

- **Policy Provenance Constraint**: `policy_basis` must contain the `EvidenceItem.evidence_id` (the dynamic UUID assigned by Phase 3 during retrieval), NOT the underlying `document_id`. This prevents namespace ambiguity and guarantees that the system knows precisely *which retrieved chunk* influenced the reasoning.
- **Retry Mechanism**: If the `GroundingValidator` detects a hallucinated ID, it feeds the `validation_errors` back into the graph, which executes a bounded retry (max 2 attempts). 
- **Grounding Failure Penalty**: If the agent continuously fails grounding, it is aborted, a `GROUNDING_FAILURE` risk flag is appended to the assessment, and a fixed `-0.30` confidence penalty is applied.

## 4. Deterministic Responsibilities

Phase 4 moves critical logic away from the LLM to pure Python functions:
- **`completeness.py`**: Reads `missing_evidence` fields from the Phase 3 schema to flag "insufficient" or "partial" assessments purely based on the presence of critical strings (e.g., "delivery").
- **`conflict_detector.py`**: Interrogates the JSON dictionaries of the `structured_evidence` to deterministically cross-check system boundaries.
- **`confidence.py`**: Implements a strict mathematical bounding mechanism `[0.0, 1.0]` applying systematic deductions to a base LLM-supplied reasoning-confidence score.

---

## 5. Verification and Testing

**1. Exact Test/Command Used:**
`pytest backend/tests/ -s` (Full Regression)
`pytest backend/tests/phase4/ -s` (Phase 4 Specific)

**2. Actual Result:**
```text
================= 54 passed, 71 warnings in 259.74s (0:04:19) =================
```

**3. Verified Metrics:**
- **Unit Tests**: 25 Phase 4 unit tests covering every penalty edge case, Pydantic failure, and grounding hallucination.
- **Integration Tests**: Tested via an end-to-end `test_verification_pipeline.py` which retrieves a real row from PG, executes the Vector/BM25 retrievals, executes the LLM reasoning, mocks grounding failures to prove retry behavior, and builds the final artifact.
- **Regression Suite**: 54/54 passing across Phase 1, Phase 2, Phase 3, and Phase 4.

### Phase 4 is definitively locked and verified.

---

## 6. Instructions for Future Phases (Phase 5)
Future agents working on Phase 5 (Dispute Defense & Generation) should note the following:

1. **Information Root**: Your input will be the `EvidenceAssessment` generated by `EvidenceVerificationService.verify_evidence()`. You must use this artifact to construct the final argument. 
2. **Phase 5 Role**: You are explicitly responsible for the final business logic decision (`CONTEST`, `ACCEPT`, `ESCALATE`) based on the structured findings and confidence bounded in Phase 4.
3. **No Retries in Phase 5**: Do not re-verify the evidence or attempt to fetch missing evidence. Accept the `EvidenceAssessment` as the absolute truth.
4. **Tool Access**: Phase 5 will consume the outputs from Phase 4 and finalize the chargeback payload formatted for the Payment Gateway.

**PHASE 4 COMPLETE AND LOCKED. WAITING FOR EXPLICIT USER APPROVAL TO BEGIN PHASE 5.**
