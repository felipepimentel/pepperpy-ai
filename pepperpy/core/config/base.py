"""Base components for configuration management."""

import asyncio
import importlib
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Generic, TypeVar

import yaml
from pydantic import ValidationError

from pepperpy.core.base import Lifecycle

from .types import ConfigT, ConfigValidationError, ConfigWatcher

if TYPE_CHECKING:
    from .sources import ConfigSource

logger = logging.getLogger(__name__)

T = TypeVar("T")


class Configuration:
    """Central configuration management for Pepperpy framework."""

    def __init__(self, config_path: Path | None = None):
        """Initialize configuration manager.

        Args:
            config_path: Optional path to configuration file. Defaults to ~/.pepperpy/config.yml
        """
        self.config_path = config_path or Path.home() / ".pepperpy" / "config.yml"
        self.providers: dict[str, dict[str, Any]] = {}
        self.load_config()

    def load_config(self) -> None:
        """Load configuration from file or use defaults."""
        if self.config_path.exists():
            with open(self.config_path) as f:
                self.providers = yaml.safe_load(f) or {}
        else:
            self.providers = self._get_default_config()

    def get_provider(self, capability: str, name: str = "default") -> dict[str, Any]:
        """Get provider configuration.

        Args:
            capability: Capability name (e.g. 'llm', 'content')
            name: Provider name within capability. Defaults to 'default'

        Returns:
            Provider configuration dictionary

        Raises:
            ConfigError: If provider configuration is not found
        """
        capability_config = self.providers.get(capability, {})
        provider_config = capability_config.get(name)

        if not provider_config:
            raise ConfigurationError(
                f"Provider {capability}.{name} not found in configuration"
            )

        return provider_config

    def load_provider(self, capability: str, name: str, base_class: type[T]) -> T:
        """Dynamically load and instantiate a provider.

        Args:
            capability: Capability name (e.g. 'llm', 'content')
            name: Provider name within capability
            base_class: Base class that provider must implement

        Returns:
            Instantiated provider

        Raises:
            ConfigError: If provider cannot be loaded or instantiated
        """
        config = self.get_provider(capability, name)
        provider_type = config["type"]
        provider_config = config.get("config", {})

        try:
            # Load provider module
            module_path = f"pepperpy.{capability}.providers.{provider_type}"
            module = importlib.import_module(module_path)

            # Get provider class
            provider_class = getattr(module, f"{provider_type.title()}Provider")

            # Validate provider class
            if not issubclass(provider_class, base_class):
                raise ConfigurationError(
                    f"Provider class {provider_class.__name__} does not implement {base_class.__name__}"
                )

            # Instantiate provider
            return provider_class(**provider_config)

        except (ImportError, AttributeError) as e:
            raise ConfigurationError(
                f"Failed to load provider {capability}.{name}: {e!s}"
            )

    def _get_default_config(self) -> dict[str, dict[str, Any]]:
        """Get default configuration when no config file exists."""
        return {
            "llm": {
                "default": {
                    "type": "openai",
                    "config": {"model": "gpt-3.5-turbo", "temperature": 0.7},
                }
            },
            "content": {
                "default": {
                    "type": "rss",
                    "config": {
                        "sources": ["https://news.google.com/rss"],
                        "language": "pt-BR",
                    },
                }
            },
            "synthesis": {
                "default": {
                    "type": "openai",
                    "config": {"voice": "alloy", "model": "tts-1"},
                }
            },
            "memory": {
                "default": {"type": "local", "config": {"path": "~/.pepperpy/memory"}}
            },
        }


class ConfigurationError(Exception):
    """Base class for configuration-related errors."""

    def __init__(
        self,
        message: str,
        *,
        config_key: str | None = None,
        details: dict[str, str] | None = None,
    ) -> None:
        """Initialize the error.

        Args:
            message: Error message
            config_key: Optional configuration key that caused the error
            details: Optional additional details

        """
        super().__init__(message)
        self.config_key = config_key
        self.details = details or {}


class ConfigurationManager(Lifecycle, Generic[ConfigT]):
    """Central manager for configuration handling.

    This class manages configuration loading, validation, and updates.
    It supports multiple configuration sources and dynamic updates.

    Type Args:
        ConfigT: Configuration model type (must be a Pydantic BaseModel)

    Attributes:
        config: Current configuration
        sources: Registered configuration sources
        watchers: Configuration change watchers

    """

    def __init__(self, config_class: type[ConfigT]) -> None:
        """Initialize the configuration manager.

        Args:
            config_class: Configuration model class

        """
        super().__init__()
        self.config_class = config_class
        self._config: ConfigT | None = None
        self._sources: list[ConfigSource] = []
        self._watchers: set[ConfigWatcher] = set()
        self._lock = asyncio.Lock()

    @property
    def config(self) -> ConfigT | None:
        """Get the current configuration."""
        return self._config

    async def initialize(self) -> None:
        """Initialize the configuration manager.

        This loads the initial configuration from all sources.

        Raises:
            ConfigurationError: If initialization fails

        """
        try:
            await self.reload()
        except Exception as e:
            raise ConfigurationError(f"Failed to initialize configuration: {e}")

    async def cleanup(self) -> None:
        """Clean up resources."""
        self._sources.clear()
        self._watchers.clear()
        self._config = None

    async def reload(self) -> None:
        """Reload configuration from all sources.

        This method merges configuration from all sources in order
        and notifies watchers of changes.

        Raises:
            ConfigurationError: If reload fails
            ConfigValidationError: If configuration is invalid

        """
        async with self._lock:
            try:
                # Collect configuration from all sources
                config_data = {}
                for source in self._sources:
                    data = await source.load()
                    config_data.update(data)

                # Create new configuration
                old_config = self._config
                try:
                    self._config = self.config_class(**config_data)
                except ValidationError as e:
                    raise ConfigValidationError(
                        "Configuration validation failed",
                        details={"validation_errors": e.errors()},
                    )

                # Notify watchers if configuration changed
                if old_config is not None and old_config != self._config:
                    await self._notify_watchers(old_config, self._config)

            except Exception as e:
                raise ConfigurationError(f"Failed to reload configuration: {e}")

    def add_source(self, source: "ConfigSource") -> None:
        """Add a configuration source.

        Sources are processed in order of addition.

        Args:
            source: Configuration source to add

        """
        self._sources.append(source)

    def remove_source(self, source: "ConfigSource") -> None:
        """Remove a configuration source.

        Args:
            source: Configuration source to remove

        """
        self._sources.remove(source)

    def add_watcher(self, watcher: ConfigWatcher) -> None:
        """Add a configuration change watcher.

        Args:
            watcher: Watcher to add

        """
        self._watchers.add(watcher)

    def remove_watcher(self, watcher: ConfigWatcher) -> None:
        """Remove a configuration change watcher.

        Args:
            watcher: Watcher to remove

        """
        self._watchers.discard(watcher)

    async def _notify_watchers(self, old_config: ConfigT, new_config: ConfigT) -> None:
        """Notify watchers of configuration changes.

        Args:
            old_config: Previous configuration
            new_config: New configuration

        """
        for watcher in self._watchers:
            try:
                await watcher.on_config_change(old_config, new_config)
            except Exception as e:
                logger.error(
                    f"Error in configuration watcher: {e}",
                    extra={
                        "watcher": watcher.__class__.__name__,
                        "error": str(e),
                    },
                )
