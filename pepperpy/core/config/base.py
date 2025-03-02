"""Base configuration system.

This module provides the core configuration functionality, including:
- Environment variable mapping
- Configuration validation
- Schema management
- Default values
- Configuration versioning
- Schema validation
- Migration support
"""

import os
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, ClassVar, TypeVar

try:
    from pydantic import BaseModel, Field, SecretStr, validator
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError:
    raise ImportError(
        "pydantic is required for configuration management. "
        "Install it with: poetry add pydantic pydantic-settings"
    )

from pepperpy.core.common.observability import ObservabilityManager
from pepperpy.core.metrics import MetricsCollector

T = TypeVar("T", bound="ConfigModel")
ConfigT = TypeVar("ConfigT", bound="BaseConfig")


class ConfigModel(BaseModel):
    """Base model for configuration with environment variable support.

    This class extends BaseModel to add support for loading values from
    environment variables and providing default values.
    """

    version: str = Field(default="1.0.0", description="Configuration version")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )

    class Config:
        """Model configuration."""

        env_prefix = "PEPPERPY_"  # Prefix for environment variables
        case_sensitive = False  # Case sensitivity for field names
        validate_all = True  # Validate default values
        json_schema_extra = {
            "examples": [
                {
                    "version": "1.0.0",
                    "created_at": "2024-03-19T00:00:00Z",
                    "updated_at": "2024-03-19T00:00:00Z",
                }
            ]
        }

    @validator("updated_at", pre=True, always=True)
    def set_updated_at(cls, v: Any, values: dict[str, Any]) -> datetime:
        """Set updated_at to current time on every update."""
        return datetime.utcnow()

    @classmethod
    def from_env(cls: type[T], prefix: str | None = None) -> T:
        """Create instance from environment variables.

        Args:
            prefix: Optional prefix for environment variables.
                   If not provided, uses the class's env_prefix.

        Returns:
            Configuration instance populated from environment variables.
        """
        env_prefix = prefix or cls.Config.env_prefix
        env_values = {}

        for field_name, field in cls.model_fields.items():
            env_key = f"{env_prefix}{field_name}".upper()
            if env_key in os.environ:
                env_values[field_name] = os.environ[env_key]

        return cls(**env_values)

    def to_schema(self) -> dict[str, Any]:
        """Generate JSON schema for configuration.

        Returns:
            JSON schema as a dictionary.
        """
        return self.model_json_schema()

    def validate_schema(self) -> bool:
        """Validate configuration against its schema.

        Returns:
            True if validation succeeds.

        Raises:
            ValidationError: If validation fails.
        """
        self.model_validate(self.dict())
        return True

    def migrate(self, target_version: str) -> None:
        """Migrate configuration to target version.

        Args:
            target_version: Version to migrate to.

        Raises:
            ValueError: If migration path is not available.
        """
        if target_version == self.version:
            return

        # Get migration path
        migration_path = self._get_migration_path(target_version)
        if not migration_path:
            raise ValueError(
                f"No migration path from {self.version} to {target_version}"
            )

        # Apply migrations
        for version in migration_path:
            self._apply_migration(version)

        self.version = target_version
        self.updated_at = datetime.utcnow()

    def _get_migration_path(self, target_version: str) -> list[str]:
        """Get migration path to target version.

        Args:
            target_version: Version to migrate to.

        Returns:
            List of versions to apply in sequence.
        """
        # TODO: Implement migration path discovery
        return []

    def _apply_migration(self, version: str) -> None:
        """Apply migration for specific version.

        Args:
            version: Version to migrate to.
        """
        # TODO: Implement migration application
        pass


class ConfigProvider(ABC):
    """Abstract base class for configuration providers.

    Configuration providers are responsible for loading configuration
    values from different sources (files, environment, etc.).
    """

    def __init__(self) -> None:
        """Initialize the provider."""
        self._metrics = MetricsCollector()
        self._observability = ObservabilityManager()

    @abstractmethod
    async def get(self, key: str) -> str | None:
        """Get configuration value.

        Args:
            key: Configuration key

        Returns:
            Configuration value or None if not found
        """
        pass

    @abstractmethod
    async def set(self, key: str, value: str) -> None:
        """Set configuration value.

        Args:
            key: Configuration key
            value: Configuration value
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete configuration value.

        Args:
            key: Configuration key
        """
        pass

    @abstractmethod
    async def list(self, prefix: str = "") -> list[str]:
        """List configuration keys.

        Args:
            prefix: Optional key prefix to filter by

        Returns:
            List of configuration keys
        """
        pass


