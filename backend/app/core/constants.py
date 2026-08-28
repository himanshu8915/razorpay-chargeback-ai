"""
Application-wide constants.
No business logic. Only values that should not be hardcoded elsewhere.
"""

# API prefix
API_V1_PREFIX = "/api/v1"

# Progress event phases (matches initialization state machine)
PHASE_INITIALIZATION = "initialization"
PHASE_EVIDENCE_DISCOVERY = "evidence_discovery"
PHASE_EVIDENCE_VERIFICATION = "evidence_verification"
PHASE_POLICY_RETRIEVAL = "policy_retrieval"
PHASE_CASE_ASSESSMENT = "case_assessment"
PHASE_DECISION = "decision"
PHASE_EXPLANATION = "explanation"
PHASE_REPRESENTMENT = "representment"
PHASE_VALIDATION = "validation"

# Initialization component labels (used in progress events)
COMPONENT_DATABASE = "database"
COMPONENT_DATASET = "dataset"
COMPONENT_RAG = "rag"
COMPONENT_BACKEND = "backend"

# Dispute ID prefix
DISPUTE_ID_PREFIX = "DSP_"
