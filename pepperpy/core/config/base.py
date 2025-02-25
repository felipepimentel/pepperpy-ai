"""Base configuration system.

This module provides the core configuration functionality, including:
- Environment variable mapping
- Configuration validation
- Schema management
- Default values
"""

import json
import os
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, TypeVar, get_type_hints

from pepperpy.core.metrics import MetricsCollector
from pepperpy.core.models import BaseModel
from pepperpy.core.observability import ObservabilityManager

T = TypeVar("T", bound="ConfigModel")


class ConfigModel(BaseModel):
    """Base model for configuration with environment variable support.

    This class extends BaseModel to add support for loading values from
    environment variables and providing default values.
    """

    class Config:
        """Model configuration."""

        env_prefix = "PEPPERPY_"  # Prefix for environment variables
        case_sensitive = False  # Case sensitivity for field names
        validate_all = True  # Validate default values

    @classmethod
    def from_env(cls: type[T], prefix: str | None = None) -> T:
        """Create instance from environment variables.

        Args:
            prefix: Optional prefix for environment variables
                (overrides Config.env_prefix)

        Returns:
            Configuration instance
        """
        # Get environment variables
        env_prefix = prefix or cls.Config.env_prefix
        env_vars = {
            k.replace(env_prefix, ""): v
            for k, v in os.environ.items()
            if k.startswith(env_prefix)
        }

        # Convert types based on annotations
        values: dict[str, Any] = {}
        for field_name, field_type in get_type_hints(cls).items():
            env_key = field_name.upper()
            if env_key in env_vars:
                # Convert value to correct type
                value = env_vars[env_key]
                if field_type == bool:
                    value = value.lower() in ("true", "1", "yes", "on")
                elif field_type == int:
                    value = int(value)
                elif field_type == float:
                    value = float(value)
                elif field_type == Path:
                    value = Path(value)
                elif field_type == list[str]:
                    value = value.split(",")
                values[field_name] = value

        return cls(**values)

    @classmethod
    def from_file(cls: type[T], path: str | Path) -> T:
        """Create instance from configuration file.

        Args:
            path: Path to configuration file (JSON)

        Returns:
            Configuration instance

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")

        try:
            with path.open() as f:
                data = json.load(f)
            return cls(**data)
        except Exception as e:
            raise ValueError(f"Invalid configuration file: {e}")

    def to_file(self, path: str | Path) -> None:
        """Save configuration to file.

        Args:
            path: Path to save configuration file (JSON)

        Raises:
            OSError: If file cannot be written
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with path.open("w") as f:
                json.dump(
                    self.model_dump(),
                    f,
                    indent=2,
                    default=str,
                )
        except Exception as e:
            raise OSError(f"Failed to save configuration: {e}")


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


__all__ = [
    "ConfigManager",
    "ConfigModel",
    "ConfigProvider",
    "config_manager",
]
