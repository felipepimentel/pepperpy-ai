"""Plugin management system.

This module provides plugin management functionality:
- Plugin discovery and loading
- Plugin lifecycle management
- Plugin dependency resolution
- Plugin configuration and state
"""

import asyncio
import importlib.util
import inspect
from dataclasses import dataclass, field
from pathlib import Path
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
    """Base plugin class."""

    def __init__(self, metadata: PluginMetadata) -> None:
        """Initialize plugin.

        Args:
            metadata: Plugin metadata
        """
        super().__init__(metadata.name)
        self.metadata = metadata

    async def _initialize(self) -> None:
        """Initialize plugin.

        Raises:
            PluginError: If initialization fails
        """
        await self._initialize_plugin()
        logger.info(
            "Plugin initialized",
            extra={
                "name": self.name,
                "version": self.metadata.version,
            },
        )

    async def _cleanup(self) -> None:
        """Clean up plugin.

        Raises:
            PluginError: If cleanup fails
        """
        await self._cleanup_plugin()
        logger.info(
            "Plugin cleaned up",
            extra={
                "name": self.name,
                "version": self.metadata.version,
            },
        )

    async def _initialize_plugin(self) -> None:
        """Initialize plugin implementation.

        This method should be implemented by subclasses to provide
        plugin-specific initialization logic.

        Raises:
            PluginError: If initialization fails
        """
        pass

    async def _cleanup_plugin(self) -> None:
        """Clean up plugin implementation.

        This method should be implemented by subclasses to provide
        plugin-specific cleanup logic.

        Raises:
            PluginError: If cleanup fails
        """
        pass


