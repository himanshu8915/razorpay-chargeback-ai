"""
Application-level exception hierarchy.
All custom exceptions inherit from ChargebackBaseError.
"""


class ChargebackBaseError(Exception):
    """Base exception for all application errors."""
    pass


class ConfigurationError(ChargebackBaseError):
    """Raised when required configuration is missing or invalid."""
    pass


class DatabaseError(ChargebackBaseError):
    """Raised when a database operation fails."""
    pass


class DatabaseNotReadyError(DatabaseError):
    """Raised when the database is not yet available."""
    pass


class RAGNotReadyError(ChargebackBaseError):
    """Raised when policy RAG vector index is not yet available."""
    pass


class DisputeNotFoundError(ChargebackBaseError):
    """Raised when a requested dispute does not exist."""
    def __init__(self, dispute_id: str):
        self.dispute_id = dispute_id
        super().__init__(f"Dispute not found: {dispute_id}")


class EvidenceError(ChargebackBaseError):
    """Raised when evidence extraction or verification fails."""
    pass


class ValidationError(ChargebackBaseError):
    """Raised when deterministic validation of a representment fails."""
    pass


class AgentError(ChargebackBaseError):
    """Raised when an agent encounters an unrecoverable error."""
    pass
