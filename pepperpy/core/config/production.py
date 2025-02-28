"""Production environment configuration."""

from pathlib import Path

from pepperpy.core.common.config.base import BaseConfig


class ProductionConfig(BaseConfig):
    """Production environment configuration."""

    # Application settings
    debug: bool = False

    # Database settings
    database_url: str = "postgresql+asyncpg://user:pass@localhost:5432/pepperpy"

    # Redis settings
    redis_url: str | None = "redis://localhost:6379/0"

    # Logging settings
    log_level: str = "INFO"
    log_format: str = "json"

    # Path settings
    base_dir: Path = Path("/opt/pepperpy")

    # Feature flags
    enable_telemetry: bool = True
    enable_cache: bool = True

    # Production settings
    reload: bool = False
    cors_origins: list[str] = []  # Configure in environment
    api_docs: bool = False  # Disable API docs in production
