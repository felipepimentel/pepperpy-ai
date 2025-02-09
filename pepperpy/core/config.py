"""Configuration system for the Pepperpy framework.

This module provides a centralized configuration system with support for:
- Environment variable overrides
- File-based configuration
- Validation and type safety
- Configuration versioning
- Lifecycle hooks
"""

import os
import time
from collections.abc import Callable
from enum import Enum
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field

from .errors import ConfigurationError


class LogLevel(str, Enum):
    """Log levels supported by the system."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ProviderConfig(BaseModel):
    """Configuration for a provider."""

    model_config = ConfigDict(extra="allow")

    api_key: str | None = Field(default=None, description="API key for the provider")
    base_url: str | None = Field(default=None, description="Base URL for API calls")
    timeout: float = Field(default=30.0, description="Timeout for API calls in seconds")
    max_retries: int = Field(default=3, description="Maximum number of retries")
    retry_delay: float = Field(
        default=1.0, description="Delay between retries in seconds"
    )


class PepperpyConfig(BaseModel):
    """Main configuration for the Pepperpy system."""

    model_config = ConfigDict(extra="allow")

    # Core settings
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: LogLevel = Field(default=LogLevel.INFO, description="Logging level")
    enable_logging: bool = Field(default=True, description="Enable logging")
    log_file: str | None = Field(default=None, description="Log file path")

    # Performance settings
    max_requests_per_minute: int = Field(
        default=60, description="Maximum requests per minute"
    )
    cache_ttl: int = Field(default=3600, description="Cache TTL in seconds")
    max_cache_size: int = Field(default=1000, description="Maximum cache size")

    # Provider configurations
    provider_configs: dict[str, ProviderConfig] = Field(
        default_factory=dict, description="Provider-specific configurations"
    )

    # Security settings
    enable_rate_limiting: bool = Field(default=True, description="Enable rate limiting")
    enable_auth: bool = Field(default=True, description="Enable authentication")
    auth_token: str | None = Field(default=None, description="Authentication token")

    # Feature flags
    enable_telemetry: bool = Field(default=True, description="Enable telemetry")
    enable_metrics: bool = Field(default=True, description="Enable metrics collection")
    enable_tracing: bool = Field(default=True, description="Enable distributed tracing")

    # Lifecycle hooks
    on_load: list[Callable[["PepperpyConfig"], None]] = Field(
        default_factory=list, description="Hooks called when config is loaded"
    )
    on_save: list[Callable[["PepperpyConfig"], None]] = Field(
        default_factory=list, description="Hooks called when config is saved"
    )
    on_update: list[Callable[["PepperpyConfig"], None]] = Field(
        default_factory=list, description="Hooks called when config is updated"
    )

    def add_hook(self, event: str, hook: Callable[["PepperpyConfig"], None]) -> None:
        """Add a lifecycle hook.

        Args:
            event: Event to hook into (load, save, update)
            hook: Hook function to call

        Raises:
            ValueError: If event is invalid
        """
        if event == "load":
            self.on_load.append(hook)
        elif event == "save":
            self.on_save.append(hook)
        elif event == "update":
            self.on_update.append(hook)
        else:
            raise ValueError(f"Invalid hook event: {event}")

    def remove_hook(self, event: str, hook: Callable[["PepperpyConfig"], None]) -> None:
        """Remove a lifecycle hook.

        Args:
            event: Event to remove hook from (load, save, update)
            hook: Hook function to remove

        Raises:
            ValueError: If event is invalid
        """
        if event == "load":
            self.on_load.remove(hook)
        elif event == "save":
            self.on_save.remove(hook)
        elif event == "update":
            self.on_update.remove(hook)
        else:
            raise ValueError(f"Invalid hook event: {event}")


class AutoConfig:
    """Automatic configuration loader.

    This class provides methods for automatically loading configuration from
    various sources, including environment variables and configuration files.
    """

    @classmethod
    def from_env(cls, prefix: str = "PEPPERPY_") -> PepperpyConfig:
        """Load configuration from environment variables.

        Args:
            prefix: Environment variable prefix (default: PEPPERPY_)

        Returns:
            Loaded configuration

        Raises:
            ConfigurationError: If required configuration is missing
        """
        config_dict: dict[str, Any] = {}

        # Load provider configs
        provider_configs: dict[str, dict[str, Any]] = {}
        for key, value in os.environ.items():
            if not key.startswith(f"{prefix}PROVIDER_"):
                continue
            parts = key[len(f"{prefix}PROVIDER_") :].split("_", 1)
            if len(parts) != 2:
                continue
            provider, setting = parts
            provider_configs.setdefault(provider.lower(), {})
            provider_configs[provider.lower()][setting.lower()] = value

        if provider_configs:
            config_dict["provider_configs"] = {
                name: ProviderConfig(**cfg) for name, cfg in provider_configs.items()
            }

        # Load other settings
        for key, value in os.environ.items():
            if not key.startswith(prefix):
                continue
            config_key = key[len(prefix) :].lower()
            if config_key.startswith("provider_"):
                continue
            config_dict[config_key] = value

        try:
            return PepperpyConfig(**config_dict)
        except Exception as e:
            raise ConfigurationError(f"Failed to load config from env: {e}") from e

    @classmethod
    def from_file(cls, path: Path) -> PepperpyConfig:
        """Load configuration from file.

        Args:
            path: Path to configuration file

        Returns:
            Loaded configuration

        Raises:
            ConfigurationError: If file cannot be loaded
        """
        try:
            with open(path) as f:
                config_dict = yaml.safe_load(f) or {}
            return PepperpyConfig(**config_dict)
        except Exception as e:
            raise ConfigurationError(f"Failed to load config file: {e}") from e


class ConfigManager:
    """Manages configuration lifecycle and updates."""

    def __init__(self) -> None:
        """Initialize the config manager."""
        self._config: PepperpyConfig | None = None
        self._last_load: float = 0

    @property
    def config(self) -> PepperpyConfig:
        """Get the current configuration.

        Returns:
            Current configuration

        Raises:
            ConfigurationError: If configuration is not loaded
        """
        if self._config is None:
            raise ConfigurationError("Configuration not loaded")
        return self._config

    def load(self, path: Path | None = None) -> PepperpyConfig:
        """Load configuration from file and environment.

        Args:
            path: Optional path to configuration file

        Returns:
            Loaded configuration

        Raises:
            ConfigurationError: If configuration is invalid
        """
        config_dict = self._load_from_sources(path)

        try:
            config = PepperpyConfig(**config_dict)
        except Exception as e:
            raise ConfigurationError(f"Invalid configuration: {e}") from e

        # Run load hooks
        for hook in config.on_load:
            try:
                hook(config)
            except Exception as e:
                raise ConfigurationError(f"Load hook failed: {e}") from e

        self._config = config
        self._last_load = time.time()
        return config

    def save(self, path: Path) -> None:
        """Save configuration to file.

        Args:
            path: Path to save configuration to

        Raises:
            ConfigurationError: If saving fails
        """
        if self._config is None:
            raise ConfigurationError("No configuration to save")

        # Run save hooks
        for hook in self._config.on_save:
            try:
                hook(self._config)
            except Exception as e:
                raise ConfigurationError(f"Save hook failed: {e}") from e

        try:
            config_dict = self._config.model_dump()
            with open(path, "w") as f:
                yaml.safe_dump(config_dict, f)
        except Exception as e:
            raise ConfigurationError(f"Failed to save config: {e}") from e

    def update(self, updates: dict[str, Any]) -> None:
        """Update configuration with new values.

        Args:
            updates: Configuration updates

        Raises:
            ConfigurationError: If update is invalid
        """
        if self._config is None:
            raise ConfigurationError("No configuration to update")

        try:
            # Create new config with updates
            config_dict = self._config.model_dump()
            config_dict.update(updates)
            new_config = PepperpyConfig(**config_dict)

            # Run update hooks
            for hook in new_config.on_update:
                hook(new_config)

            self._config = new_config
        except Exception as e:
            raise ConfigurationError(f"Failed to update config: {e}") from e

    def _load_from_sources(self, path: Path | None = None) -> dict[str, Any]:
        """Load configuration from all sources.

        Args:
            path: Optional path to configuration file

        Returns:
            Loaded configuration dictionary

        Raises:
            ConfigurationError: If configuration loading fails
        """
        config_dict: dict[str, Any] = {}

        # Load from file if provided
        if path is not None:
            try:
                with open(path) as f:
                    config_dict = yaml.safe_load(f) or {}
            except Exception as e:
                raise ConfigurationError(f"Failed to load config file: {e}") from e

        # Override with environment variables
        env_prefix = "PEPPERPY_"
        for key, value in os.environ.items():
            if key.startswith(env_prefix):
                config_key = key[len(env_prefix) :].lower()
                # Convert string values to appropriate types
                if isinstance(value, str):
                    if value.lower() in ("true", "false"):
                        config_dict[config_key] = value.lower() == "true"
                    elif value.isdigit():
                        config_dict[config_key] = int(value)
                    else:
                        config_dict[config_key] = value

        # Convert types
        if "enable_logging" in config_dict:
            config_dict["enable_logging"] = bool(config_dict["enable_logging"])
        if "max_requests_per_minute" in config_dict:
            config_dict["max_requests_per_minute"] = int(
                config_dict["max_requests_per_minute"]
            )

        return config_dict


# Global configuration manager instance
config_manager = ConfigManager()


def load_config(path: Path | None = None) -> PepperpyConfig:
    """Load configuration from file and environment.

    This is a convenience function that uses the global config manager.

    Args:
        path: Optional path to configuration file

    Returns:
        Loaded configuration

    Raises:
        ConfigurationError: If configuration is invalid
    """
    return config_manager.load(path)


def save_config(config: PepperpyConfig, path: Path) -> None:
    """Save configuration to file.

    This is a convenience function that uses the global config manager.

    Args:
        config: Configuration to save
        path: Path to save configuration to

    Raises:
        ConfigurationError: If saving fails
    """
    # Update the global manager's config
    config_manager._config = config
    config_manager.save(path)
