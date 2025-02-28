"""Test environment configuration."""

from pathlib import Path

from pepperpy.common.config.base import BaseConfig


class TestConfig(BaseConfig):
    """Test environment configuration."""

    # Application settings
    debug: bool = True

    # Database settings
    database_url: str = "sqlite+aiosqlite:///:memory:"

    # Redis settings
    redis_url: str | None = None  # No Redis in tests by default

    # Logging settings
    log_level: str = "DEBUG"
    log_format: str = "console"

    # Path settings
    base_dir: Path = Path(__file__).parent.parent.parent.parent

    # Feature flags
    enable_telemetry: bool = False
    enable_cache: bool = False

    # Test settings
    reload: bool = False
    cors_origins: list[str] = ["http://localhost:3000"]
    api_docs: bool = True
