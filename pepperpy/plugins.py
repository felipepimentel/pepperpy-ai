"""PepperPy Plugins Module.

This module provides plugin management functionality for the PepperPy framework, including:
- Plugin discovery and loading
- Plugin lifecycle management
- Plugin dependency management

The plugins module is designed to enable extensibility of the framework through
the addition of custom functionality via plugins.
"""

import importlib
import inspect
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, TypeVar

from pepperpy.core.errors import PepperPyError, ValidationError
from pepperpy.core.logging import get_logger

# Logger for this module
logger = get_logger(__name__)

# Type variable for plugin types
T = TypeVar("T")


class PluginError(PepperPyError):
    """Error raised when a plugin operation fails."""

    pass


class PluginState:
    """States of a plugin's lifecycle."""

    UNLOADED = "unloaded"
    LOADED = "loaded"
    INITIALIZED = "initialized"
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"


@dataclass
class PluginInfo:
    """Information about a plugin.

    Plugin information includes metadata about a plugin, such as its name, version,
    description, and dependencies.
    """

    name: str
    version: str
    description: Optional[str] = None
    author: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    entry_point: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the plugin information to a dictionary.

        Returns:
            The plugin information as a dictionary
        """
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "dependencies": self.dependencies,
            "tags": self.tags,
            "metadata": self.metadata,
            "entry_point": self.entry_point,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PluginInfo":
        """Create plugin information from a dictionary.

        Args:
            data: The dictionary to create the plugin information from

        Returns:
            The created plugin information
        """
        return cls(
            name=data["name"],
            version=data["version"],
            description=data.get("description"),
            author=data.get("author"),
            dependencies=data.get("dependencies", []),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
            entry_point=data.get("entry_point"),
        )

    def get_id(self) -> str:
        """Get the ID for the plugin.

        Returns:
            The ID for the plugin
        """
        return f"{self.name}@{self.version}"


class Plugin(ABC):
    """Base class for plugins.

    A plugin is a component that can be loaded, initialized, enabled, disabled,
    and unloaded. Plugins can extend the functionality of the PepperPy framework.
    """

    def __init__(self, info: PluginInfo):
        """Initialize a plugin.

        Args:
            info: Information about the plugin
        """
        self.info = info
        self.state = PluginState.UNLOADED
        self._error: Optional[Exception] = None

    def initialize(self) -> None:
        """Initialize the plugin.

        This method is called when the plugin is initialized. It calls the
        on_initialize method, which should be implemented by subclasses.

        Raises:
            PluginError: If the plugin is not in the LOADED state
            Exception: If initialization fails
        """
        if self.state != PluginState.LOADED:
            raise PluginError(
                f"Cannot initialize plugin {self.info.name}: not in LOADED state"
            )

        try:
            self.on_initialize()
            self.state = PluginState.INITIALIZED
        except Exception as e:
            self._error = e
            self.state = PluginState.ERROR
            raise

    def enable(self) -> None:
        """Enable the plugin.

        This method is called when the plugin is enabled. It calls the
        on_enable method, which should be implemented by subclasses.

        Raises:
            PluginError: If the plugin is not in the INITIALIZED or DISABLED state
            Exception: If enabling fails
        """
        if self.state not in [PluginState.INITIALIZED, PluginState.DISABLED]:
            raise PluginError(
                f"Cannot enable plugin {self.info.name}: not in INITIALIZED or DISABLED state"
            )

        try:
            self.on_enable()
            self.state = PluginState.ENABLED
        except Exception as e:
            self._error = e
            self.state = PluginState.ERROR
            raise

    def disable(self) -> None:
        """Disable the plugin.

        This method is called when the plugin is disabled. It calls the
        on_disable method, which should be implemented by subclasses.

        Raises:
            PluginError: If the plugin is not in the ENABLED state
            Exception: If disabling fails
        """
        if self.state != PluginState.ENABLED:
            raise PluginError(
                f"Cannot disable plugin {self.info.name}: not in ENABLED state"
            )

        try:
            self.on_disable()
            self.state = PluginState.DISABLED
        except Exception as e:
            self._error = e
            self.state = PluginState.ERROR
            raise

    def unload(self) -> None:
        """Unload the plugin.

        This method is called when the plugin is unloaded. It calls the
        on_unload method, which should be implemented by subclasses.

        Raises:
            PluginError: If the plugin is not in the INITIALIZED, DISABLED, or ERROR state
            Exception: If unloading fails
        """
        if self.state not in [
            PluginState.INITIALIZED,
            PluginState.DISABLED,
            PluginState.ERROR,
        ]:
            raise PluginError(
                f"Cannot unload plugin {self.info.name}: not in INITIALIZED, DISABLED, or ERROR state"
            )

        try:
            self.on_unload()
            self.state = PluginState.UNLOADED
        except Exception as e:
            self._error = e
            self.state = PluginState.ERROR
            raise

    def validate(self) -> None:
        """Validate the plugin.

        This method is called to validate the plugin. It calls the
        on_validate method, which can be overridden by subclasses.

        Raises:
            ValidationError: If validation fails
        """
        try:
            self.on_validate()
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(f"Plugin validation failed: {str(e)}") from e

    @abstractmethod
    def on_initialize(self) -> None:
        """Called when the plugin is initialized.

        This method should be implemented by subclasses to perform
        initialization tasks.
        """
        pass

    @abstractmethod
    def on_enable(self) -> None:
        """Called when the plugin is enabled.

        This method should be implemented by subclasses to perform
        enabling tasks.
        """
        pass

    @abstractmethod
    def on_disable(self) -> None:
        """Called when the plugin is disabled.

        This method should be implemented by subclasses to perform
        disabling tasks.
        """
        pass

    @abstractmethod
    def on_unload(self) -> None:
        """Called when the plugin is unloaded.

        This method should be implemented by subclasses to perform
        unloading tasks.
        """
        pass

    def on_validate(self) -> None:
        """Called when the plugin is validated.

        This method can be overridden by subclasses to perform
        validation tasks.
        """
        pass


class PluginManager:
    """Manager for plugins.

    The plugin manager is responsible for loading, initializing, enabling,
    disabling, and unloading plugins. It also provides methods for discovering
    plugins and managing plugin dependencies.
    """

    def __init__(self):
        """Initialize the plugin manager."""
        self._plugins: Dict[str, Plugin] = {}
        self._plugin_directories: List[str] = []

    def register_plugin(self, plugin: Plugin) -> None:
        """Register a plugin.

        Args:
            plugin: The plugin to register

        Raises:
            PluginError: If a plugin with the same ID is already registered
        """
        plugin_id = plugin.info.get_id()
        if plugin_id in self._plugins:
            raise PluginError(f"Plugin {plugin_id} already registered")
        self._plugins[plugin_id] = plugin
        logger.info(f"Registered plugin: {plugin_id}")

    def unregister_plugin(self, plugin_id: str) -> None:
        """Unregister a plugin.

        Args:
            plugin_id: The ID of the plugin to unregister

        Raises:
            PluginError: If the plugin is not registered
        """
        if plugin_id not in self._plugins:
            raise PluginError(f"Plugin {plugin_id} not registered")
        del self._plugins[plugin_id]
        logger.info(f"Unregistered plugin: {plugin_id}")

    def get_plugin(self, plugin_id: str) -> Plugin:
        """Get a plugin.

        Args:
            plugin_id: The ID of the plugin to get

        Returns:
            The plugin

        Raises:
            PluginError: If the plugin is not registered
        """
        if plugin_id not in self._plugins:
            raise PluginError(f"Plugin {plugin_id} not registered")
        return self._plugins[plugin_id]

    def list_plugins(self) -> List[Plugin]:
        """List all registered plugins.

        Returns:
            A list of all registered plugins
        """
        return list(self._plugins.values())

    def load_plugin(self, plugin: Plugin) -> None:
        """Load a plugin.

        Args:
            plugin: The plugin to load

        Raises:
            PluginError: If the plugin is already loaded
        """
        if plugin.state != PluginState.UNLOADED:
            raise PluginError(f"Plugin {plugin.info.name} already loaded")

        # Register the plugin
        self.register_plugin(plugin)

        # Update the plugin state
        plugin.state = PluginState.LOADED
        logger.info(f"Loaded plugin: {plugin.info.get_id()}")

    def initialize_plugin(self, plugin_id: str) -> None:
        """Initialize a plugin.

        Args:
            plugin_id: The ID of the plugin to initialize

        Raises:
            PluginError: If the plugin is not registered or not in the LOADED state
        """
        plugin = self.get_plugin(plugin_id)
        if plugin.state != PluginState.LOADED:
            raise PluginError(
                f"Cannot initialize plugin {plugin_id}: not in LOADED state"
            )

        # Initialize the plugin
        try:
            plugin.initialize()
            logger.info(f"Initialized plugin: {plugin_id}")
        except Exception as e:
            logger.error(f"Failed to initialize plugin {plugin_id}: {str(e)}")
            raise

    def enable_plugin(self, plugin_id: str) -> None:
        """Enable a plugin.

        Args:
            plugin_id: The ID of the plugin to enable

        Raises:
            PluginError: If the plugin is not registered or not in the INITIALIZED or DISABLED state
        """
        plugin = self.get_plugin(plugin_id)
        if plugin.state not in [PluginState.INITIALIZED, PluginState.DISABLED]:
            raise PluginError(
                f"Cannot enable plugin {plugin_id}: not in INITIALIZED or DISABLED state"
            )

        # Enable the plugin
        try:
            plugin.enable()
            logger.info(f"Enabled plugin: {plugin_id}")
        except Exception as e:
            logger.error(f"Failed to enable plugin {plugin_id}: {str(e)}")
            raise

    def disable_plugin(self, plugin_id: str) -> None:
        """Disable a plugin.

        Args:
            plugin_id: The ID of the plugin to disable

        Raises:
            PluginError: If the plugin is not registered or not in the ENABLED state
        """
        plugin = self.get_plugin(plugin_id)
        if plugin.state != PluginState.ENABLED:
            raise PluginError(
                f"Cannot disable plugin {plugin_id}: not in ENABLED state"
            )

        # Disable the plugin
        try:
            plugin.disable()
            logger.info(f"Disabled plugin: {plugin_id}")
        except Exception as e:
            logger.error(f"Failed to disable plugin {plugin_id}: {str(e)}")
            raise

    def unload_plugin(self, plugin_id: str) -> None:
        """Unload a plugin.

        Args:
            plugin_id: The ID of the plugin to unload

        Raises:
            PluginError: If the plugin is not registered or not in the INITIALIZED, DISABLED, or ERROR state
        """
        plugin = self.get_plugin(plugin_id)
        if plugin.state not in [
            PluginState.INITIALIZED,
            PluginState.DISABLED,
            PluginState.ERROR,
        ]:
            raise PluginError(
                f"Cannot unload plugin {plugin_id}: not in INITIALIZED, DISABLED, or ERROR state"
            )

        # Unload the plugin
        try:
            plugin.unload()
            logger.info(f"Unloaded plugin: {plugin_id}")
        except Exception as e:
            logger.error(f"Failed to unload plugin {plugin_id}: {str(e)}")
            raise

        # Unregister the plugin
        self.unregister_plugin(plugin_id)

    def validate_plugin(self, plugin_id: str) -> None:
        """Validate a plugin.

        Args:
            plugin_id: The ID of the plugin to validate

        Raises:
            PluginError: If the plugin is not registered
            ValidationError: If validation fails
        """
        plugin = self.get_plugin(plugin_id)

        # Validate the plugin
        try:
            plugin.validate()
            logger.info(f"Validated plugin: {plugin_id}")
        except ValidationError as e:
            logger.error(f"Plugin {plugin_id} validation failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Failed to validate plugin {plugin_id}: {str(e)}")
            raise ValidationError(f"Plugin validation failed: {str(e)}") from e

    def discover_plugins(self, directory: str) -> List[PluginInfo]:
        """Discover plugins in a directory.

        Args:
            directory: The directory to discover plugins in

        Returns:
            A list of plugin information for discovered plugins
        """
        directory_path = Path(directory)
        if not directory_path.exists() or not directory_path.is_dir():
            logger.warning(f"Plugin directory does not exist: {directory}")
            return []

        # Add the directory to the Python path
        if str(directory_path) not in sys.path:
            sys.path.insert(0, str(directory_path))

        # Add the directory to the plugin directories
        if directory not in self._plugin_directories:
            self._plugin_directories.append(directory)

        # Discover plugins
        plugin_infos = []
        for plugin_dir in directory_path.iterdir():
            if not plugin_dir.is_dir():
                continue

            # Check if the directory contains a plugin.py file
            plugin_file = plugin_dir / "plugin.py"
            if not plugin_file.exists():
                continue

            # Try to load the plugin information
            try:
                module_name = f"{plugin_dir.name}.plugin"
                module = importlib.import_module(module_name)

                # Check if the module has a PLUGIN_INFO attribute
                if not hasattr(module, "PLUGIN_INFO"):
                    logger.warning(
                        f"Plugin module {module_name} does not have a PLUGIN_INFO attribute"
                    )
                    continue

                # Get the plugin information
                plugin_info_dict = getattr(module, "PLUGIN_INFO")
                if not isinstance(plugin_info_dict, dict):
                    logger.warning(
                        f"Plugin module {module_name} PLUGIN_INFO is not a dictionary"
                    )
                    continue

                # Create the plugin information
                plugin_info = PluginInfo.from_dict(plugin_info_dict)
                plugin_info.entry_point = module_name
                plugin_infos.append(plugin_info)
                logger.info(f"Discovered plugin: {plugin_info.get_id()}")
            except Exception as e:
                logger.warning(
                    f"Failed to load plugin information from {plugin_dir}: {str(e)}"
                )

        return plugin_infos

    def load_plugin_from_info(self, plugin_info: PluginInfo, directory: str) -> Plugin:
        """Load a plugin from plugin information.

        Args:
            plugin_info: The plugin information
            directory: The directory to load the plugin from

        Returns:
            The loaded plugin

        Raises:
            PluginError: If the plugin cannot be loaded
        """
        # Check if the plugin is already registered
        plugin_id = plugin_info.get_id()
        if plugin_id in self._plugins:
            return self._plugins[plugin_id]

        # Add the directory to the Python path
        directory_path = Path(directory)
        if str(directory_path) not in sys.path:
            sys.path.insert(0, str(directory_path))

        # Add the directory to the plugin directories
        if directory not in self._plugin_directories:
            self._plugin_directories.append(directory)

        # Load the plugin module
        if not plugin_info.entry_point:
            raise PluginError(f"Plugin {plugin_id} does not have an entry point")

        try:
            module = importlib.import_module(plugin_info.entry_point)
        except ImportError as e:
            raise PluginError(f"Failed to import plugin module: {str(e)}") from e

        # Find the plugin class
        plugin_class = None
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and issubclass(obj, Plugin) and obj is not Plugin:
                plugin_class = obj
                break

        if not plugin_class:
            raise PluginError(
                f"Plugin module {plugin_info.entry_point} does not contain a Plugin class"
            )

        # Create the plugin instance
        try:
            plugin = plugin_class(plugin_info)
        except Exception as e:
            raise PluginError(f"Failed to create plugin instance: {str(e)}") from e

        # Load the plugin
        self.load_plugin(plugin)

        return plugin

    def load_plugins(self, directory: str) -> List[Plugin]:
        """Load plugins from a directory.

        Args:
            directory: The directory to load plugins from

        Returns:
            A list of loaded plugins
        """
        # Discover plugins
        plugin_infos = self.discover_plugins(directory)

        # Load plugins
        plugins = []
        for plugin_info in plugin_infos:
            try:
                plugin = self.load_plugin_from_info(plugin_info, directory)
                plugins.append(plugin)
            except Exception as e:
                logger.error(f"Failed to load plugin {plugin_info.get_id()}: {str(e)}")

        return plugins


# Global plugin manager instance
_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """Get the global plugin manager instance.

    Returns:
        The global plugin manager instance
    """
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager


def set_plugin_manager(plugin_manager: PluginManager) -> None:
    """Set the global plugin manager instance.

    Args:
        plugin_manager: The plugin manager instance to set
    """
    global _plugin_manager
    _plugin_manager = plugin_manager


def register_plugin(plugin: Plugin) -> None:
    """Register a plugin.

    Args:
        plugin: The plugin to register

    Raises:
        PluginError: If a plugin with the same ID is already registered
    """
    plugin_manager = get_plugin_manager()
    plugin_manager.register_plugin(plugin)


def unregister_plugin(plugin_id: str) -> None:
    """Unregister a plugin.

    Args:
        plugin_id: The ID of the plugin to unregister

    Raises:
        PluginError: If the plugin is not registered
    """
    plugin_manager = get_plugin_manager()
    plugin_manager.unregister_plugin(plugin_id)


def get_plugin(plugin_id: str) -> Plugin:
    """Get a plugin.

    Args:
        plugin_id: The ID of the plugin to get

    Returns:
        The plugin

    Raises:
        PluginError: If the plugin is not registered
    """
    plugin_manager = get_plugin_manager()
    return plugin_manager.get_plugin(plugin_id)


def list_plugins() -> List[Plugin]:
    """List all registered plugins.

    Returns:
        A list of all registered plugins
    """
    plugin_manager = get_plugin_manager()
    return plugin_manager.list_plugins()


def load_plugin(plugin: Plugin) -> None:
    """Load a plugin.

    Args:
        plugin: The plugin to load

    Raises:
        PluginError: If the plugin is already loaded
    """
    plugin_manager = get_plugin_manager()
    plugin_manager.load_plugin(plugin)


def initialize_plugin(plugin_id: str) -> None:
    """Initialize a plugin.

    Args:
        plugin_id: The ID of the plugin to initialize

    Raises:
        PluginError: If the plugin is not registered or not in the LOADED state
    """
    plugin_manager = get_plugin_manager()
    plugin_manager.initialize_plugin(plugin_id)


def enable_plugin(plugin_id: str) -> None:
    """Enable a plugin.

    Args:
        plugin_id: The ID of the plugin to enable

    Raises:
        PluginError: If the plugin is not registered or not in the INITIALIZED or DISABLED state
    """
    plugin_manager = get_plugin_manager()
    plugin_manager.enable_plugin(plugin_id)


def disable_plugin(plugin_id: str) -> None:
    """Disable a plugin.

    Args:
        plugin_id: The ID of the plugin to disable

    Raises:
        PluginError: If the plugin is not registered or not in the ENABLED state
    """
    plugin_manager = get_plugin_manager()
    plugin_manager.disable_plugin(plugin_id)


def unload_plugin(plugin_id: str) -> None:
    """Unload a plugin.

    Args:
        plugin_id: The ID of the plugin to unload

    Raises:
        PluginError: If the plugin is not registered or not in the INITIALIZED, DISABLED, or ERROR state
    """
    plugin_manager = get_plugin_manager()
    plugin_manager.unload_plugin(plugin_id)


def validate_plugin(plugin_id: str) -> None:
    """Validate a plugin.

    Args:
        plugin_id: The ID of the plugin to validate

    Raises:
        PluginError: If the plugin is not registered
        ValidationError: If validation fails
    """
    plugin_manager = get_plugin_manager()
    plugin_manager.validate_plugin(plugin_id)


def discover_plugins(directory: str) -> List[PluginInfo]:
    """Discover plugins in a directory.

    Args:
        directory: The directory to discover plugins in

    Returns:
        A list of plugin information for discovered plugins
    """
    plugin_manager = get_plugin_manager()
    return plugin_manager.discover_plugins(directory)


def load_plugin_from_info(plugin_info: PluginInfo, directory: str) -> Plugin:
    """Load a plugin from plugin information.

    Args:
        plugin_info: The plugin information
        directory: The directory to load the plugin from

    Returns:
        The loaded plugin

    Raises:
        PluginError: If the plugin cannot be loaded
    """
    plugin_manager = get_plugin_manager()
    return plugin_manager.load_plugin_from_info(plugin_info, directory)


def load_plugins(directory: str) -> List[Plugin]:
    """Load plugins from a directory.

    Args:
        directory: The directory to load plugins from

    Returns:
        A list of loaded plugins
    """
    plugin_manager = get_plugin_manager()
    return plugin_manager.load_plugins(directory)


__all__ = [
    "PluginError",
    "PluginState",
    "PluginInfo",
    "Plugin",
    "PluginManager",
    "get_plugin_manager",
    "set_plugin_manager",
    "register_plugin",
    "unregister_plugin",
    "get_plugin",
    "list_plugins",
    "load_plugin",
    "initialize_plugin",
    "enable_plugin",
    "disable_plugin",
    "unload_plugin",
    "validate_plugin",
    "discover_plugins",
    "load_plugin_from_info",
    "load_plugins",
]
