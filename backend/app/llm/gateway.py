"""
LLM Gateway factory.
Selects the concrete provider from settings.llm_provider and uses LiteLLM
for multi-provider routing and fallback support.
"""

from app.config.settings import settings
from app.core.exceptions import ConfigurationError
import os

def get_llm_gateway():
    """
    Return the configured LLM gateway instance (a LangChain Chat model using LiteLLM).
    Raises ConfigurationError if LLM_PROVIDER is not supported or missing keys.
    """
    provider = settings.llm_provider.lower()
    
    if provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI
        if not settings.llm_api_key:
            raise ConfigurationError("LLM_API_KEY is missing for Google provider.")
            
        # Configure tracing explicitly using LangSmith variables
        if settings.langchain_tracing_v2:
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            if settings.langchain_api_key:
                os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
            if settings.langchain_project:
                os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project

        model_name = getattr(settings, 'llm_model', 'gemma-4-31b-it')
        
        return ChatGoogleGenerativeAI(
            google_api_key=settings.llm_api_key,
            model=model_name,
            temperature=0.0  # Deterministic output for planners
        )
        
    elif provider == "groq":
        from langchain_groq import ChatGroq
        if not settings.llm_api_key:
            raise ConfigurationError("LLM_API_KEY is missing for Groq provider.")
        
        # Configure tracing explicitly using LangSmith variables
        if settings.langchain_tracing_v2:
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            if settings.langchain_api_key:
                os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
            if settings.langchain_project:
                os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project

        model_name = getattr(settings, 'llm_model', 'qwen-2.5-32b-it')

        return ChatGroq(
            api_key=settings.llm_api_key,
            model_name=model_name,
            temperature=0.0  # Deterministic output for planners
        )
    else:
        raise ConfigurationError(
            f"LLM provider '{provider}' is not yet implemented or unsupported in Phase 3."
        )
