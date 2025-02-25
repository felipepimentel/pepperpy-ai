"""Plugin management system.

This module provides plugin management functionality:
- Plugin discovery and loading
- Plugin lifecycle management
- Plugin dependency resolution
- Plugin configuration and state
"""

import importlib
import importlib.util
import inspect
import os
from dataclasses import dataclass, field
from typing import Any

from pepperpy.core.errors import PluginError
from pepperpy.core.lifecycle import LifecycleComponent
from pepperpy.core.logging import get_logger

# Configure logging
logger = get_logger(__name__)


@dataclass
class PluginMetadata:
    """Plugin metadata information."""

    name: str
    version: str
    description: str
    author: str
    dependencies: set[str] = field(default_factory=set)
    config: dict[str, Any] = field(default_factory=dict)
    tags: dict[str, str] = field(default_factory=dict)


class Plugin(LifecycleComponent):
    """Base class for plugins."""

    def __init__(self, metadata: PluginMetadata) -> None:
        """Initialize plugin.

        Args:
            metadata: Plugin metadata
        """
        super().__init__(f"plugin_{metadata.name}")
        self.metadata = metadata

    async def initialize(self) -> None:
        """Initialize plugin.

        Raises:
            PluginError: If initialization fails
        """
        try:
            await super().initialize()
            await self._initialize_plugin()
            logger.info(
                "Plugin initialized",
                extra={
                    "name": self.metadata.name,
                    "version": self.metadata.version,
                },
            )
        except Exception as e:
            raise PluginError(f"Failed to initialize plugin {self.metadata.name}: {e}")

    async def cleanup(self) -> None:
        """Clean up plugin.

        Raises:
            PluginError: If cleanup fails
        """
        try:
            await super().cleanup()
            await self._cleanup_plugin()
            logger.info(
                "Plugin cleaned up",
                extra={
                    "name": self.metadata.name,
                    "version": self.metadata.version,
                },
            )
        except Exception as e:
            raise PluginError(f"Failed to clean up plugin {self.metadata.name}: {e}")

    async def _initialize_plugin(self) -> None:
        """Initialize plugin implementation.

        This method should be overridden by subclasses to perform
        plugin-specific initialization.

        Raises:
            PluginError: If initialization fails
        """
        pass

    async def _cleanup_plugin(self) -> None:
        """Clean up plugin implementation.

        This method should be overridden by subclasses to perform
        plugin-specific cleanup.

        Raises:
            PluginError: If cleanup fails
        """
        pass


