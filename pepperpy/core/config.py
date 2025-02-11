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
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List

import yaml
from pydantic import BaseModel, Field

from pepperpy.monitoring import logger as log
from pepperpy.providers.base import ProviderConfig

from .errors import ConfigurationError

# Default configuration paths
DEFAULT_CONFIG_PATHS = [
    Path.home() / ".pepperpy/config.yml",
    Path.cwd() / ".pepperpy/config.yml",
    Path.cwd() / "pepperpy.yml",
]


class LogLevel(str, Enum):
    """Log levels supported by the system."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


# Type aliases for better readability
ConfigCallback = Callable[["PepperpyConfig"], None]


class PepperpyConfig(BaseModel):
    """Configuration for the Pepperpy client.

    Attributes
    ----------
        provider_type: Type of provider to use
        provider_config: Provider-specific configuration
        memory_config: Memory store configuration
        prompt_config: Prompt template configuration
        timeout: Operation timeout in seconds
        max_retries: Maximum number of retries
        retry_delay: Delay between retries in seconds

    """

    provider_type: str = Field(default="openrouter")
    provider_config: Dict[str, Any] = Field(default_factory=lambda: {})
    memory_config: Dict[str, Any] = Field(default_factory=lambda: {"type": "inmemory"})
    prompt_config: Dict[str, Any] = Field(default_factory=lambda: {"type": "jinja2"})
    timeout: float = Field(default=30.0, gt=0)
    max_retries: int = Field(default=3, ge=0)
    retry_delay: float = Field(default=1.0, ge=0)

    # Lifecycle hooks
    on_load_hooks: List[ConfigCallback] = Field(default_factory=list)
    on_save_hooks: List[ConfigCallback] = Field(default_factory=list)
    on_update_hooks: List[ConfigCallback] = Field(default_factory=list)

    @classmethod
    def auto(cls) -> "PepperpyConfig":
        """Create a configuration instance automatically.

        This method attempts to load configuration from:
        1. Environment variables
        2. Configuration files in standard locations
        3. Default values

        Returns
        -------
            A configured PepperpyConfig instance

        """
        # Start with environment configuration
        config = cls._load_from_env()

        # Try to load from config files
        for path in DEFAULT_CONFIG_PATHS:
            if path.exists():
                file_config = cls._load_from_yaml(path)
                config.update(file_config)
                break

        # Create instance with merged configuration
        try:
            instance = cls(**config)
            log.info("Created configuration automatically", sources=list(config.keys()))
            return instance
        except Exception as e:
            raise ConfigurationError(
                f"Failed to create configuration automatically: {e}"
            ) from e

    @classmethod
    def _load_from_env(cls) -> Dict[str, Any]:
        """Load configuration from environment variables.

        Returns
        -------
            Dictionary with configuration from environment

        """
        config = {}

        # Map environment variables to configuration
        env_mapping = {
            "PEPPERPY_PROVIDER": "provider_type",
            "PEPPERPY_API_KEY": ("provider_config", "api_key"),
            "PEPPERPY_MODEL": ("provider_config", "model"),
            "PEPPERPY_TIMEOUT": "timeout",
            "PEPPERPY_MAX_RETRIES": "max_retries",
            "PEPPERPY_RETRY_DELAY": "retry_delay",
            "PEPPERPY_CACHE_ENABLED": "cache_enabled",
            "PEPPERPY_CACHE_STORE": "cache_store",
        }

        for env_var, config_key in env_mapping.items():
            value = os.getenv(env_var)
            if value is not None:
                if isinstance(config_key, tuple):
                    # Handle nested configuration
                    current = config
                    for key in config_key[:-1]:
                        current = current.setdefault(key, {})
                    current[config_key[-1]] = value
                else:
                    config[config_key] = value

        return config

    @classmethod
    def _load_from_yaml(cls, path: Path) -> Dict[str, Any]:
        """Load configuration from a YAML file.

        Args:
        ----
            path: Path to the YAML file

        Returns:
        -------
            Dictionary with configuration from YAML

        """
        try:
            with path.open("r") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            log.warning(f"Failed to load config from {path}: {e}")
            return {}

    @property
    def on_load(self) -> List[ConfigCallback]:
        """Get the list of load hooks.

        Returns
        -------
            List of callback functions to run when configuration is loaded.

        """
        return self.on_load_hooks

    @property
    def on_save(self) -> List[ConfigCallback]:
        """Get the list of save hooks.

        Returns
        -------
            List of callback functions to run before configuration is saved.

        """
        return self.on_save_hooks

    @property
    def on_update(self) -> List[ConfigCallback]:
        """Get the list of update hooks.

        Returns
        -------
            List of callback functions to run when configuration is updated.

        """
        return self.on_update_hooks


class AutoConfig:
    """Automatic configuration loader.

    This class provides methods for automatically loading configuration from
    various sources, including environment variables and configuration files.
    """

    @classmethod
    def from_env(cls, prefix: str = "PEPPERPY_") -> PepperpyConfig:
        """Load configuration from environment variables.

        Args:
        ----
            prefix: Environment variable prefix (default: PEPPERPY_)

        Returns:
        -------
            Loaded configuration

        Raises:
        ------
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
        ----
            path: Path to configuration file

        Returns:
        -------
            Loaded configuration

        Raises:
        ------
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

        Returns
        -------
            Current configuration

        Raises
        ------
            ConfigurationError: If configuration is not loaded

        """
        if self._config is None:
            raise ConfigurationError("Configuration not loaded")
        return self._config

    def load(self, path: Path | None = None) -> PepperpyConfig:
        """Load configuration from file and environment.

        Args:
        ----
            path: Optional path to configuration file

        Returns:
        -------
            Loaded configuration

        Raises:
        ------
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
        ----
            path: Path to save configuration to

        Raises:
        ------
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
        ----
            updates: Configuration updates

        Raises:
        ------
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
        ----
            path: Optional path to configuration file

        Returns:
        -------
            Loaded configuration dictionary

        Raises:
        ------
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
    ----
        path: Optional path to configuration file

    Returns:
    -------
        Loaded configuration

    Raises:
    ------
        ConfigurationError: If configuration is invalid

    """
    return config_manager.load(path)


def save_config(config: PepperpyConfig, path: Path) -> None:
    """Save configuration to file.

    This is a convenience function that uses the global config manager.

    Args:
    ----
        config: Configuration to save
        path: Path to save configuration to

    Raises:
    ------
        ConfigurationError: If saving fails

    """
    # Update the global manager's config
    config_manager._config = config
    config_manager.save(path)