class ConfigManager:
    """Manager for configuration values.

    This class provides a centralized way to manage configuration values
    from multiple providers.
    """

    def __init__(self) -> None:
        """Initialize the manager."""
        self._providers: list[ConfigProvider] = []
        self._metrics = MetricsCollector()
        self._observability = ObservabilityManager()

    def add_provider(self, provider: ConfigProvider) -> None:
        """Add configuration provider.

        Args:
            provider: Provider to add
        """
        self._providers.append(provider)

    async def get(self, key: str) -> str | None:
        """Get configuration value.

        Args:
            key: Configuration key

        Returns:
            Configuration value or None if not found
        """
        start_time = datetime.now()
        value = None

        try:
            # Try each provider in order
            for provider in self._providers:
                value = await provider.get(key)
                if value is not None:
                    break

            # Record metrics
            duration = (datetime.now() - start_time).total_seconds()
            self._metrics.histogram(
                "config_get_duration",
                duration,
                labels={"key": key},
            )
            self._metrics.counter(
                "config_get_total",
                1,
                labels={
                    "key": key,
                    "found": str(value is not None).lower(),
                },
            )

            return value

        except Exception as e:
            # Record error
            self._observability.log_error(
                "config.get",
                f"Failed to get configuration value: {e}",
                exception=e,
                context={"key": key},
            )
            raise

    async def set(self, key: str, value: str) -> None:
        """Set configuration value.

        Args:
            key: Configuration key
            value: Configuration value
        """
        start_time = datetime.now()

        try:
            # Set value in all providers
            for provider in self._providers:
                await provider.set(key, value)

            # Record metrics
            duration = (datetime.now() - start_time).total_seconds()
            self._metrics.histogram(
                "config_set_duration",
                duration,
                labels={"key": key},
            )
            self._metrics.counter(
                "config_set_total",
                1,
                labels={"key": key},
            )

        except Exception as e:
            # Record error
            self._observability.log_error(
                "config.set",
                f"Failed to set configuration value: {e}",
                exception=e,
                context={"key": key},
            )
            raise

    async def delete(self, key: str) -> None:
        """Delete configuration value.

        Args:
            key: Configuration key
        """
        start_time = datetime.now()

        try:
            # Delete from all providers
            for provider in self._providers:
                await provider.delete(key)

            # Record metrics
            duration = (datetime.now() - start_time).total_seconds()
            self._metrics.histogram(
                "config_delete_duration",
                duration,
                labels={"key": key},
            )
            self._metrics.counter(
                "config_delete_total",
                1,
                labels={"key": key},
            )

        except Exception as e:
            # Record error
            self._observability.log_error(
                "config.delete",
                f"Failed to delete configuration value: {e}",
                exception=e,
                context={"key": key},
            )
            raise

    async def list(self, prefix: str = "") -> list[str]:
        """List configuration keys.

        Args:
            prefix: Optional key prefix to filter by

        Returns:
            List of configuration keys
        """
        start_time = datetime.now()
        keys = set()

        try:
            # Get keys from all providers
            for provider in self._providers:
                provider_keys = await provider.list(prefix)
                keys.update(provider_keys)

            # Record metrics
            duration = (datetime.now() - start_time).total_seconds()
            self._metrics.histogram(
                "config_list_duration",
                duration,
                labels={"prefix": prefix},
            )
            self._metrics.gauge(
                "config_keys_total",
                len(keys),
                labels={"prefix": prefix},
            )

            return sorted(keys)

        except Exception as e:
            # Record error
            self._observability.log_error(
                "config.list",
                f"Failed to list configuration keys: {e}",
                exception=e,
                context={"prefix": prefix},
            )
            raise


