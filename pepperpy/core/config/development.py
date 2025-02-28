"""Development environment configuration."""

from pathlib import Path

from pepperpy.core.common.config.base import BaseConfig


class DevelopmentConfig(BaseConfig):
    """Development environment configuration."""

    # Application settings
    debug: bool = True

    # Database settings
    database_url: str = "sqlite+aiosqlite:///dev.db"

    # Redis settings
    redis_url: str | None = "redis://localhost:6379/0"

    # Logging settings
    log_level: str = "DEBUG"
    log_format: str = "console"

    # Path settings
    base_dir: Path = Path(__file__).parent.parent.parent.parent

    # Feature flags
    enable_telemetry: bool = False
    enable_cache: bool = True

    # Development settings
    reload: bool = True
    cors_origins: list[str] = ["http://localhost:3000"]
    api_docs: bool = True
