"""Configuration models for Pepperpy.

This module defines the configuration models used by the framework, providing
type-safe configuration with validation.
"""

from pathlib import Path

from pydantic import BaseModel, Field, validator

from pepperpy.core.errors import ConfigurationError
from pepperpy.core.utils import validate_path


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = Field(default="INFO")
    format: str = Field(default="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    file: Path | None = Field(default=None)

    @validator("level")
    def validate_level(cls, v: str) -> str:
        """Validate log level."""
        if v not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ConfigurationError(f"Invalid log level: {v}")
        return v

    @validator("file")
    def validate_file(cls, v: Path | None) -> Path | None:
        """Validate log file path."""
        if v:
            validate_path(v.parent, must_exist=True)
        return v


class MonitoringConfig(BaseModel):
    """Monitoring configuration."""

    enabled: bool = Field(default=True)
    metrics_enabled: bool = Field(default=True)
    tracing_enabled: bool = Field(default=True)
    batch_size: int = Field(default=100, gt=0)
    flush_interval: float = Field(default=60.0, gt=0)


class SecurityConfig(BaseModel):
    """Security configuration."""

    api_key: str | None = Field(default=None)
    api_key_header: str = Field(default="X-API-Key")
    ssl_verify: bool = Field(default=True)
    ssl_cert: Path | None = Field(default=None)
    ssl_key: Path | None = Field(default=None)

    @validator("ssl_cert", "ssl_key")
    def validate_ssl_files(cls, v: Path | None, values: dict) -> Path | None:
        """Validate SSL files."""
        if v:
            validate_path(v, must_exist=True)
            if "ssl_cert" in values and "ssl_key" in values:
                cert = values["ssl_cert"]
                key = values["ssl_key"]
                if bool(cert) != bool(key):
                    raise ConfigurationError(
                        "Both SSL certificate and key must be provided together"
                    )
        return v


class ResourceConfig(BaseModel):
    """Resource configuration."""

    base_path: Path = Field(default_factory=lambda: Path.cwd() / "resources")
    cache_enabled: bool = Field(default=True)
    cache_size: int = Field(default=1000, ge=0)
    cache_ttl: float = Field(default=3600.0, gt=0)

    @validator("base_path")
    def validate_base_path(cls, v: Path) -> Path:
        """Validate base path."""
        validate_path(v, must_exist=True)
        return v


class ProviderConfig(BaseModel):
    """Provider configuration."""

    timeout: float = Field(default=30.0, gt=0)
    max_retries: int = Field(default=3, ge=0)
    retry_delay: float = Field(default=1.0, gt=0)
    retry_backoff: float = Field(default=2.0, gt=1)


class Config(BaseModel):
    """Main configuration class."""

    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    resources: ResourceConfig = Field(default_factory=ResourceConfig)
    providers: ProviderConfig = Field(default_factory=ProviderConfig)
