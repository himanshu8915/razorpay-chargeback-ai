"""
Core enumerations used across the application.
No business logic — only type definitions.
"""

from enum import Enum


class DecisionAction(str, Enum):
    CONTEST = "contest"
    ACCEPT = "accept"
    HUMAN_REVIEW = "human_review"


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class CaseStatus(str, Enum):
    NEW = "new"
    ANALYZING = "analyzing"
    REVIEW = "review"
    READY = "ready"
    COMPLETED = "completed"


class EvidenceStrength(str, Enum):
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"
    MISSING = "missing"
    CONTRADICTORY = "contradictory"


class InitializationStatus(str, Enum):
    NOT_STARTED = "not_started"
    DATABASE_STARTING = "database_starting"
    DATASET_INITIALIZING = "dataset_initializing"
    STRUCTURED_DATA_READY = "structured_data_ready"
    APPLICATION_READY = "application_ready"


class RAGStatus(str, Enum):
    RAG_INITIALIZATION = "rag_initialization"
    DOCUMENT_LOADING = "document_loading"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    VECTOR_INDEX_READY = "vector_index_ready"


class ProgressStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class DisputeType(str, Enum):
    FRAUD = "fraud"
    DUPLICATE_CHARGE = "duplicate_charge"
    PRODUCT_NOT_RECEIVED = "product_not_received"
    PRODUCT_NOT_AS_DESCRIBED = "product_not_as_described"
    REFUND_NOT_RECEIVED = "refund_not_received"
    PROCESSING_ERROR = "processing_error"
    UNAUTHORIZED_TRANSACTION = "unauthorized_transaction"
    OTHER = "other"


class DisputeStatus(str, Enum):
    OPEN = "open"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    CLOSED = "closed"
