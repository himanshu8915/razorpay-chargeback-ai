"""
LLM Gateway base interface.
Concrete providers are implemented in Phase 5.
The gateway abstracts provider selection so agents are not tightly coupled
to any single LLM provider.
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseLLMGateway(ABC):
    """Abstract base for all LLM provider implementations."""

    @abstractmethod
    async def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate a text completion."""
        ...

    @abstractmethod
    async def generate_structured(
        self, prompt: str, schema: type, **kwargs: Any
    ) -> Any:
        """Generate a structured (Pydantic model) response."""
        ...