# Global configuration manager instance
config_manager = ConfigManager()


class BaseConfig(ConfigModel):
    """Base configuration with common settings."""

    # Application settings
    app_name: str = Field(default="PepperPy", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    environment: str = Field(default="development", description="Environment name")

    # Security settings
    secret_key: SecretStr = Field(
        default=SecretStr("change-me-in-production"),
        description="Secret key for cryptographic operations",
    )
    allowed_hosts: list[str] = Field(
        default=["localhost", "127.0.0.1"], description="List of allowed hosts"
    )

    # Database settings
    database_url: str = Field(
        default="sqlite+aiosqlite:///pepperpy.db", description="Database connection URL"
    )

    # Redis settings
    redis_url: str | None = Field(default=None, description="Redis connection URL")

    # Logging settings
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Logging format")

    # Path settings
    base_dir: Path = Field(
        default=Path(__file__).parent.parent.parent.parent,
        description="Base directory path",
    )

    # Feature flags
    enable_telemetry: bool = Field(default=True, description="Enable telemetry")
    enable_cache: bool = Field(default=True, description="Enable caching")

    # API settings
    reload: bool = Field(default=False, description="Enable auto-reload")
    cors_origins: list[str] = Field(default=[], description="CORS allowed origins")
    api_docs: bool = Field(default=True, description="Enable API documentation")

    # Schema version mapping
    SCHEMA_VERSIONS: ClassVar[dict[str, dict[str, Any]]] = {
        "1.0.0": {
            "description": "Initial version",
            "added": ["app_name", "app_version", "debug", "environment"],
            "required": ["app_name", "environment"],
        },
        "1.1.0": {
            "description": "Added security settings",
            "added": ["secret_key", "allowed_hosts"],
            "required": ["secret_key"],
        },
        "1.2.0": {
            "description": "Added database and Redis settings",
            "added": ["database_url", "redis_url"],
            "required": ["database_url"],
        },
    }

    def get_schema_version(self) -> dict[str, Any]:
        """Get schema definition for current version.

        Returns:
            Schema definition as a dictionary.
        """
        return self.SCHEMA_VERSIONS.get(self.version, {})

    def validate_version(self) -> bool:
        """Validate configuration version.

        Returns:
            True if version is valid.

        Raises:
            ValueError: If version is not supported.
        """
        if self.version not in self.SCHEMA_VERSIONS:
            raise ValueError(f"Unsupported configuration version: {self.version}")
        return True

    class Config:
        """Model configuration."""

        env_prefix = "PEPPERPY_"
        case_sensitive = False
        validate_all = True
        json_encoders = {
            Path: str,
            SecretStr: lambda v: v.get_secret_value() if v else None,
        }

    @classmethod
    def load(cls: type[ConfigT], env_file: str | None = None) -> ConfigT:
        """Load configuration from environment and files.

        Args:
            env_file: Optional path to environment file

        Returns:
            ConfigT: Configuration instance
        """
        kwargs = {}
        if env_file:
            kwargs["env_file"] = env_file
        return cls(**kwargs)

    def get_secret(self, key: str) -> str | None:
        """Securely retrieve a secret value.

        Args:
            key: The secret key to retrieve

        Returns:
            Optional[str]: The secret value if found
        """
        value = getattr(self, key, None)
        if isinstance(value, SecretStr):
            return value.get_secret_value()
        return None

    def to_dict(self, exclude_secrets: bool = True) -> dict[str, Any]:
        """Convert configuration to dictionary.

        Args:
            exclude_secrets: Whether to exclude secret values

        Returns:
            Dict[str, Any]: Configuration as dictionary
        """
        data = {}
        for field, value in self:
            if exclude_secrets and isinstance(value, SecretStr):
                continue
            if isinstance(value, SecretStr):
                data[field] = "**********"
            else:
                data[field] = value
        return data


class ConfigurationError(Exception):
    """Raised when there is a configuration error."""

    pass


__all__ = [
    "BaseConfig",
    "ConfigManager",
    "ConfigModel",
    "ConfigProvider",
    "ConfigurationError",
    "config_manager",
]
