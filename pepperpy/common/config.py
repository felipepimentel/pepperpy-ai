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


class MemoryBackend(str, Enum):
    """Supported memory backend types."""

    DICT = "dict"
    REDIS = "redis"
    SQLITE = "sqlite"
    POSTGRES = "postgres"


class ProviderConfig(BaseModel):
    """Configuration for a provider.

    Attributes:
        api_key: API key for the provider
        model: Model to use
        timeout: Operation timeout in seconds
        max_retries: Maximum number of retries
        retry_delay: Delay between retries in seconds
        extra_args: Additional provider-specific arguments
    """

    api_key: str = Field(..., description="API key for the provider")
    model: str = Field(..., description="Model to use")
    timeout: float = Field(default=30.0, gt=0)
    max_retries: int = Field(default=3, ge=0)
    retry_delay: float = Field(default=1.0, ge=0)
    extra_args: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(validate_assignment=True, extra="forbid")


class AgentConfig(BaseModel):
    """Configuration for an agent type.

    Attributes:
        provider: Provider to use for this agent type
        capabilities: List of enabled capabilities
        memory_enabled: Whether to enable memory
        max_tokens: Maximum tokens per request
        temperature: Sampling temperature
        extra_args: Additional agent-specific arguments
    """

    provider: str = Field(..., description="Provider to use")
    capabilities: list[str] = Field(default_factory=list)
    memory_enabled: bool = Field(default=True)
    max_tokens: int = Field(default=2048, gt=0)
    temperature: float = Field(default=0.7, ge=0, le=1)
    extra_args: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(validate_assignment=True, extra="forbid")


class SecurityConfig(BaseModel):
    """Security-related configuration.

    Attributes:
        enable_tool_security: Enable tool security checks
        enable_rate_limiting: Enable rate limiting
        enable_audit_logging: Enable audit logging
        max_requests_per_minute: Maximum requests per minute
        require_api_keys: Require API keys for all providers
        allowed_hosts: List of allowed hosts
    """

    enable_tool_security: bool = Field(default=True)
    enable_rate_limiting: bool = Field(default=True)
    enable_audit_logging: bool = Field(default=True)
    max_requests_per_minute: int = Field(default=60, gt=0)
    require_api_keys: bool = Field(default=True)
    allowed_hosts: list[str] = Field(default_factory=list)

    model_config = ConfigDict(validate_assignment=True, extra="forbid")


class PepperpyConfig(BaseModel):
    """Global configuration for the Pepperpy system.

    This class manages all configuration aspects of the system, including:
    - System paths and locations
    - Provider configurations
    - Agent configurations
    - Security settings
    - Monitoring configuration
    """

    # Version tracking
    version: str = Field(
        default="1.0",
        description="Configuration version",
    )

    # System paths
    workspace_path: Path = Field(
        default_factory=lambda: Path.cwd(),
        description="Root workspace path",
    )
    assets_path: Path | None = Field(
        default=None,
        description="Path for storing assets",
    )
    cache_path: Path | None = Field(
        default=None,
        description="Path for storing cache data",
    )

    # Provider settings
    provider_configs: dict[str, ProviderConfig] = Field(
        default_factory=dict,
        description="Configuration for each provider",
    )
    default_provider: str | None = Field(
        default=None,
        description="Default provider to use",
    )

    # Agent settings
    agent_configs: dict[str, AgentConfig] = Field(
        default_factory=dict,
        description="Configuration for each agent type",
    )

    # Memory settings
    memory_backend: MemoryBackend = Field(
        default=MemoryBackend.DICT,
        description="Memory storage backend to use",
    )
    memory_settings: dict[str, Any] = Field(
        default_factory=dict,
        description="Settings for the memory backend",
    )

    # Monitoring settings
    enable_logging: bool = Field(
        default=True,
        description="Enable system logging",
    )
    enable_metrics: bool = Field(
        default=False,
        description="Enable metrics collection",
    )
    enable_tracing: bool = Field(
        default=False,
        description="Enable distributed tracing",
    )
    log_level: LogLevel = Field(
        default=LogLevel.INFO,
        description="Logging level",
    )

    # Security settings
    security: SecurityConfig = Field(
        default_factory=SecurityConfig,
        description="Security configuration",
    )

    # Timestamps
    created_at: float = Field(
        default_factory=time.time,
        description="Configuration creation timestamp",
    )
    updated_at: float = Field(
        default_factory=time.time,
        description="Configuration update timestamp",
    )

    model_config = ConfigDict(
        validate_assignment=True, extra="forbid", json_encoders={Path: str}
    )

    def get_provider_config(self, provider: str | None = None) -> dict[str, Any]:
        """Get configuration for a specific provider.

        Args:
            provider: Provider name, or None for default provider

        Returns:
            Provider configuration dictionary

        Raises:
            ConfigurationError: If provider not found or no default set
        """
        if not provider:
            provider = self.default_provider
        if not provider:
            raise ConfigurationError("No provider specified and no default set")
        if provider not in self.provider_configs:
            raise ConfigurationError(f"Provider not found: {provider}")
        return self.provider_configs[provider].dict()


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
            setting = key[len(prefix) :].lower()
            if setting == "workspace_path":
                config_dict[setting] = Path(value)
            elif setting == "log_level":
                config_dict[setting] = LogLevel(value.upper())
            elif setting == "memory_backend":
                config_dict[setting] = MemoryBackend(value.lower())
            elif setting in {"enable_logging", "enable_metrics", "enable_tracing"}:
                config_dict[setting] = value.lower() == "true"
            elif setting == "default_provider":
                config_dict[setting] = value.lower()

        return PepperpyConfig(**config_dict)

    @classmethod
    def from_file(cls, path: Path) -> PepperpyConfig:
        """Load configuration from a YAML file.

        Args:
            path: Path to configuration file

        Returns:
            Loaded configuration

        Raises:
            ConfigurationError: If file cannot be loaded or is invalid
        """
        try:
            with open(path) as f:
                config_dict = yaml.safe_load(f)
            return PepperpyConfig(**config_dict)
        except Exception as e:
            raise ConfigurationError(f"Failed to load config from {path}: {e!s}") from e


