"""Core functionality for plugin management in PepperPy.

This module provides the core functionality for plugin management in PepperPy,
including plugin discovery, loading, and lifecycle management.
"""

import importlib
import inspect
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, TypeVar

from pepperpy.errors import ValidationError
from pepperpy.events import Event, EventBus, get_event_bus
from pepperpy.registry import ComponentId, RegistryManager, get_registry_manager
from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)

# Type variable for plugin types
T = TypeVar("T")


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

    def get_component_id(self) -> ComponentId:
        """Get the component ID for the plugin.

        Returns:
            The component ID for the plugin
        """
        return ComponentId(
            name=self.name,
            version=self.version,
            namespace="plugins",
        )


class Plugin(ABC):
    """Base class for plugins.

    A plugin is a component that can be loaded and unloaded at runtime to extend
    the functionality of the application.
    """

    def __init__(self, info: PluginInfo):
        """Initialize a plugin.

        Args:
            info: The plugin information
        """
        self.info = info
        self.state = PluginState.UNLOADED
        self.error: Optional[Exception] = None

    def initialize(self) -> None:
        """Initialize the plugin.

        This method is called after the plugin is loaded, but before it is enabled.
        It can be used to set up resources and register components.

        Raises:
            Exception: If initialization fails
        """
        try:
            self.on_initialize()
            self.state = PluginState.INITIALIZED
        except Exception as e:
            self.state = PluginState.ERROR
            self.error = e
            raise

    def enable(self) -> None:
        """Enable the plugin.

        This method is called to enable the plugin. It can be used to start
        background tasks and register event handlers.

        Raises:
            Exception: If enabling fails
        """
        try:
            self.on_enable()
            self.state = PluginState.ENABLED
        except Exception as e:
            self.state = PluginState.ERROR
            self.error = e
            raise

    def disable(self) -> None:
        """Disable the plugin.

        This method is called to disable the plugin. It can be used to stop
        background tasks and unregister event handlers.

        Raises:
            Exception: If disabling fails
        """
        try:
            self.on_disable()
            self.state = PluginState.DISABLED
        except Exception as e:
            self.state = PluginState.ERROR
            self.error = e
            raise

    def unload(self) -> None:
        """Unload the plugin.

        This method is called to unload the plugin. It can be used to clean up
        resources and unregister components.

        Raises:
            Exception: If unloading fails
        """
        try:
            self.on_unload()
            self.state = PluginState.UNLOADED
        except Exception as e:
            self.state = PluginState.ERROR
            self.error = e
            raise

    def validate(self) -> None:
        """Validate the plugin.

        This method is called to validate the plugin. It can be used to check
        if the plugin is compatible with the current environment.

        Raises:
            ValidationError: If validation fails
        """
        self.on_validate()

    @abstractmethod
    def on_initialize(self) -> None:
        """Initialize the plugin.

        This method should be implemented by subclasses to initialize the plugin.
        """
        pass

    @abstractmethod
    def on_enable(self) -> None:
        """Enable the plugin.

        This method should be implemented by subclasses to enable the plugin.
        """
        pass

    @abstractmethod
    def on_disable(self) -> None:
        """Disable the plugin.

        This method should be implemented by subclasses to disable the plugin.
        """
        pass

    @abstractmethod
    def on_unload(self) -> None:
        """Unload the plugin.

        This method should be implemented by subclasses to unload the plugin.
        """
        pass

    def on_validate(self) -> None:
        """Validate the plugin.

        This method can be overridden by subclasses to validate the plugin.
        """
        pass


@dataclass
class PluginEvent(Event[Dict[str, Any]]):
    """Event for plugin lifecycle changes.

    A plugin event is emitted when a plugin's lifecycle state changes, such as
    when it is loaded, initialized, enabled, disabled, or unloaded.
    """

    @classmethod
    def create(
        cls, plugin: Plugin, event_type: str, metadata: Optional[Dict[str, Any]] = None
    ) -> "PluginEvent":
        """Create a plugin event.

        Args:
            plugin: The plugin that the event is for
            event_type: The type of event
            metadata: Additional metadata for the event

        Returns:
            The created plugin event
        """
        return cls(
            event_type=f"plugin.{event_type}",
            data={
                "plugin": plugin.info.to_dict(),
                "state": plugin.state,
            },
            metadata=metadata or {},
        )


