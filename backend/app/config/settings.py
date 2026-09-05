"""
Application settings loaded from environment variables.
No secrets are hardcoded here.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_env: str = "development"
    app_name: str = "Chargeback Intelligence"
    app_version: str = "0.1.0"

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/chargeback"

    # LLM Gateway
    llm_provider: str = ""
    llm_api_key: str = ""
    llm_model: str = "gemini-3.5-flash-lite"

    # LangSmith observability
    langchain_tracing_v2: bool = False
    langchain_api_key: str = ""
    langchain_project: str = "chargeback-intelligence"

    # Kaggle API credentials
    kaggle_username: str = ""
    kaggle_key: str = ""

    # Deadline abstraction: dispute_opened_at + N days
    dispute_deadline_days: int = 30

    # Logging
    log_level: str = "INFO"
    log_dir: str = "logs"

    # Phase 5 Pricing Config
    llm_input_price_per_1k: float = 0.0
    llm_output_price_per_1k: float = 0.0

    # Phase 5 Decision Thresholds
    decision_confidence_threshold: float = 0.60
    decision_min_nev: float = 100.0


settings = Settings()