class ConfigManager:
    """Manages configuration lifecycle and updates."""

    def __init__(self) -> None:
        """Initialize the configuration manager."""
        self._config: PepperpyConfig | None = None
        self._hooks: dict[str, set[Callable[[PepperpyConfig], None]]] = {
            "load": set(),
            "save": set(),
            "update": set(),
        }

    @property
    def config(self) -> PepperpyConfig:
        """Get current configuration.

        Raises:
            ConfigurationError: If configuration is not loaded
        """
        if self._config is None:
            raise ConfigurationError("Configuration not loaded")
        return self._config

    def add_hook(self, event: str, callback: Callable[[PepperpyConfig], None]) -> None:
        """Add a configuration lifecycle hook.

        Args:
            event: Event to hook ("load", "save", "update")
            callback: Function to call on event
        """
        if event not in self._hooks:
            raise ValueError(f"Invalid event: {event}")
        self._hooks[event].add(callback)

    def remove_hook(
        self, event: str, callback: Callable[[PepperpyConfig], None]
    ) -> None:
        """Remove a configuration lifecycle hook.

        Args:
            event: Event to unhook
            callback: Function to remove
        """
        if event not in self._hooks:
            raise ValueError(f"Invalid event: {event}")
        self._hooks[event].discard(callback)

    def load(self, path: Path | None = None) -> PepperpyConfig:
        """Load configuration from file and environment.

        Args:
            path: Optional path to configuration file

        Returns:
            Loaded configuration

        Raises:
            ConfigurationError: If configuration is invalid
        """
        try:
            config_dict = self._load_from_sources(path)
            self._config = PepperpyConfig(**config_dict)

            # Trigger hooks
            for hook in self._hooks["load"]:
                try:
                    hook(self._config)
                except Exception as e:
                    # Log but don't fail
                    print(f"Hook failed: {e}")

            return self._config

        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration: {e}") from e

    def save(self, path: Path) -> None:
        """Save configuration to file.

        Args:
            path: Path to save configuration to

        Raises:
            ConfigurationError: If saving fails
        """
        if self._config is None:
            raise ConfigurationError("No configuration to save")

        try:
            # Update timestamp
            self._config.updated_at = time.time()

            # Trigger hooks
            for hook in self._hooks["save"]:
                try:
                    hook(self._config)
                except Exception as e:
                    # Log but don't fail
                    print(f"Hook failed: {e}")

            # Convert to dictionary
            config_dict = self._config.dict()

            # Convert paths to strings
            for key in ["workspace_path", "assets_path", "cache_path"]:
                if config_dict[key] is not None:
                    config_dict[key] = str(config_dict[key])

            # Save to file
            with open(path, "w") as f:
                yaml.safe_dump(config_dict, f, default_flow_style=False)

        except Exception as e:
            raise ConfigurationError(f"Failed to save configuration: {e}") from e

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
