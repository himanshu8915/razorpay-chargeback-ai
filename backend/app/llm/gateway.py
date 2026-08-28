"""
LLM Gateway factory.
Selects the concrete provider from settings.LLM_PROVIDER.
Provider implementations live in app/llm/providers/.
Implemented in Phase 5.
"""

from app.config.settings import settings
from app.core.exceptions import ConfigurationError
from app.llm.base import BaseLLMGateway


def get_llm_gateway() -> BaseLLMGateway:
    """
    Return the configured LLM gateway instance.
    Raises ConfigurationError if LLM_PROVIDER is not set or not supported.
    (Phase 5 will implement actual providers.)
    """
    provider = settings.llm_provider
    if not provider:
        raise ConfigurationError(
            "LLM_PROVIDER is not configured. Set it in your .env file."
        )
    raise ConfigurationError(
        f"LLM provider '{provider}' is not yet implemented. "
        "Provider implementations are added in Phase 5."
    )
