"""Configuration management for Pepperpy.

This module provides a unified configuration system with support for:
- Multiple configuration sources (env vars, files, CLI)
- Type-safe configuration with validation
- Dynamic configuration updates
- Configuration versioning
- Lifecycle hooks
"""

from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from .base import Configuration, ConfigurationError
from .loader import ProcessorLoader, ProviderLoader, load_class
from .manager import ConfigurationManager
from .models import (
    Config,
    LoggingConfig,
    MonitoringConfig,
    ProviderConfig,
    ResourceConfig,
    SecurityConfig,
)
from .unified import (
    ConfigHook,
    ConfigSource,
    ConfigState,
    UnifiedConfig,
)


class PepperpyConfig(BaseModel):
    """Configuration for the Pepperpy framework.

    This model defines all configuration options available in the framework.
    It is used by the UnifiedConfig manager to provide type-safe configuration
    with validation.
    """

    # Core settings
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    # Provider settings
    provider: str = Field(default="openai", description="AI provider to use")
    api_key: str | None = Field(default=None, description="Provider API key")
    model: str = Field(default="gpt-4", description="Model to use")

    # Client settings
    timeout: float = Field(default=30.0, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum number of retries")
    retry_delay: float = Field(default=1.0, description="Delay between retries")

    # Cache settings
    cache_enabled: bool = Field(default=True, description="Enable response caching")
    cache_ttl: int = Field(default=3600, description="Cache TTL in seconds")

    # Advanced settings
    provider_configs: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description="Provider-specific configurations",
    )
    hooks_enabled: bool = Field(default=True, description="Enable lifecycle hooks")
    experimental: bool = Field(
        default=False, description="Enable experimental features"
    )


# Global configuration manager
config_manager = UnifiedConfig[Config](Config)


async def initialize_config(config_path: Path | None = None) -> Config:
    """Initialize the configuration system.

    This function initializes the global configuration manager with settings from:
    1. Default configuration
    2. Configuration files
    3. Environment variables

    Args:
        config_path: Optional path to configuration file

    Returns:
        Initialized configuration instance

    Raises:
        ConfigurationError: If initialization fails or configuration is not available

    """
    try:
        await config_manager.initialize()
        if config_manager.config is None:
            raise ConfigurationError("Configuration not initialized")
        return config_manager.config
    except Exception as e:
        raise ConfigurationError(f"Failed to initialize configuration: {e}") from e


async def update_config(updates: dict[str, Any]) -> None:
    """Update the current configuration.

    Args:
        updates: Configuration updates to apply

    Raises:
        ConfigurationError: If update fails

    """
    await config_manager.update(updates)


def add_config_hook(
    event: str,
    callback: Any,
    source: ConfigSource | None = None,
) -> None:
    """Add a configuration lifecycle hook.

    Args:
        event: Event to hook into ("on_load", "on_update", "on_error")
        callback: Function to call when event occurs
        source: Optional source to restrict hook to

    Raises:
        ValueError: If event is invalid

    """
    config_manager.add_hook(event, callback, source)


def remove_config_hook(event: str, callback: Any) -> None:
    """Remove a configuration lifecycle hook.

    Args:
        event: Event to remove hook from
        callback: Callback to remove

    Raises:
        ValueError: If event is invalid

    """
    config_manager.remove_hook(event, callback)


__all__ = [
    # Configuration manager
    "config_manager",
    "ConfigurationManager",
    # Configuration models
    "Config",
    "Configuration",
    "LoggingConfig",
    "MonitoringConfig",
    "ProviderConfig",
    "ResourceConfig",
    "SecurityConfig",
    # Configuration system
    "ConfigHook",
    "ConfigSource",
    "ConfigState",
    "UnifiedConfig",
    # Dynamic loading
    "ProviderLoader",
    "ProcessorLoader",
    "load_class",
]
