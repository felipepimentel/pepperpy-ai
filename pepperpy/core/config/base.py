"""Base components for configuration management."""

import asyncio
import logging
from typing import TYPE_CHECKING, Dict, Generic, List, Optional, Set

from pydantic import ValidationError

from pepperpy.core.lifecycle import Lifecycle

from .types import ConfigT, ConfigValidationError, ConfigWatcher

if TYPE_CHECKING:
    from .sources import ConfigSource

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Base class for configuration-related errors."""

    def __init__(
        self,
        message: str,
        *,
        config_key: Optional[str] = None,
        details: Optional[Dict[str, str]] = None,
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
        self._config: Optional[ConfigT] = None
        self._sources: List["ConfigSource"] = []
        self._watchers: Set[ConfigWatcher] = set()
        self._lock = asyncio.Lock()

    @property
    def config(self) -> Optional[ConfigT]:
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
