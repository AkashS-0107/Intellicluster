"""
Application configuration management using Pydantic Settings.
Loads values from environment variables or .env file with type validation.
"""

from typing import Any, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration settings for IntelliCluster."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    APP_NAME: str = "IntelliCluster Backend"
    APP_ENV: str = "development"
    DEBUG: bool = True

    # Persistence
    DATABASE_URL: str = "sqlite:///./intellicluster.db"
    DB_ECHO: bool = False

    # Node Liveness & Heartbeat (seconds before node is flagged stale/unreachable)
    NODE_HEARTBEAT_TIMEOUT_SECONDS: int = Field(
        default=60,
        description="Threshold in seconds after which a silent node is marked UNREACHABLE",
    )

    # Workload Orchestration Strategy (active production strategy)
    SCHEDULER_STRATEGY: str = "heuristic"

    # ML Artifact Registry path
    ML_MODEL_REGISTRY_PATH: str = "./ml_models"

    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "text"  # "text" or "json"

    # CORS Configuration
    CORS_ORIGINS: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://127.0.0.1:3000"],
        description="Allowed CORS origin URLs for frontend cross-origin requests",
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            v_stripped = v.strip()
            if v_stripped.startswith("[") and v_stripped.endswith("]"):
                import json
                try:
                    parsed = json.loads(v_stripped)
                    if isinstance(parsed, list):
                        return [str(orig).strip() for orig in parsed if str(orig).strip()]
                except Exception:
                    pass
            return [orig.strip() for orig in v_stripped.split(",") if orig.strip()]
        elif isinstance(v, list):
            return [str(orig).strip() for orig in v if str(orig).strip()]
        return ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Cloud settings (optional)
    AWS_REGION: Optional[str] = None
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None


# Global singleton instance
settings = Settings()