class PluginManager(LifecycleComponent):
    """Manager for plugin lifecycle."""

    def __init__(self) -> None:
        """Initialize manager."""
        super().__init__("plugin_manager")
        self._plugins: dict[str, Plugin] = {}
        self._initialized = False
        self._lock = asyncio.Lock()

    async def _initialize(self) -> None:
        """Initialize manager.

        Raises:
            PluginError: If initialization fails
        """
        await self._validate_plugins()
        await self._initialize_plugins()
        self._initialized = True
        logger.info("Plugin manager initialized")

    async def _cleanup(self) -> None:
        """Clean up manager.

        Raises:
            PluginError: If cleanup fails
        """
        await self._cleanup_plugins()
        self._initialized = False
        logger.info("Plugin manager cleaned up")

    def register_plugin(self, plugin: Plugin) -> None:
        """Register a plugin.

        Args:
            plugin: Plugin to register

        Raises:
            PluginError: If plugin is already registered
        """
        if plugin.name in self._plugins:
            raise PluginError(f"Plugin {plugin.name} is already registered")

        self._plugins[plugin.name] = plugin
        logger.info(
            "Plugin registered",
            extra={
                "name": plugin.name,
                "version": plugin.metadata.version,
            },
        )

    def unregister_plugin(self, name: str) -> None:
        """Unregister a plugin.

        Args:
            name: Plugin name

        Raises:
            PluginError: If plugin is not registered
        """
        if name not in self._plugins:
            raise PluginError(f"Plugin {name} is not registered")

        plugin = self._plugins.pop(name)
        logger.info(
            "Plugin unregistered",
            extra={
                "name": plugin.name,
                "version": plugin.metadata.version,
            },
        )

    def get_plugin(self, name: str, type: type[Plugin] | None = None) -> Plugin:
        """Get a plugin.

        Args:
            name: Plugin name
            type: Optional plugin type to validate

        Returns:
            Plugin: Plugin instance

        Raises:
            PluginError: If plugin is not found or type mismatch
        """
        if name not in self._plugins:
            raise PluginError(f"Plugin {name} not found")

        plugin = self._plugins[name]
        if type is not None and not isinstance(plugin, type):
            raise PluginError(f"Plugin {name} is not of type {type.__name__}")

        return plugin

    def list_plugins(self) -> list[str]:
        """List registered plugins.

        Returns:
            list[str]: List of plugin names
        """
        return list(self._plugins.keys())

    async def load_plugins(self, directory: str) -> None:
        """Load plugins from directory.

        Args:
            directory: Plugin directory path

        Raises:
            PluginError: If plugin loading fails
        """
        try:
            path = Path(directory)
            if not path.is_dir():
                raise PluginError(f"Invalid plugin directory: {directory}")

            for file in path.glob("*.py"):
                if file.name.startswith("_"):
                    continue
                await self._load_plugin(str(file))

        except Exception as e:
            raise PluginError(f"Failed to load plugins: {e}")

    async def _load_plugin(self, path: str) -> None:
        """Load a plugin from file.

        Args:
            path: Plugin file path

        Raises:
            PluginError: If plugin loading fails
        """
        try:
            module_path = Path(path)
            if not module_path.exists():
                raise PluginError(f"Plugin file not found: {path}")

            # Import module
            module_name = module_path.stem
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            if not spec or not spec.loader:
                raise PluginError(f"Invalid plugin module: {path}")

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find plugin classes
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and issubclass(obj, Plugin) and obj != Plugin:
                    # Create plugin instance with default metadata
                    metadata = PluginMetadata(
                        name=name,
                        version="0.1.0",
                        description=obj.__doc__ or "No description",
                        author="Unknown",
                    )
                    plugin = obj(metadata)
                    self.register_plugin(plugin)
                    break
            else:
                raise PluginError(f"No plugin class found in {path}")

        except Exception as e:
            raise PluginError(f"Failed to load plugin {path}: {e}")

    async def _validate_plugins(self) -> None:
        """Validate plugin dependencies.

        Raises:
            PluginError: If validation fails
        """
        visited: set[str] = set()
        visiting: set[str] = set()

        def check_cycles(name: str) -> None:
            """Check for dependency cycles.

            Args:
                name: Plugin name

            Raises:
                PluginError: If cycle is detected
            """
            if name in visiting:
                raise PluginError(f"Dependency cycle detected: {name}")
            if name in visited:
                return

            visiting.add(name)
            plugin = self._plugins[name]
            for dep in plugin.metadata.dependencies:
                if dep not in self._plugins:
                    raise PluginError(f"Missing dependency {dep} for plugin {name}")
                check_cycles(dep)
            visiting.remove(name)
            visited.add(name)

        for name in self._plugins:
            check_cycles(name)

    async def _initialize_plugins(self) -> None:
        """Initialize plugins in dependency order.

        Raises:
            PluginError: If initialization fails
        """
        initialized: set[str] = set()

        async def initialize_plugin(name: str) -> None:
            """Initialize a plugin and its dependencies.

            Args:
                name: Plugin name

            Raises:
                PluginError: If initialization fails
            """
            if name in initialized:
                return

            plugin = self._plugins[name]
            for dep in plugin.metadata.dependencies:
                await initialize_plugin(dep)

            try:
                await plugin.initialize()
                initialized.add(name)
            except Exception as e:
                raise PluginError(f"Failed to initialize plugin {name}: {e}")

        for name in self._plugins:
            await initialize_plugin(name)

    async def _cleanup_plugins(self) -> None:
        """Clean up plugins in reverse dependency order.

        Raises:
            PluginError: If cleanup fails
        """
        cleaned: set[str] = set()

        async def cleanup_plugin(name: str) -> None:
            """Clean up a plugin and its dependents.

            Args:
                name: Plugin name

            Raises:
                PluginError: If cleanup fails
            """
            if name in cleaned:
                return

            plugin = self._plugins[name]
            for dep_name, dep in self._plugins.items():
                if name in dep.metadata.dependencies:
                    await cleanup_plugin(dep_name)

            try:
                await plugin.cleanup()
                cleaned.add(name)
            except Exception as e:
                raise PluginError(f"Failed to clean up plugin {name}: {e}")

        for name in reversed(list(self._plugins)):
            await cleanup_plugin(name)


__all__ = [
    "Plugin",
    "PluginManager",
    "PluginMetadata",
]
