"""
Sentinel backend configuration.

Loads all settings from environment variables using Pydantic BaseSettings.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # --- Database ---
    DATABASE_URL: str = "postgresql+asyncpg://sentinel:sentinel@postgres:5432/sentinel"

    # --- Redis ---
    REDIS_URL: str = "redis://redis:6379/0"

    # --- JWT Auth ---
    JWT_SECRET_KEY: str = "change-me-to-a-random-secret-at-least-32-chars"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    JWT_ALGORITHM: str = "HS256"

    # --- LLM Providers ---
    GROQ_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    LLM_PRIMARY_PROVIDER: str = "groq"
    LLM_TIMEOUT_SECONDS: int = 10

    # --- Anomaly Detection ---
    ANOMALY_DETECTOR: str = "zscore"  # zscore or isolation_forest
    ANOMALY_ZSCORE_WINDOW: int = 30
    ANOMALY_ZSCORE_THRESHOLD: float = 3.0

    # --- Correlation ---
    CORRELATION_WINDOW_SECONDS: int = 60

    # --- General ---
    ENVIRONMENT: str = "development"

    # --- Ingestion ---
    INGESTION_BATCH_SIZE: int = 10
    INGESTION_FLUSH_INTERVAL_SECONDS: float = 1.0

    # --- Services config path ---
    SERVICES_YAML_PATH: str = "/app/services.yaml"

    model_config = {"env_file": ".env", "case_sensitive": True}


# Singleton settings instance
settings = Settings()