class PluginManager(LifecycleComponent):
    """Manages plugins and their lifecycle."""

    def __init__(self) -> None:
        """Initialize plugin manager."""
        super().__init__("plugin_manager")
        self._plugins: dict[str, Plugin] = {}
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize plugin manager.

        Raises:
            PluginError: If initialization fails
        """
        try:
            await super().initialize()
            await self._validate_plugins()
            await self._initialize_plugins()
            self._initialized = True
            logger.info("Plugin manager initialized")
        except Exception as e:
            raise PluginError(f"Failed to initialize plugin manager: {e}")

    async def cleanup(self) -> None:
        """Clean up plugin manager.

        Raises:
            PluginError: If cleanup fails
        """
        try:
            await super().cleanup()
            await self._cleanup_plugins()
            self._initialized = False
            logger.info("Plugin manager cleaned up")
        except Exception as e:
            raise PluginError(f"Failed to clean up plugin manager: {e}")

    def register_plugin(self, plugin: Plugin) -> None:
        """Register plugin.

        Args:
            plugin: Plugin instance

        Raises:
            PluginError: If registration fails
        """
        name = plugin.metadata.name
        if name in self._plugins:
            raise PluginError(f"Plugin {name} already registered")

        self._plugins[name] = plugin
        logger.info(
            "Plugin registered",
            extra={
                "name": name,
                "version": plugin.metadata.version,
            },
        )

    def unregister_plugin(self, name: str) -> None:
        """Unregister plugin.

        Args:
            name: Plugin name

        Raises:
            PluginError: If unregistration fails
        """
        if name not in self._plugins:
            raise PluginError(f"Unknown plugin {name}")

        # Check if any other plugins depend on this one
        for plugin in self._plugins.values():
            if name in plugin.metadata.dependencies:
                raise PluginError(
                    f"Cannot unregister {name}, {plugin.metadata.name} depends on it"
                )

        del self._plugins[name]
        logger.info(
            "Plugin unregistered",
            extra={"name": name},
        )

    def get_plugin(self, name: str, type: type[Plugin] | None = None) -> Plugin:
        """Get plugin instance.

        Args:
            name: Plugin name
            type: Expected plugin type

        Returns:
            Plugin instance

        Raises:
            PluginError: If plugin not found or type mismatch
        """
        if not self._initialized:
            raise PluginError("Plugin manager not initialized")

        if name not in self._plugins:
            raise PluginError(f"Unknown plugin {name}")

        plugin = self._plugins[name]
        if type and not isinstance(plugin, type):
            raise PluginError(
                f"Type mismatch for {name}: expected {type}, got {type(plugin)}"
            )

        return plugin

    def list_plugins(self) -> list[str]:
        """List registered plugins.

        Returns:
            List of plugin names
        """
        return list(self._plugins.keys())

    async def load_plugins(self, directory: str) -> None:
        """Load plugins from directory.

        Args:
            directory: Plugin directory path

        Raises:
            PluginError: If loading fails
        """
        try:
            for entry in os.listdir(directory):
                path = os.path.join(directory, entry)
                if os.path.isdir(path) and os.path.exists(
                    os.path.join(path, "__init__.py")
                ):
                    await self._load_plugin(path)
        except Exception as e:
            raise PluginError(f"Failed to load plugins from {directory}: {e}")

    async def _load_plugin(self, path: str) -> None:
        """Load plugin from path.

        Args:
            path: Plugin path

        Raises:
            PluginError: If loading fails
        """
        try:
            # Import plugin module
            module_name = os.path.basename(path)
            spec = importlib.util.spec_from_file_location(
                module_name,
                os.path.join(path, "__init__.py"),
            )
            if not spec or not spec.loader:
                raise PluginError(f"Failed to load plugin spec from {path}")

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find plugin class
            for item in dir(module):
                obj = getattr(module, item)
                if inspect.isclass(obj) and issubclass(obj, Plugin) and obj != Plugin:
                    # Create plugin instance
                    plugin = obj()
                    self.register_plugin(plugin)
                    break
            else:
                raise PluginError(f"No plugin class found in {path}")
        except Exception as e:
            raise PluginError(f"Failed to load plugin from {path}: {e}")

    async def _validate_plugins(self) -> None:
        """Validate plugin dependencies.

        Raises:
            PluginError: If validation fails
        """
        # Check for missing dependencies
        for plugin in self._plugins.values():
            for dep in plugin.metadata.dependencies:
                if dep not in self._plugins:
                    raise PluginError(
                        f"Missing dependency {dep} for plugin {plugin.metadata.name}"
                    )

        # Check for cycles
        visited: set[str] = set()
        path: set[str] = set()

        def check_cycles(name: str) -> None:
            if name in path:
                cycle = " -> ".join(list(path) + [name])
                raise PluginError(f"Plugin dependency cycle detected: {cycle}")
            if name in visited:
                return

            visited.add(name)
            path.add(name)
            for dep in self._plugins[name].metadata.dependencies:
                check_cycles(dep)
            path.remove(name)

        for name in self._plugins:
            check_cycles(name)

        logger.info("Plugin dependencies validated")

    async def _initialize_plugins(self) -> None:
        """Initialize plugins.

        Raises:
            PluginError: If initialization fails
        """
        # Initialize in dependency order
        initialized: set[str] = set()

        async def initialize_plugin(name: str) -> None:
            if name in initialized:
                return

            # Initialize dependencies first
            plugin = self._plugins[name]
            for dep in plugin.metadata.dependencies:
                await initialize_plugin(dep)

            # Initialize plugin
            try:
                await plugin.initialize()
            except Exception as e:
                raise PluginError(f"Failed to initialize plugin {name}: {e}")

            initialized.add(name)

        for name in self._plugins:
            await initialize_plugin(name)

        logger.info("Plugins initialized")

    async def _cleanup_plugins(self) -> None:
        """Clean up plugins.

        Raises:
            PluginError: If cleanup fails
        """
        # Clean up in reverse dependency order
        cleaned: set[str] = set()

        async def cleanup_plugin(name: str) -> None:
            if name in cleaned:
                return

            # Clean up plugins that depend on this one first
            dependents = {
                p.metadata.name
                for p in self._plugins.values()
                if name in p.metadata.dependencies
            }
            for dep in dependents:
                await cleanup_plugin(dep)

            # Clean up plugin
            plugin = self._plugins[name]
            try:
                await plugin.cleanup()
            except Exception as e:
                raise PluginError(f"Failed to clean up plugin {name}: {e}")

            cleaned.add(name)

        for name in reversed(list(self._plugins)):
            await cleanup_plugin(name)

        logger.info("Plugins cleaned up")
