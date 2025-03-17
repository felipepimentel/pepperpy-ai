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

from pepperpy.core.errors import ValidationError
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

    Plugins extend the functionality of the PepperPy framework. They are loaded
    dynamically and can be enabled or disabled at runtime.
    """

    def __init__(self, info: PluginInfo):
        """Initialize the plugin.

        Args:
            info: The plugin information
        """
        self.info = info
        self.state = PluginState.UNLOADED

    def initialize(self) -> None:
        """Initialize the plugin.

        This method is called when the plugin is initialized. It performs common
        initialization tasks and then calls the plugin-specific on_initialize method.
        """
        if self.state != PluginState.LOADED:
            raise ValueError(
                f"Plugin {self.info.name} must be loaded before initializing"
            )

        logger.info(f"Initializing plugin: {self.info.name}")
        try:
            self.on_initialize()
            self.state = PluginState.INITIALIZED
            logger.info(f"Plugin initialized: {self.info.name}")
        except Exception as e:
            self.state = PluginState.ERROR
            logger.error(f"Error initializing plugin {self.info.name}: {str(e)}")
            raise

    def enable(self) -> None:
        """Enable the plugin.

        This method is called when the plugin is enabled. It performs common
        enabling tasks and then calls the plugin-specific on_enable method.
        """
        if self.state != PluginState.INITIALIZED and self.state != PluginState.DISABLED:
            raise ValueError(
                f"Plugin {self.info.name} must be initialized before enabling"
            )

        logger.info(f"Enabling plugin: {self.info.name}")
        try:
            self.on_enable()
            self.state = PluginState.ENABLED
            logger.info(f"Plugin enabled: {self.info.name}")
        except Exception as e:
            self.state = PluginState.ERROR
            logger.error(f"Error enabling plugin {self.info.name}: {str(e)}")
            raise

    def disable(self) -> None:
        """Disable the plugin.

        This method is called when the plugin is disabled. It performs common
        disabling tasks and then calls the plugin-specific on_disable method.
        """
        if self.state != PluginState.ENABLED:
            raise ValueError(
                f"Plugin {self.info.name} must be enabled before disabling"
            )

        logger.info(f"Disabling plugin: {self.info.name}")
        try:
            self.on_disable()
            self.state = PluginState.DISABLED
            logger.info(f"Plugin disabled: {self.info.name}")
        except Exception as e:
            self.state = PluginState.ERROR
            logger.error(f"Error disabling plugin {self.info.name}: {str(e)}")
            raise

    def unload(self) -> None:
        """Unload the plugin.

        This method is called when the plugin is unloaded. It performs common
        unloading tasks and then calls the plugin-specific on_unload method.
        """
        if self.state == PluginState.ENABLED:
            self.disable()

        logger.info(f"Unloading plugin: {self.info.name}")
        try:
            self.on_unload()
            self.state = PluginState.UNLOADED
            logger.info(f"Plugin unloaded: {self.info.name}")
        except Exception as e:
            self.state = PluginState.ERROR
            logger.error(f"Error unloading plugin {self.info.name}: {str(e)}")
            raise

    def validate(self) -> None:
        """Validate the plugin.

        This method is called to validate the plugin configuration and dependencies.
        It performs common validation tasks and then calls the plugin-specific on_validate method.
        """
        logger.debug(f"Validating plugin: {self.info.name}")
        try:
            self.on_validate()
            logger.debug(f"Plugin validated: {self.info.name}")
        except Exception as e:
            logger.error(f"Error validating plugin {self.info.name}: {str(e)}")
            raise

    @abstractmethod
    def on_initialize(self) -> None:
        """Initialize the plugin.

        This method should be implemented by plugin subclasses to perform
        plugin-specific initialization.
        """
        pass

    @abstractmethod
    def on_enable(self) -> None:
        """Enable the plugin.

        This method should be implemented by plugin subclasses to perform
        plugin-specific enabling.
        """
        pass

    @abstractmethod
    def on_disable(self) -> None:
        """Disable the plugin.

        This method should be implemented by plugin subclasses to perform
        plugin-specific disabling.
        """
        pass

    @abstractmethod
    def on_unload(self) -> None:
        """Unload the plugin.

        This method should be implemented by plugin subclasses to perform
        plugin-specific unloading.
        """
        pass

    def on_validate(self) -> None:
        """Validate the plugin.

        This method can be overridden by plugin subclasses to perform
        plugin-specific validation.
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
    """Manager for plugin lifecycle and discovery.

    The plugin manager is responsible for loading, initializing, enabling,
    disabling, and unloading plugins, as well as discovering plugins in a
    directory.
    """

    def __init__(
        self,
        registry_manager: Optional[RegistryManager] = None,
        event_bus: Optional[EventBus] = None,
    ):
        """Initialize the plugin manager.

        Args:
            registry_manager: The registry manager to use
            event_bus: The event bus to use
        """
        self._plugins: Dict[str, Plugin] = {}
        self._registry_manager = registry_manager or get_registry_manager()
        self._event_bus = event_bus or get_event_bus()

        # Create registry for plugins
        if "plugins" not in self._registry_manager.registries:
            self._registry_manager.create_registry("plugins")

    def register_plugin(self, plugin: Plugin) -> None:
        """Register a plugin with the manager.

        Args:
            plugin: The plugin to register
        """
        if plugin.info.name in self._plugins:
            logger.warning(
                f"Plugin {plugin.info.name} is already registered, replacing existing plugin"
            )
            old_plugin = self._plugins[plugin.info.name]
            if old_plugin.state == PluginState.ENABLED:
                old_plugin.disable()
                old_plugin.unload()
            self._plugins[plugin.info.name] = plugin
        else:
            logger.info(f"Registering plugin: {plugin.info.name}")
            self._plugins[plugin.info.name] = plugin

        # Register the plugin with the registry
        self._registry_manager.get_registry("plugins").register(
            plugin.info.get_component_id(),
            plugin,
        )

        # Emit event
        self._event_bus.emit(
            PluginEvent.create(plugin, "registered", {"action": "register"})
        )

    def unregister_plugin(self, plugin_id: str) -> None:
        """Unregister a plugin from the manager.

        Args:
            plugin_id: The ID of the plugin to unregister
        """
        if plugin_id not in self._plugins:
            logger.warning(f"Plugin {plugin_id} is not registered")
            return

        plugin = self._plugins[plugin_id]
        if plugin.state == PluginState.ENABLED:
            plugin.disable()
        if plugin.state != PluginState.UNLOADED:
            plugin.unload()

        # Unregister the plugin from the registry
        self._registry_manager.get_registry("plugins").unregister(
            plugin.info.get_component_id()
        )

        # Remove the plugin from the manager
        del self._plugins[plugin_id]

        # Emit event
        self._event_bus.emit(
            PluginEvent.create(plugin, "unregistered", {"action": "unregister"})
        )

    def get_plugin(self, plugin_id: str) -> Plugin:
        """Get a plugin by its ID.

        Args:
            plugin_id: The ID of the plugin to get

        Returns:
            The plugin with the given ID

        Raises:
            KeyError: If the plugin is not registered
        """
        if plugin_id not in self._plugins:
            raise KeyError(f"Plugin {plugin_id} is not registered")
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
        """
        if plugin.info.name not in self._plugins:
            self.register_plugin(plugin)
        else:
            plugin = self._plugins[plugin.info.name]

        if plugin.state != PluginState.UNLOADED:
            logger.warning(f"Plugin {plugin.info.name} is already loaded")
            return

        logger.info(f"Loading plugin: {plugin.info.name}")

        # Validate the plugin
        plugin.validate()

        # Check dependencies
        for dependency in plugin.info.dependencies:
            if dependency not in self._plugins:
                raise ValueError(
                    f"Plugin {plugin.info.name} depends on plugin {dependency}, which is not registered"
                )
            dependency_plugin = self._plugins[dependency]
            if dependency_plugin.state == PluginState.UNLOADED:
                self.load_plugin(dependency_plugin)

        # Update state
        plugin.state = PluginState.LOADED

        # Emit event
        self._event_bus.emit(PluginEvent.create(plugin, "loaded", {"action": "load"}))

        logger.info(f"Plugin loaded: {plugin.info.name}")

    def initialize_plugin(self, plugin_id: str) -> None:
        """Initialize a plugin.

        Args:
            plugin_id: The ID of the plugin to initialize
        """
        if plugin_id not in self._plugins:
            raise KeyError(f"Plugin {plugin_id} is not registered")

        plugin = self._plugins[plugin_id]

        if plugin.state == PluginState.UNLOADED:
            self.load_plugin(plugin)
        elif plugin.state != PluginState.LOADED:
            logger.warning(
                f"Plugin {plugin_id} is already initialized or in an invalid state: {plugin.state}"
            )
            return

        logger.info(f"Initializing plugin: {plugin_id}")

        # Initialize dependencies
        for dependency in plugin.info.dependencies:
            dependency_plugin = self._plugins[dependency]
            if dependency_plugin.state == PluginState.LOADED:
                self.initialize_plugin(dependency)

        try:
            # Initialize the plugin
            plugin.initialize()

            # Emit event
            self._event_bus.emit(
                PluginEvent.create(plugin, "initialized", {"action": "initialize"})
            )

            logger.info(f"Plugin initialized: {plugin_id}")
        except Exception as e:
            logger.error(f"Error initializing plugin {plugin_id}: {str(e)}")
            raise

    def enable_plugin(self, plugin_id: str) -> None:
        """Enable a plugin.

        Args:
            plugin_id: The ID of the plugin to enable
        """
        if plugin_id not in self._plugins:
            raise KeyError(f"Plugin {plugin_id} is not registered")

        plugin = self._plugins[plugin_id]

        if plugin.state == PluginState.UNLOADED:
            self.load_plugin(plugin)
            self.initialize_plugin(plugin_id)
        elif plugin.state == PluginState.LOADED:
            self.initialize_plugin(plugin_id)
        elif plugin.state == PluginState.ENABLED:
            logger.warning(f"Plugin {plugin_id} is already enabled")
            return
        elif (
            plugin.state != PluginState.INITIALIZED
            and plugin.state != PluginState.DISABLED
        ):
            logger.warning(
                f"Plugin {plugin_id} is in an invalid state for enabling: {plugin.state}"
            )
            return

        logger.info(f"Enabling plugin: {plugin_id}")

        # Enable dependencies
        for dependency in plugin.info.dependencies:
            dependency_plugin = self._plugins[dependency]
            if (
                dependency_plugin.state == PluginState.INITIALIZED
                or dependency_plugin.state == PluginState.DISABLED
            ):
                self.enable_plugin(dependency)

        try:
            # Enable the plugin
            plugin.enable()

            # Emit event
            self._event_bus.emit(
                PluginEvent.create(plugin, "enabled", {"action": "enable"})
            )

            logger.info(f"Plugin enabled: {plugin_id}")
        except Exception as e:
            logger.error(f"Error enabling plugin {plugin_id}: {str(e)}")
            raise

    def disable_plugin(self, plugin_id: str) -> None:
        """Disable a plugin.

        Args:
            plugin_id: The ID of the plugin to disable
        """
        if plugin_id not in self._plugins:
            raise KeyError(f"Plugin {plugin_id} is not registered")

        plugin = self._plugins[plugin_id]

        if plugin.state != PluginState.ENABLED:
            logger.warning(
                f"Plugin {plugin_id} is not enabled, current state: {plugin.state}"
            )
            return

        logger.info(f"Disabling plugin: {plugin_id}")

        # Check if this plugin is a dependency for any enabled plugins
        for other_plugin in self._plugins.values():
            if (
                other_plugin.state == PluginState.ENABLED
                and plugin_id in other_plugin.info.dependencies
            ):
                # Disable dependent plugins first
                logger.info(
                    f"Disabling dependent plugin {other_plugin.info.name} before disabling {plugin_id}"
                )
                self.disable_plugin(other_plugin.info.name)

        try:
            # Disable the plugin
            plugin.disable()

            # Emit event
            self._event_bus.emit(
                PluginEvent.create(plugin, "disabled", {"action": "disable"})
            )

            logger.info(f"Plugin disabled: {plugin_id}")
        except Exception as e:
            logger.error(f"Error disabling plugin {plugin_id}: {str(e)}")
            raise

    def unload_plugin(self, plugin_id: str) -> None:
        """Unload a plugin.

        Args:
            plugin_id: The ID of the plugin to unload
        """
        if plugin_id not in self._plugins:
            raise KeyError(f"Plugin {plugin_id} is not registered")

        plugin = self._plugins[plugin_id]

        if plugin.state == PluginState.UNLOADED:
            logger.warning(f"Plugin {plugin_id} is already unloaded")
            return

        logger.info(f"Unloading plugin: {plugin_id}")

        # Check if this plugin is a dependency for any loaded plugins
        for other_plugin in self._plugins.values():
            if (
                other_plugin.state != PluginState.UNLOADED
                and plugin_id in other_plugin.info.dependencies
            ):
                # Unload dependent plugins first
                logger.info(
                    f"Unloading dependent plugin {other_plugin.info.name} before unloading {plugin_id}"
                )
                self.unload_plugin(other_plugin.info.name)

        try:
            # Unload the plugin
            plugin.unload()

            # Emit event
            self._event_bus.emit(
                PluginEvent.create(plugin, "unloaded", {"action": "unload"})
            )

            logger.info(f"Plugin unloaded: {plugin_id}")
        except Exception as e:
            logger.error(f"Error unloading plugin {plugin_id}: {str(e)}")
            raise

    def validate_plugin(self, plugin_id: str) -> None:
        """Validate a plugin.

        Args:
            plugin_id: The ID of the plugin to validate
        """
        if plugin_id not in self._plugins:
            raise KeyError(f"Plugin {plugin_id} is not registered")

        plugin = self._plugins[plugin_id]

        logger.info(f"Validating plugin: {plugin_id}")

        try:
            # Validate plugin metadata
            if not plugin.info.name:
                raise ValidationError(f"Plugin {plugin_id} has no name")
            if not plugin.info.version:
                raise ValidationError(f"Plugin {plugin_id} has no version")

            # Validate plugin dependencies
            for dependency in plugin.info.dependencies:
                if dependency not in self._plugins:
                    raise ValidationError(
                        f"Plugin {plugin_id} depends on plugin {dependency}, which is not registered"
                    )

            # Run plugin-specific validation
            plugin.validate()

            # Emit event
            self._event_bus.emit(
                PluginEvent.create(plugin, "validated", {"action": "validate"})
            )

            logger.info(f"Plugin validated: {plugin_id}")
        except Exception as e:
            logger.error(f"Error validating plugin {plugin_id}: {str(e)}")
            raise

    def discover_plugins(self, directory: str) -> List[PluginInfo]:
        """Discover plugins in a directory.

        This method searches for plugin metadata files in the specified directory
        and returns a list of plugin information objects.

        Args:
            directory: The directory to search for plugins

        Returns:
            A list of plugin information objects
        """
        logger.info(f"Discovering plugins in directory: {directory}")

        # Convert to Path object
        path = Path(directory)
        if not path.exists() or not path.is_dir():
            logger.warning(f"Plugin directory does not exist: {directory}")
            return []

        # Look for plugin metadata files
        plugin_infos: List[PluginInfo] = []
        for plugin_dir in path.iterdir():
            if not plugin_dir.is_dir():
                continue

            # Check for plugin metadata file
            metadata_file = plugin_dir / "plugin.json"
            if not metadata_file.exists():
                continue

            try:
                # Load plugin metadata
                with open(metadata_file, "r") as f:
                    metadata = json.loads(f.read())

                # Create plugin information
                plugin_info = PluginInfo.from_dict(metadata)

                # Add entry point if present
                entry_point_file = plugin_dir / "plugin.py"
                if entry_point_file.exists():
                    plugin_info.entry_point = str(entry_point_file)

                plugin_infos.append(plugin_info)
                logger.info(f"Discovered plugin: {plugin_info.name}")
            except Exception as e:
                logger.error(
                    f"Error loading plugin metadata from {metadata_file}: {str(e)}"
                )

        return plugin_infos

    def load_plugin_from_info(self, plugin_info: PluginInfo, directory: str) -> Plugin:
        """Load a plugin from plugin information.

        This method loads a plugin based on the provided plugin information.
        It assumes that the plugin module is in the specified directory.

        Args:
            plugin_info: The plugin information
            directory: The directory containing the plugin

        Returns:
            The loaded plugin

        Raises:
            ValueError: If the plugin entry point is not valid
            ImportError: If the plugin module cannot be imported
        """
        logger.info(f"Loading plugin from info: {plugin_info.name}")

        if not plugin_info.entry_point:
            # Try to find the entry point based on the plugin name
            plugin_dir = Path(directory) / plugin_info.name.lower().replace(" ", "_")
            if not plugin_dir.exists() or not plugin_dir.is_dir():
                raise ValueError(f"Plugin directory not found: {plugin_dir}")

            entry_point_file = plugin_dir / "plugin.py"
            if not entry_point_file.exists():
                raise ValueError(f"Plugin entry point not found: {entry_point_file}")

            plugin_info.entry_point = str(entry_point_file)

        # Get the plugin module path
        if not plugin_info.entry_point.endswith(".py"):
            raise ValueError(
                f"Plugin entry point must be a Python file: {plugin_info.entry_point}"
            )

        # Add the directory to the Python path
        if directory not in sys.path:
            sys.path.insert(0, directory)

        # Import the plugin module
        try:
            # Convert file path to module path
            module_path = Path(plugin_info.entry_point)
            if module_path.is_absolute():
                # Make the path relative to the directory
                module_path = module_path.relative_to(Path(directory))

            # Convert to module name
            module_name = str(module_path.with_suffix("")).replace("/", ".")
            module = importlib.import_module(module_name)

            # Find the plugin class
            plugin_class = None
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and issubclass(obj, Plugin) and obj != Plugin:
                    plugin_class = obj
                    break

            if not plugin_class:
                raise ValueError(f"No plugin class found in module {module_name}")

            # Create the plugin instance
            plugin = plugin_class(plugin_info)

            return plugin
        except ImportError as e:
            logger.error(f"Error importing plugin module: {str(e)}")
            raise ImportError(f"Error importing plugin module: {str(e)}") from e
        except Exception as e:
            logger.error(f"Error loading plugin {plugin_info.name}: {str(e)}")
            raise

    def load_plugins(self, directory: str) -> List[Plugin]:
        """Load plugins from a directory.

        This method discovers and loads plugins from the specified directory.

        Args:
            directory: The directory to load plugins from

        Returns:
            A list of loaded plugins
        """
        logger.info(f"Loading plugins from directory: {directory}")

        # Discover plugins
        plugin_infos = self.discover_plugins(directory)

        # Load plugins
        loaded_plugins: List[Plugin] = []
        for plugin_info in plugin_infos:
            try:
                plugin = self.load_plugin_from_info(plugin_info, directory)
                self.register_plugin(plugin)
                self.load_plugin(plugin)
                loaded_plugins.append(plugin)
            except Exception as e:
                logger.error(f"Error loading plugin {plugin_info.name}: {str(e)}")

        return loaded_plugins


# Singleton instance
_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """Get the global plugin manager.

    Returns:
        The global plugin manager
    """
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager


# __all__ defines the public API
__all__ = [
    # Classes
    "Plugin",
    "PluginEvent",
    "PluginInfo",
    "PluginManager",
    "PluginState",
    # Functions
    "get_plugin_manager",
]