class PluginManager:
    """Manager for plugins.

    The plugin manager is responsible for discovering, loading, initializing,
    enabling, disabling, and unloading plugins.
    """

    def __init__(
        self,
        registry_manager: Optional[RegistryManager] = None,
        event_bus: Optional[EventBus] = None,
    ):
        """Initialize a plugin manager.

        Args:
            registry_manager: The registry manager to use
            event_bus: The event bus to use
        """
        self.registry_manager = registry_manager or get_registry_manager()
        self.event_bus = event_bus or get_event_bus()
        self.plugins: Dict[str, Plugin] = {}
        self.plugin_registry = self.registry_manager.get_registry(Plugin)

    def register_plugin(self, plugin: Plugin) -> None:
        """Register a plugin.

        Args:
            plugin: The plugin to register

        Raises:
            ValueError: If a plugin with the same ID is already registered
        """
        plugin_id = str(plugin.info.get_component_id())

        if plugin_id in self.plugins:
            raise ValueError(f"Plugin {plugin_id} is already registered")

        # Register the plugin
        self.plugins[plugin_id] = plugin

        # Register the plugin in the registry
        self.plugin_registry.register(
            component=plugin,
            id=plugin.info.get_component_id(),
            description=plugin.info.description,
            metadata={
                "author": plugin.info.author,
                "tags": plugin.info.tags,
                "entry_point": plugin.info.entry_point,
            },
        )

        # Log the registration
        logger.info(f"Registered plugin {plugin_id}")

    def unregister_plugin(self, plugin_id: str) -> None:
        """Unregister a plugin.

        Args:
            plugin_id: The ID of the plugin to unregister

        Raises:
            ValueError: If the plugin is not registered
        """
        if plugin_id not in self.plugins:
            raise ValueError(f"Plugin {plugin_id} is not registered")

        # Unregister the plugin
        plugin = self.plugins[plugin_id]

        # Unregister the plugin from the registry
        self.plugin_registry.unregister(plugin.info.get_component_id())

        # Remove the plugin from the plugins dictionary
        del self.plugins[plugin_id]

        # Log the unregistration
        logger.info(f"Unregistered plugin {plugin_id}")

    def get_plugin(self, plugin_id: str) -> Plugin:
        """Get a plugin.

        Args:
            plugin_id: The ID of the plugin to get

        Returns:
            The plugin

        Raises:
            ValueError: If the plugin is not registered
        """
        if plugin_id not in self.plugins:
            raise ValueError(f"Plugin {plugin_id} is not registered")

        return self.plugins[plugin_id]

    def list_plugins(self) -> List[Plugin]:
        """List all registered plugins.

        Returns:
            A list of registered plugins
        """
        return list(self.plugins.values())

    def load_plugin(self, plugin: Plugin) -> None:
        """Load a plugin.

        Args:
            plugin: The plugin to load

        Raises:
            ValueError: If the plugin is already loaded
            Exception: If loading fails
        """
        plugin_id = str(plugin.info.get_component_id())

        if plugin.state != PluginState.UNLOADED:
            raise ValueError(f"Plugin {plugin_id} is already loaded")

        try:
            # Register the plugin
            self.register_plugin(plugin)

            # Update the plugin state
            plugin.state = PluginState.LOADED

            # Emit a plugin loaded event
            self.event_bus.emit(PluginEvent.create(plugin, "loaded"))

            # Log the loading
            logger.info(f"Loaded plugin {plugin_id}")
        except Exception as e:
            # Update the plugin state and error
            plugin.state = PluginState.ERROR
            plugin.error = e

            # Emit a plugin error event
            self.event_bus.emit(
                PluginEvent.create(plugin, "error", {"error": str(e), "phase": "load"})
            )

            # Log the error
            logger.error(f"Error loading plugin {plugin_id}: {e}")

            # Re-raise the exception
            raise

    def initialize_plugin(self, plugin_id: str) -> None:
        """Initialize a plugin.

        Args:
            plugin_id: The ID of the plugin to initialize

        Raises:
            ValueError: If the plugin is not registered or not loaded
            Exception: If initialization fails
        """
        if plugin_id not in self.plugins:
            raise ValueError(f"Plugin {plugin_id} is not registered")

        plugin = self.plugins[plugin_id]

        if plugin.state != PluginState.LOADED:
            raise ValueError(f"Plugin {plugin_id} is not loaded")

        try:
            # Initialize the plugin
            plugin.initialize()

            # Emit a plugin initialized event
            self.event_bus.emit(PluginEvent.create(plugin, "initialized"))

            # Log the initialization
            logger.info(f"Initialized plugin {plugin_id}")
        except Exception as e:
            # Update the plugin state and error
            plugin.state = PluginState.ERROR
            plugin.error = e

            # Emit a plugin error event
            self.event_bus.emit(
                PluginEvent.create(
                    plugin, "error", {"error": str(e), "phase": "initialize"}
                )
            )

            # Log the error
            logger.error(f"Error initializing plugin {plugin_id}: {e}")

            # Re-raise the exception
            raise

    def enable_plugin(self, plugin_id: str) -> None:
        """Enable a plugin.

        Args:
            plugin_id: The ID of the plugin to enable

        Raises:
            ValueError: If the plugin is not registered or not initialized
            Exception: If enabling fails
        """
        if plugin_id not in self.plugins:
            raise ValueError(f"Plugin {plugin_id} is not registered")

        plugin = self.plugins[plugin_id]

        if (
            plugin.state != PluginState.INITIALIZED
            and plugin.state != PluginState.DISABLED
        ):
            raise ValueError(f"Plugin {plugin_id} is not initialized or disabled")

        try:
            # Enable the plugin
            plugin.enable()

            # Emit a plugin enabled event
            self.event_bus.emit(PluginEvent.create(plugin, "enabled"))

            # Log the enabling
            logger.info(f"Enabled plugin {plugin_id}")
        except Exception as e:
            # Update the plugin state and error
            plugin.state = PluginState.ERROR
            plugin.error = e

            # Emit a plugin error event
            self.event_bus.emit(
                PluginEvent.create(
                    plugin, "error", {"error": str(e), "phase": "enable"}
                )
            )

            # Log the error
            logger.error(f"Error enabling plugin {plugin_id}: {e}")

            # Re-raise the exception
            raise

    def disable_plugin(self, plugin_id: str) -> None:
        """Disable a plugin.

        Args:
            plugin_id: The ID of the plugin to disable

        Raises:
            ValueError: If the plugin is not registered or not enabled
            Exception: If disabling fails
        """
        if plugin_id not in self.plugins:
            raise ValueError(f"Plugin {plugin_id} is not registered")

        plugin = self.plugins[plugin_id]

        if plugin.state != PluginState.ENABLED:
            raise ValueError(f"Plugin {plugin_id} is not enabled")

        try:
            # Disable the plugin
            plugin.disable()

            # Emit a plugin disabled event
            self.event_bus.emit(PluginEvent.create(plugin, "disabled"))

            # Log the disabling
            logger.info(f"Disabled plugin {plugin_id}")
        except Exception as e:
            # Update the plugin state and error
            plugin.state = PluginState.ERROR
            plugin.error = e

            # Emit a plugin error event
            self.event_bus.emit(
                PluginEvent.create(
                    plugin, "error", {"error": str(e), "phase": "disable"}
                )
            )

            # Log the error
            logger.error(f"Error disabling plugin {plugin_id}: {e}")

            # Re-raise the exception
            raise

    def unload_plugin(self, plugin_id: str) -> None:
        """Unload a plugin.

        Args:
            plugin_id: The ID of the plugin to unload

        Raises:
            ValueError: If the plugin is not registered or not disabled
            Exception: If unloading fails
        """
        if plugin_id not in self.plugins:
            raise ValueError(f"Plugin {plugin_id} is not registered")

        plugin = self.plugins[plugin_id]

        if plugin.state != PluginState.DISABLED and plugin.state != PluginState.LOADED:
            raise ValueError(f"Plugin {plugin_id} is not disabled or loaded")

        try:
            # Unload the plugin
            plugin.unload()

            # Emit a plugin unloaded event
            self.event_bus.emit(PluginEvent.create(plugin, "unloaded"))

            # Unregister the plugin
            self.unregister_plugin(plugin_id)

            # Log the unloading
            logger.info(f"Unloaded plugin {plugin_id}")
        except Exception as e:
            # Update the plugin state and error
            plugin.state = PluginState.ERROR
            plugin.error = e

            # Emit a plugin error event
            self.event_bus.emit(
                PluginEvent.create(
                    plugin, "error", {"error": str(e), "phase": "unload"}
                )
            )

            # Log the error
            logger.error(f"Error unloading plugin {plugin_id}: {e}")

            # Re-raise the exception
            raise

    def validate_plugin(self, plugin_id: str) -> None:
        """Validate a plugin.

        Args:
            plugin_id: The ID of the plugin to validate

        Raises:
            ValueError: If the plugin is not registered
            ValidationError: If validation fails
        """
        if plugin_id not in self.plugins:
            raise ValueError(f"Plugin {plugin_id} is not registered")

        plugin = self.plugins[plugin_id]

        try:
            # Validate the plugin
            plugin.validate()

            # Emit a plugin validated event
            self.event_bus.emit(PluginEvent.create(plugin, "validated"))

            # Log the validation
            logger.info(f"Validated plugin {plugin_id}")
        except ValidationError as e:
            # Update the plugin state and error
            plugin.state = PluginState.ERROR
            plugin.error = e

            # Emit a plugin error event
            self.event_bus.emit(
                PluginEvent.create(
                    plugin, "error", {"error": str(e), "phase": "validate"}
                )
            )

            # Log the error
            logger.error(f"Error validating plugin {plugin_id}: {e}")

            # Re-raise the exception
            raise

    def discover_plugins(self, directory: str) -> List[PluginInfo]:
        """Discover plugins in a directory.

        Args:
            directory: The directory to search for plugins

        Returns:
            A list of plugin information for discovered plugins
        """
        # Get the absolute path of the directory
        directory_path = Path(directory).resolve()

        # Check if the directory exists
        if not directory_path.exists():
            logger.warning(f"Plugin directory {directory_path} does not exist")
            return []

        # Check if the directory is a directory
        if not directory_path.is_dir():
            logger.warning(f"Plugin directory {directory_path} is not a directory")
            return []

        # Find plugin directories
        plugin_infos = []

        for path in directory_path.iterdir():
            # Check if the path is a directory
            if not path.is_dir():
                continue

            # Check if the directory contains a plugin.json file
            plugin_json_path = path / "plugin.json"
            if not plugin_json_path.exists():
                continue

            try:
                # Load the plugin.json file
                with open(plugin_json_path, "r") as f:
                    plugin_data = json.load(f)

                # Create plugin information
                plugin_info = PluginInfo.from_dict(plugin_data)

                # Add the plugin information to the list
                plugin_infos.append(plugin_info)

                # Log the discovery
                logger.info(
                    f"Discovered plugin {plugin_info.name} {plugin_info.version}"
                )
            except Exception as e:
                # Log the error
                logger.error(f"Error loading plugin.json from {plugin_json_path}: {e}")

        return plugin_infos

    def load_plugin_from_info(self, plugin_info: PluginInfo, directory: str) -> Plugin:
        """Load a plugin from plugin information.

        Args:
            plugin_info: The plugin information
            directory: The directory containing the plugin

        Returns:
            The loaded plugin

        Raises:
            ImportError: If the plugin module cannot be imported
            AttributeError: If the plugin class cannot be found
            Exception: If loading fails
        """
        # Get the absolute path of the directory
        directory_path = Path(directory).resolve()

        # Check if the directory exists
        if not directory_path.exists():
            raise ValueError(f"Plugin directory {directory_path} does not exist")

        # Check if the directory is a directory
        if not directory_path.is_dir():
            raise ValueError(f"Plugin directory {directory_path} is not a directory")

        # Get the plugin directory
        plugin_directory = directory_path / plugin_info.name

        # Check if the plugin directory exists
        if not plugin_directory.exists():
            raise ValueError(f"Plugin directory {plugin_directory} does not exist")

        # Check if the plugin directory is a directory
        if not plugin_directory.is_dir():
            raise ValueError(f"Plugin directory {plugin_directory} is not a directory")

        # Get the entry point
        entry_point = plugin_info.entry_point
        if not entry_point:
            entry_point = f"{plugin_info.name}.plugin"

        try:
            # Add the plugin directory to the Python path
            sys.path.insert(0, str(directory_path))

            # Import the plugin module
            module = importlib.import_module(entry_point)

            # Find the plugin class
            plugin_class = None
            for name, obj in inspect.getmembers(module):
                if (
                    inspect.isclass(obj)
                    and issubclass(obj, Plugin)
                    and obj is not Plugin
                ):
                    plugin_class = obj
                    break

            if not plugin_class:
                raise AttributeError(f"Plugin class not found in module {entry_point}")

            # Create the plugin
            plugin = plugin_class(plugin_info)

            # Load the plugin
            self.load_plugin(plugin)

            return plugin
        finally:
            # Remove the plugin directory from the Python path
            if str(directory_path) in sys.path:
                sys.path.remove(str(directory_path))

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
                # Load the plugin
                plugin = self.load_plugin_from_info(plugin_info, directory)

                # Add the plugin to the list
                plugins.append(plugin)
            except Exception as e:
                # Log the error
                logger.error(
                    f"Error loading plugin {plugin_info.name} {plugin_info.version}: {e}"
                )

        return plugins


# Global plugin manager
_plugin_manager = PluginManager()


def get_plugin_manager() -> PluginManager:
    """Get the global plugin manager.

    Returns:
        The global plugin manager
    """
    return _plugin_manager
