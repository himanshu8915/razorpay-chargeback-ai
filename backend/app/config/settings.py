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

    # LangSmith observability
    langsmith_tracing: bool = False
    langsmith_api_key: str = ""
    langsmith_project: str = "chargeback-intelligence"

    # Kaggle API credentials
    kaggle_username: str = ""
    kaggle_key: str = ""

    # Deadline abstraction: dispute_opened_at + N days
    dispute_deadline_days: int = 30

    # Logging
    log_level: str = "INFO"
    log_dir: str = "logs"


settings = Settings()
