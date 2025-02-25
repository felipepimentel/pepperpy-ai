"""Base plugin functionality for the Pepperpy framework.

This module provides the base classes and interfaces for the plugin system.
"""

import abc
from typing import Any, TypeVar

from pepperpy.core.config import ConfigModel
from pepperpy.core.metrics import metrics_manager
from pepperpy.core.observability import observability_manager


class PluginConfig(ConfigModel):
    """Configuration for a plugin.

    Attributes:
        enabled: Whether the plugin is enabled
        priority: Plugin load priority (lower loads first)
        dependencies: List of required plugin names
        settings: Plugin-specific settings
    """

    enabled: bool = True
    priority: int = 100
    dependencies: list[str] = []
    settings: dict[str, Any] = {}


T = TypeVar("T", bound="PluginBase")


class PluginBase(abc.ABC):
    """Base class for plugins.

    All plugins must inherit from this class and implement the required
    lifecycle methods.
    """

    def __init__(self) -> None:
        """Initialize the plugin."""
        self.config = PluginConfig()
        self._metrics = metrics_manager
        self._observability = observability_manager
        self._initialized = False

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Get plugin name.

        Returns:
            Plugin name
        """
        pass

    @property
    @abc.abstractmethod
    def version(self) -> str:
        """Get plugin version.

        Returns:
            Plugin version string
        """
        pass

    @property
    def description(self) -> str:
        """Get plugin description.

        Returns:
            Plugin description
        """
        return "No description available"

    @property
    def dependencies(self) -> list[str]:
        """Get plugin dependencies.

        Returns:
            List of required plugin names
        """
        return self.config.dependencies

    @property
    def is_initialized(self) -> bool:
        """Check if plugin is initialized.

        Returns:
            True if plugin is initialized
        """
        return self._initialized

    async def initialize(self) -> None:
        """Initialize the plugin.

        This method is called when the plugin is loaded. Override to
        perform initialization tasks.

        Raises:
            PluginError: If initialization fails
        """
        try:
            start = self._metrics.counter(
                "plugin_initialize",
                "Plugin initialization count",
                labels={"plugin": self.name},
            )

            # Perform initialization
            await self._initialize()
            self._initialized = True

            # Record success
            start.inc()
            self._observability.log_info(
                "plugins.initialize",
                f"Plugin {self.name} initialized successfully",
                context={"plugin": self.name, "version": self.version},
            )

        except Exception as e:
            # Record failure
            self._metrics.counter(
                "plugin_initialize_errors",
                "Plugin initialization error count",
                labels={"plugin": self.name},
            ).inc()

            self._observability.log_error(
                "plugins.initialize",
                f"Failed to initialize plugin {self.name}",
                exception=e,
                context={"plugin": self.name, "version": self.version},
            )
            raise

    async def cleanup(self) -> None:
        """Clean up plugin resources.

        This method is called when the plugin is unloaded. Override to
        perform cleanup tasks.

        Raises:
            PluginError: If cleanup fails
        """
        try:
            start = self._metrics.counter(
                "plugin_cleanup",
                "Plugin cleanup count",
                labels={"plugin": self.name},
            )

            # Perform cleanup
            await self._cleanup()
            self._initialized = False

            # Record success
            start.inc()
            self._observability.log_info(
                "plugins.cleanup",
                f"Plugin {self.name} cleaned up successfully",
                context={"plugin": self.name, "version": self.version},
            )

        except Exception as e:
            # Record failure
            self._metrics.counter(
                "plugin_cleanup_errors",
                "Plugin cleanup error count",
                labels={"plugin": self.name},
            ).inc()

            self._observability.log_error(
                "plugins.cleanup",
                f"Failed to clean up plugin {self.name}",
                exception=e,
                context={"plugin": self.name, "version": self.version},
            )
            raise

    @abc.abstractmethod
    async def _initialize(self) -> None:
        """Initialize plugin resources.

        Override this method to perform actual initialization.

        Raises:
            PluginError: If initialization fails
        """
        pass

    @abc.abstractmethod
    async def _cleanup(self) -> None:
        """Clean up plugin resources.

        Override this method to perform actual cleanup.

        Raises:
            PluginError: If cleanup fails
        """
        pass


class PluginError(Exception):
    """Base class for plugin-related errors."""

    def __init__(self, message: str, plugin: str | None = None) -> None:
        """Initialize the error.

        Args:
            message: Error message
            plugin: Optional plugin name
        """
        super().__init__(message)
        self.plugin = plugin


class PluginNotFoundError(PluginError):
    """Raised when a plugin is not found."""

    pass


class PluginLoadError(PluginError):
    """Raised when a plugin fails to load."""

    pass


class PluginDependencyError(PluginError):
    """Raised when plugin dependencies cannot be satisfied."""

    pass


__all__ = [
    "PluginBase",
    "PluginConfig",
    "PluginDependencyError",
    "PluginError",
    "PluginLoadError",
    "PluginNotFoundError",
]
