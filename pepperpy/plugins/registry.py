"""Plugin registry for PepperPy.

This module provides a centralized registry for all plugins, with support for
lazy loading, dependency resolution, and event-based communication.
"""

import asyncio
import os
import threading
import weakref
from dataclasses import dataclass, field
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    Type,
    TypeVar,
    Union,
)

from pepperpy.core.errors import (
    PluginError,
    PluginNotFoundError,
    ValidationError,
)
from pepperpy.core.logging import get_logger
from pepperpy.plugins.dependencies import (
    DependencyType,
    add_dependency,
    get_load_order,
)
from pepperpy.plugins.dependencies import (
    add_plugin as register_dependency,
)
from pepperpy.plugins.dependencies import (
    is_loaded as is_dependency_loaded,
)
from pepperpy.plugins.dependencies import (
    mark_loaded as mark_dependency_loaded,
)
from pepperpy.plugins.discovery import (
    PluginInfo,
    discover_plugins,
    get_plugin,
    register_scan_path,
)
from pepperpy.plugins.discovery import (
    register_plugin as register_discovered_plugin,
)
from pepperpy.plugins.plugin import PepperpyPlugin
from pepperpy.plugins.state import (
    PluginState,
    set_state,
    verify_state,
)
from pepperpy.plugins.state import (
    has_plugin as has_plugin_state,
)
from pepperpy.plugins.state import (
    register_plugin as register_plugin_state,
)
from pepperpy.plugins.validation import validate_plugin_instance

logger = get_logger(__name__)

# Type variable for plugin classes
T = TypeVar("T", bound=PepperpyPlugin)

# Global registry state
_plugin_registry: Dict[str, Dict[str, Type[PepperpyPlugin]]] = {}
_plugin_metadata: Dict[str, Dict[str, Dict[str, Any]]] = {}
_plugin_paths: Set[str] = set()
_scan_timestamps: Dict[str, float] = {}
_discovery_initialized = False
_plugin_watchers: Dict[str, Any] = {}  # Path to watcher object
_hot_reload_enabled = False
_autodiscovery_enabled = True  # Enable auto-discovery by default

# Mapping of plugin aliases to actual implementations
_plugin_aliases: Dict[str, Dict[str, Union[str, Dict[str, Any]]]] = {
    "llm": {
        "gpt4": "openai:gpt-4",
        "gpt4o": "openrouter:openai/gpt-4o",
        "claude": "anthropic:claude-3-sonnet",
        "llama": "local:llama",
    },
    "embeddings": {
        "ada": "openai:text-embedding-ada-002",
        "e5": "huggingface:e5-large-v2",
    },
}

# Plugin fallback configuration
_plugin_fallbacks: Dict[str, List[str]] = {
    "llm": ["openrouter", "openai", "local"],
    "embeddings": ["openai", "huggingface", "local"],
    "rag": ["memory", "chroma", "faiss"],
}


class PluginSource(Enum):
    """Source of plugin discovery."""

    FILE = "file"  # From filesystem
    PACKAGE = "package"  # From installed package
    REGISTRY = "registry"  # From plugin registry
    DYNAMIC = "dynamic"  # Dynamically registered


@dataclass
class PluginInfo:
    """Information about a plugin."""

    name: str
    version: str
    description: str
    plugin_type: str
    provider_type: str
    author: str = ""
    email: str = ""
    license: str = ""
    source: PluginSource = PluginSource.FILE
    path: Optional[str] = None
    module: Optional[str] = None
    class_name: Optional[str] = None
    requirements: List[str] = field(default_factory=list)
    dependencies: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class PluginError(ValidationError):
    """Error raised when a plugin operation fails."""

    def __init__(
        self,
        message: str,
        plugin_type: Optional[str] = None,
        provider_type: Optional[str] = None,
        cause: Optional[Exception] = None,
    ):
        """Initialize a new plugin error.

        Args:
            message: Error message
            plugin_type: Type of plugin
            provider_type: Type of provider
            cause: Cause of error
        """
        super().__init__(message)
        self.plugin_type = plugin_type
        self.provider_type = provider_type
        self.cause = cause


class RegistryEvent(Enum):
    """Events emitted by the plugin registry."""

    # Plugin registration events
    PLUGIN_REGISTERED = "plugin_registered"
    PLUGIN_UNREGISTERED = "plugin_unregistered"

    # Plugin lifecycle events
    PLUGIN_INITIALIZING = "plugin_initializing"
    PLUGIN_INITIALIZED = "plugin_initialized"
    PLUGIN_INITIALIZATION_FAILED = "plugin_initialization_failed"
    PLUGIN_CLEANUP_STARTED = "plugin_cleanup_started"
    PLUGIN_CLEANUP_COMPLETED = "plugin_cleanup_completed"
    PLUGIN_CLEANUP_FAILED = "plugin_cleanup_failed"

    # Registry lifecycle events
    REGISTRY_INITIALIZING = "registry_initializing"
    REGISTRY_INITIALIZED = "registry_initialized"
    REGISTRY_SHUTTING_DOWN = "registry_shutting_down"
    REGISTRY_SHUTDOWN = "registry_shutdown"


class PluginProxy:
    """Proxy for lazy loading of plugins.

    This class acts as a proxy for plugin instances, loading them only when
    needed and forwarding attribute access to the real instance.
    """

    def __init__(
        self,
        plugin_id: str,
        plugin_type: str,
        provider_type: str,
        registry: "PluginRegistry",
    ):
        """Initialize the plugin proxy.

        Args:
            plugin_id: ID of the plugin
            plugin_type: Type of plugin
            provider_type: Type of provider
            registry: Plugin registry
        """
        self._plugin_id = plugin_id
        self._plugin_type = plugin_type
        self._provider_type = provider_type
        self._registry = weakref.ref(registry)
        self._instance: Optional[PepperpyPlugin] = None

    def __getattr__(self, name: str) -> Any:
        """Forward attribute access to the real plugin instance.

        Args:
            name: Attribute name

        Returns:
            Attribute value

        Raises:
            AttributeError: If the attribute doesn't exist
        """
        # Get the real instance
        instance = self._get_instance()

        # Forward attribute access
        return getattr(instance, name)

    def _get_instance(self) -> PepperpyPlugin:
        """Get the real plugin instance, loading it if needed.

        Returns:
            Plugin instance

        Raises:
            PluginNotFoundError: If the plugin is not found
        """
        if self._instance is None:
            # Get registry
            registry = self._registry()
            if registry is None:
                raise PluginNotFoundError(
                    self._plugin_id,
                    f"{self._plugin_type}/{self._provider_type}",
                    cause=RuntimeError("Plugin registry has been garbage collected"),
                )

            # Load the real instance
            self._instance = registry._load_plugin_instance(
                self._plugin_type, self._provider_type
            )

        return self._instance


class LazyPlugin:
    """Lazy-loaded plugin.

    This class represents a plugin that hasn't been loaded yet, but can be
    loaded on demand when its attributes are accessed.
    """

    def __init__(
        self,
        plugin_type: str,
        provider_type: str,
        plugin_class: Type[PepperpyPlugin],
        registry: "PluginRegistry",
        plugin_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the lazy plugin.

        Args:
            plugin_type: Type of plugin
            provider_type: Type of provider
            plugin_class: Plugin class
            registry: Plugin registry
            plugin_id: Optional plugin ID
            config: Optional plugin configuration
        """
        self.plugin_type = plugin_type
        self.provider_type = provider_type
        self.plugin_class = plugin_class
        self.registry = weakref.ref(registry)
        self.plugin_id = plugin_id or f"{plugin_type}.{provider_type}"
        self.config = config or {}
        self.instance: Optional[PepperpyPlugin] = None

    def __call__(self, *args: Any, **kwargs: Any) -> PepperpyPlugin:
        """Create a plugin instance.

        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Plugin instance
        """
        if self.instance is None:
            # Get registry
            registry = self.registry()
            if registry is None:
                raise RuntimeError("Plugin registry has been garbage collected")

            # Create instance
            self.instance = self.plugin_class(*args, **kwargs)

            # Set plugin ID if not already set
            if not hasattr(self.instance, "plugin_id") or not self.instance.plugin_id:
                self.instance.plugin_id = self.plugin_id

            # Apply configuration
            for key, value in self.config.items():
                setattr(self.instance, key, value)

        return self.instance


class PluginRegistry:
    """Registry for PepperPy plugins.

    This class provides a centralized registry for all plugins, with support for
    lazy loading, dependency resolution, and event-based communication.
    """

    def __init__(self):
        """Initialize the plugin registry."""
        # Plugin registration
        self._plugins: Dict[str, Dict[str, PepperpyPlugin]] = {}
        self._lazy_plugins: Dict[str, Dict[str, LazyPlugin]] = {}
        self._proxies: Dict[str, Dict[str, PluginProxy]] = {}

        # Plugin classes
        self._plugin_classes: Dict[str, Dict[str, Type[PepperpyPlugin]]] = {}

        # Plugin metadata
        self._metadata: Dict[str, Dict[str, Dict[str, Any]]] = {}

        # Event listeners
        self._event_listeners: Dict[RegistryEvent, List[Callable]] = {
            event: [] for event in RegistryEvent
        }

        # Initialization status
        self._initialized = False
        self._initializing = False
        self._shutting_down = False

        # Registry lock
        self._lock = threading.RLock()

        # Auto-initialization
        self._auto_init = True

        # Scan paths and package paths
        self._scan_paths: Set[str] = set()
        self._package_paths: Set[str] = set()

    def register_plugin(
        self,
        plugin_type: str,
        provider_type: str,
        plugin_class: Type[PepperpyPlugin],
        plugin_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        dependencies: Optional[Dict[str, List[str]]] = None,
        lazy: bool = True,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Register a plugin with the registry.

        Args:
            plugin_type: Type of plugin
            provider_type: Type of provider
            plugin_class: Plugin class
            plugin_id: Optional plugin ID
            metadata: Optional plugin metadata
            dependencies: Optional plugin dependencies
            lazy: Whether to lazy-load the plugin
            config: Optional plugin configuration
        """
        plugin_id = plugin_id or f"{plugin_type}.{provider_type}"

        with self._lock:
            # Initialize dictionaries if needed
            if plugin_type not in self._plugin_classes:
                self._plugin_classes[plugin_type] = {}
                self._lazy_plugins[plugin_type] = {}
                self._plugins[plugin_type] = {}
                self._proxies[plugin_type] = {}
                self._metadata[plugin_type] = {}

            # Store plugin class
            self._plugin_classes[plugin_type][provider_type] = plugin_class

            # Create lazy plugin
            lazy_plugin = LazyPlugin(
                plugin_type=plugin_type,
                provider_type=provider_type,
                plugin_class=plugin_class,
                registry=self,
                plugin_id=plugin_id,
                config=config,
            )
            self._lazy_plugins[plugin_type][provider_type] = lazy_plugin

            # Create proxy
            proxy = PluginProxy(
                plugin_id=plugin_id,
                plugin_type=plugin_type,
                provider_type=provider_type,
                registry=self,
            )
            self._proxies[plugin_type][provider_type] = proxy

            # Store metadata
            meta = metadata or {}
            self._metadata[plugin_type][provider_type] = meta

            # Register with discovery system
            register_discovered_plugin(
                plugin_type=plugin_type,
                provider_type=provider_type,
                plugin_class=plugin_class,
                metadata=meta,
            )

            # Register with dependency system
            register_dependency(plugin_id)

            # Register dependencies
            if dependencies:
                for dep_type_str, deps in dependencies.items():
                    try:
                        dep_type = DependencyType(dep_type_str)
                        for dep in deps:
                            dep_parts = dep.split(".")
                            if len(dep_parts) >= 2:
                                dep_plugin_type, dep_provider_type = (
                                    dep_parts[0],
                                    dep_parts[1],
                                )
                                dep_id = f"{dep_plugin_type}.{dep_provider_type}"
                                add_dependency(plugin_id, dep_id, dep_type)
                    except ValueError:
                        logger.warning(f"Invalid dependency type: {dep_type_str}")

        # Emit event
        self._emit_event(
            RegistryEvent.PLUGIN_REGISTERED,
            plugin_id=plugin_id,
            plugin_type=plugin_type,
            provider_type=provider_type,
        )

        logger.debug(f"Registered plugin: {plugin_type}/{provider_type} ({plugin_id})")

    def register_plugin_instance(
        self,
        plugin_type: str,
        provider_type: str,
        instance: PepperpyPlugin,
        metadata: Optional[Dict[str, Any]] = None,
        dependencies: Optional[Dict[str, List[str]]] = None,
    ) -> None:
        """Register a plugin instance with the registry.

        Args:
            plugin_type: Type of plugin
            provider_type: Type of provider
            instance: Plugin instance
            metadata: Optional plugin metadata
            dependencies: Optional plugin dependencies
        """
        with self._lock:
            # Initialize dictionaries if needed
            if plugin_type not in self._plugins:
                self._plugins[plugin_type] = {}
                self._lazy_plugins[plugin_type] = {}
                self._plugin_classes[plugin_type] = {}
                self._proxies[plugin_type] = {}
                self._metadata[plugin_type] = {}

            # Store instance
            self._plugins[plugin_type][provider_type] = instance

            # Store class
            self._plugin_classes[plugin_type][provider_type] = instance.__class__

            # Store metadata
            meta = metadata or {}
            self._metadata[plugin_type][provider_type] = meta

            # Register with state system if not already registered
            if not has_plugin_state(instance.plugin_id):
                register_plugin_state(instance.plugin_id)

            # Register with dependency system
            register_dependency(instance.plugin_id)
            mark_dependency_loaded(instance.plugin_id)

            # Register dependencies
            if dependencies:
                for dep_type_str, deps in dependencies.items():
                    try:
                        dep_type = DependencyType(dep_type_str)
                        for dep in deps:
                            dep_parts = dep.split(".")
                            if len(dep_parts) >= 2:
                                dep_plugin_type, dep_provider_type = (
                                    dep_parts[0],
                                    dep_parts[1],
                                )
                                dep_id = f"{dep_plugin_type}.{dep_provider_type}"
                                add_dependency(instance.plugin_id, dep_id, dep_type)
                    except ValueError:
                        logger.warning(f"Invalid dependency type: {dep_type_str}")

        # Emit event
        self._emit_event(
            RegistryEvent.PLUGIN_REGISTERED,
            plugin_id=instance.plugin_id,
            plugin_type=plugin_type,
            provider_type=provider_type,
        )

        logger.debug(
            f"Registered plugin instance: {plugin_type}/{provider_type} ({instance.plugin_id})"
        )

    def unregister_plugin(self, plugin_type: str, provider_type: str) -> None:
        """Unregister a plugin from the registry.

        Args:
            plugin_type: Type of plugin
            provider_type: Type of provider
        """
        with self._lock:
            # Get plugin ID
            plugin_id = None
            if (
                plugin_type in self._plugins
                and provider_type in self._plugins[plugin_type]
            ):
                plugin_id = self._plugins[plugin_type][provider_type].plugin_id
            elif (
                plugin_type in self._lazy_plugins
                and provider_type in self._lazy_plugins[plugin_type]
            ):
                plugin_id = self._lazy_plugins[plugin_type][provider_type].plugin_id

            # Remove from registry
            if plugin_type in self._plugins:
                self._plugins[plugin_type].pop(provider_type, None)

            if plugin_type in self._lazy_plugins:
                self._lazy_plugins[plugin_type].pop(provider_type, None)

            if plugin_type in self._proxies:
                self._proxies[plugin_type].pop(provider_type, None)

            if plugin_type in self._plugin_classes:
                self._plugin_classes[plugin_type].pop(provider_type, None)

            if plugin_type in self._metadata:
                self._metadata[plugin_type].pop(provider_type, None)

        # Emit event if we have a plugin ID
        if plugin_id:
            self._emit_event(
                RegistryEvent.PLUGIN_UNREGISTERED,
                plugin_id=plugin_id,
                plugin_type=plugin_type,
                provider_type=provider_type,
            )

            logger.debug(
                f"Unregistered plugin: {plugin_type}/{provider_type} ({plugin_id})"
            )

    def get_plugin(
        self, plugin_type: str, provider_type: str, lazy: bool = True
    ) -> Union[PepperpyPlugin, PluginProxy]:
        """Get a plugin from the registry.

        Args:
            plugin_type: Type of plugin
            provider_type: Type of provider
            lazy: Whether to return a lazy-loading proxy or force loading

        Returns:
            Plugin instance or proxy

        Raises:
            PluginNotFoundError: If the plugin is not found
        """
        with self._lock:
            # Check if plugin exists
            if (
                plugin_type not in self._plugin_classes
                or provider_type not in self._plugin_classes[plugin_type]
            ):
                # Auto-initialize if enabled
                if self._auto_init and not self._initialized and not self._initializing:
                    self.discover_plugins()
                    return self.get_plugin(plugin_type, provider_type, lazy)

                # Plugin not found
                raise PluginNotFoundError(
                    f"{plugin_type}.{provider_type}",
                    f"{plugin_type}/{provider_type}",
                )

            # Return existing instance if available
            if (
                plugin_type in self._plugins
                and provider_type in self._plugins[plugin_type]
            ):
                return self._plugins[plugin_type][provider_type]

            # Return proxy if lazy loading is enabled
            if lazy:
                return self._proxies[plugin_type][provider_type]

            # Otherwise, load the plugin
            return self._load_plugin_instance(plugin_type, provider_type)

    def _load_plugin_instance(
        self, plugin_type: str, provider_type: str
    ) -> PepperpyPlugin:
        """Load a plugin instance.

        Args:
            plugin_type: Type of plugin
            provider_type: Type of provider

        Returns:
            Plugin instance

        Raises:
            PluginNotFoundError: If the plugin is not found
        """
        with self._lock:
            # Check if plugin exists
            if (
                plugin_type not in self._lazy_plugins
                or provider_type not in self._lazy_plugins[plugin_type]
            ):
                raise PluginNotFoundError(
                    f"{plugin_type}.{provider_type}",
                    f"{plugin_type}/{provider_type}",
                )

            # Get lazy plugin
            lazy_plugin = self._lazy_plugins[plugin_type][provider_type]

            # Check if already loaded
            if (
                plugin_type in self._plugins
                and provider_type in self._plugins[plugin_type]
            ):
                return self._plugins[plugin_type][provider_type]

            # Load dependencies first
            dependencies = get_load_order([lazy_plugin.plugin_id])
            for dep_id in dependencies:
                if dep_id != lazy_plugin.plugin_id and not is_dependency_loaded(dep_id):
                    # Find dependency plugin
                    dep_parts = dep_id.split(".")
                    if len(dep_parts) >= 2:
                        dep_plugin_type, dep_provider_type = dep_parts[0], dep_parts[1]
                        try:
                            # Attempt to load dependency
                            self._load_plugin_instance(
                                dep_plugin_type, dep_provider_type
                            )
                        except PluginNotFoundError:
                            logger.warning(f"Dependency {dep_id} not found")

            # Create instance
            try:
                instance = lazy_plugin()

                # Store instance
                self._plugins[plugin_type][provider_type] = instance

                # Mark as loaded in dependency system
                mark_dependency_loaded(lazy_plugin.plugin_id)

                # Register with state system if not already registered
                if not has_plugin_state(instance.plugin_id):
                    register_plugin_state(instance.plugin_id)

                # Validate instance
                validate_plugin_instance(instance)

                return instance
            except Exception as e:
                logger.error(
                    f"Error loading plugin {plugin_type}/{provider_type}: {e}",
                    exc_info=True,
                )
                raise PluginNotFoundError(
                    f"{plugin_type}.{provider_type}",
                    f"{plugin_type}/{provider_type}",
                    cause=e,
                )

    def has_plugin(self, plugin_type: str, provider_type: str) -> bool:
        """Check if a plugin exists.

        Args:
            plugin_type: Type of plugin
            provider_type: Type of provider

        Returns:
            True if the plugin exists, False otherwise
        """
        with self._lock:
            return (
                plugin_type in self._plugin_classes
                and provider_type in self._plugin_classes[plugin_type]
            )

    def get_plugin_metadata(
        self, plugin_type: str, provider_type: str
    ) -> Optional[Dict[str, Any]]:
        """Get plugin metadata.

        Args:
            plugin_type: Type of plugin
            provider_type: Type of provider

        Returns:
            Plugin metadata or None if not found
        """
        with self._lock:
            if (
                plugin_type not in self._metadata
                or provider_type not in self._metadata[plugin_type]
            ):
                return None

            return self._metadata[plugin_type][provider_type].copy()

    def get_plugins_by_type(
        self, plugin_type: str, lazy: bool = True
    ) -> Dict[str, Union[PepperpyPlugin, PluginProxy]]:
        """Get all plugins of a specific type.

        Args:
            plugin_type: Type of plugin
            lazy: Whether to return lazy-loading proxies or force loading

        Returns:
            Dictionary of provider types to plugin instances or proxies
        """
        with self._lock:
            result: Dict[str, Union[PepperpyPlugin, PluginProxy]] = {}

            # Check if type exists
            if plugin_type not in self._plugin_classes:
                return result

            # Get all providers
            for provider_type in self._plugin_classes[plugin_type]:
                try:
                    result[provider_type] = self.get_plugin(
                        plugin_type, provider_type, lazy=lazy
                    )
                except Exception as e:
                    logger.warning(
                        f"Error getting plugin {plugin_type}/{provider_type}: {e}"
                    )

            return result

    def get_all_plugins(
        self, lazy: bool = True
    ) -> Dict[str, Dict[str, Union[PepperpyPlugin, PluginProxy]]]:
        """Get all plugins.

        Args:
            lazy: Whether to return lazy-loading proxies or force loading

        Returns:
            Dictionary of plugin types to dictionaries of provider types to plugin instances or proxies
        """
        with self._lock:
            result: Dict[str, Dict[str, Union[PepperpyPlugin, PluginProxy]]] = {}

            # Get all plugin types
            for plugin_type in self._plugin_classes:
                result[plugin_type] = self.get_plugins_by_type(plugin_type, lazy=lazy)

            return result

    def add_event_listener(self, event: RegistryEvent, listener: Callable) -> None:
        """Add an event listener.

        Args:
            event: Event to listen for
            listener: Event listener function
        """
        with self._lock:
            self._event_listeners[event].append(listener)

    def remove_event_listener(self, event: RegistryEvent, listener: Callable) -> None:
        """Remove an event listener.

        Args:
            event: Event to stop listening for
            listener: Event listener function to remove
        """
        with self._lock:
            if listener in self._event_listeners[event]:
                self._event_listeners[event].remove(listener)

    def _emit_event(self, event: RegistryEvent, **kwargs: Any) -> None:
        """Emit an event.

        Args:
            event: Event to emit
            **kwargs: Event data
        """
        with self._lock:
            listeners = self._event_listeners[event].copy()

        # Call listeners outside the lock
        for listener in listeners:
            try:
                listener(event, **kwargs)
            except Exception as e:
                logger.error(f"Error in event listener: {e}")

    def add_scan_path(self, path: str) -> None:
        """Add a path to scan for plugins.

        Args:
            path: Path to scan
        """
        with self._lock:
            self._scan_paths.add(os.path.abspath(path))
            register_scan_path(path)

    def add_package_path(self, package: str) -> None:
        """Add a package to scan for plugins.

        Args:
            package: Package name to scan
        """
        with self._lock:
            self._package_paths.add(package)

    def set_auto_init(self, enabled: bool) -> None:
        """Enable or disable auto-initialization.

        Args:
            enabled: Whether to enable auto-initialization
        """
        with self._lock:
            self._auto_init = enabled

    def discover_plugins(self) -> None:
        """Discover plugins from all sources."""
        if self._initialized:
            return

        with self._lock:
            if self._initializing:
                return

            self._initializing = True

        # Emit event
        self._emit_event(RegistryEvent.REGISTRY_INITIALIZING)

        try:
            logger.debug("Discovering plugins...")

            # Discover plugins
            plugins = discover_plugins()

            # Register discovered plugins
            for plugin_type, providers in plugins.items():
                for provider_type, info in providers.items():
                    plugin_class = info.get_class()
                    if plugin_class is not None:
                        metadata = info.metadata.copy() if info.metadata else {}
                        self.register_plugin(
                            plugin_type=plugin_type,
                            provider_type=provider_type,
                            plugin_class=plugin_class,
                            metadata=metadata,
                            lazy=True,
                        )

            # Mark as initialized
            with self._lock:
                self._initialized = True
                self._initializing = False

            # Emit event
            self._emit_event(RegistryEvent.REGISTRY_INITIALIZED)

            logger.debug("Plugin discovery completed")
        except Exception as e:
            logger.error(f"Error discovering plugins: {e}", exc_info=True)

            # Reset initialization state
            with self._lock:
                self._initializing = False

            # Re-raise exception
            raise

    async def initialize_plugin(
        self,
        plugin_type: str,
        provider_type: str,
        **kwargs: Any,
    ) -> PepperpyPlugin:
        """Initialize a plugin.

        Args:
            plugin_type: Type of plugin
            provider_type: Type of provider
            **kwargs: Initialization parameters

        Returns:
            Initialized plugin instance

        Raises:
            PluginNotFoundError: If the plugin is not found
        """
        # Get plugin instance (force loading)
        instance = self.get_plugin(plugin_type, provider_type, lazy=False)

        # Get plugin ID
        plugin_id = instance.plugin_id

        # Verify state
        verify_state(
            plugin_id,
            [PluginState.REGISTERED, PluginState.INIT_FAILED],
            "initialization",
        )

        # Emit event
        self._emit_event(
            RegistryEvent.PLUGIN_INITIALIZING,
            plugin_id=plugin_id,
            plugin_type=plugin_type,
            provider_type=provider_type,
        )

        try:
            # Initialize plugin
            set_state(plugin_id, PluginState.INITIALIZING)
            await instance.initialize(**kwargs)
            set_state(plugin_id, PluginState.INITIALIZED)

            # Emit event
            self._emit_event(
                RegistryEvent.PLUGIN_INITIALIZED,
                plugin_id=plugin_id,
                plugin_type=plugin_type,
                provider_type=provider_type,
            )

            return instance
        except Exception as e:
            # Set state to initialization failed
            set_state(plugin_id, PluginState.INIT_FAILED, e)

            # Emit event
            self._emit_event(
                RegistryEvent.PLUGIN_INITIALIZATION_FAILED,
                plugin_id=plugin_id,
                plugin_type=plugin_type,
                provider_type=provider_type,
                error=e,
            )

            # Re-raise exception
            raise

    async def cleanup_plugin(
        self,
        plugin_type: str,
        provider_type: str,
        **kwargs: Any,
    ) -> None:
        """Clean up a plugin.

        Args:
            plugin_type: Type of plugin
            provider_type: Type of provider
            **kwargs: Cleanup parameters

        Raises:
            PluginNotFoundError: If the plugin is not found
        """
        # Check if plugin exists and is loaded
        if (
            plugin_type not in self._plugins
            or provider_type not in self._plugins[plugin_type]
        ):
            # Plugin not found or not loaded, nothing to clean up
            return

        # Get plugin instance
        instance = self._plugins[plugin_type][provider_type]

        # Get plugin ID
        plugin_id = instance.plugin_id

        # Verify state
        try:
            verify_state(
                plugin_id,
                [PluginState.INITIALIZED, PluginState.CLEANUP_FAILED],
                "cleanup",
            )
        except PluginError:
            # Plugin is not in a state that requires cleanup
            return

        # Emit event
        self._emit_event(
            RegistryEvent.PLUGIN_CLEANUP_STARTED,
            plugin_id=plugin_id,
            plugin_type=plugin_type,
            provider_type=provider_type,
        )

        try:
            # Clean up plugin
            set_state(plugin_id, PluginState.CLEANING_UP)
            await instance.cleanup(**kwargs)
            set_state(plugin_id, PluginState.CLEANED_UP)

            # Emit event
            self._emit_event(
                RegistryEvent.PLUGIN_CLEANUP_COMPLETED,
                plugin_id=plugin_id,
                plugin_type=plugin_type,
                provider_type=provider_type,
            )
        except Exception as e:
            # Set state to cleanup failed
            set_state(plugin_id, PluginState.CLEANUP_FAILED, e)

            # Emit event
            self._emit_event(
                RegistryEvent.PLUGIN_CLEANUP_FAILED,
                plugin_id=plugin_id,
                plugin_type=plugin_type,
                provider_type=provider_type,
                error=e,
            )

            # Re-raise exception
            raise

    async def initialize_all_plugins(self, **kwargs: Any) -> None:
        """Initialize all registered plugins.

        Args:
            **kwargs: Initialization parameters
        """
        # Discover plugins if not already done
        if not self._initialized:
            self.discover_plugins()

        # Get all plugin types and providers
        plugins = []
        with self._lock:
            for plugin_type, providers in self._lazy_plugins.items():
                for provider_type in providers:
                    plugins.append((plugin_type, provider_type))

        # Initialize plugins
        for plugin_type, provider_type in plugins:
            try:
                await self.initialize_plugin(plugin_type, provider_type, **kwargs)
            except Exception as e:
                logger.error(
                    f"Error initializing plugin {plugin_type}/{provider_type}: {e}",
                    exc_info=True,
                )

    async def cleanup_all_plugins(self, **kwargs: Any) -> None:
        """Clean up all initialized plugins.

        Args:
            **kwargs: Cleanup parameters
        """
        # Emit event
        self._emit_event(RegistryEvent.REGISTRY_SHUTTING_DOWN)

        # Get all loaded plugins
        plugins = []
        with self._lock:
            for plugin_type, providers in self._plugins.items():
                for provider_type in providers:
                    plugins.append((plugin_type, provider_type))

            self._shutting_down = True

        # Clean up plugins in reverse order
        for plugin_type, provider_type in reversed(plugins):
            try:
                await self.cleanup_plugin(plugin_type, provider_type, **kwargs)
            except Exception as e:
                logger.error(
                    f"Error cleaning up plugin {plugin_type}/{provider_type}: {e}",
                    exc_info=True,
                )

        # Emit event
        self._emit_event(RegistryEvent.REGISTRY_SHUTDOWN)

        # Reset registry state
        with self._lock:
            self._shutting_down = False
            self._initialized = False

    def __del__(self):
        """Clean up the registry when it's garbage collected."""
        # Only attempt cleanup if there are plugins registered
        with self._lock:
            if not self._plugins:
                return

        # Run cleanup in a separate thread
        try:
            loop = asyncio.new_event_loop()
            loop.run_until_complete(self.cleanup_all_plugins())
            loop.close()
        except Exception:
            # Ignore exceptions during garbage collection
            pass


# Singleton instance
_registry = PluginRegistry()


# Public API
register_plugin = _registry.register_plugin
register_plugin_instance = _registry.register_plugin_instance
unregister_plugin = _registry.unregister_plugin
get_plugin = _registry.get_plugin
has_plugin = _registry.has_plugin
get_plugin_metadata = _registry.get_plugin_metadata
get_plugins_by_type = _registry.get_plugins_by_type
get_all_plugins = _registry.get_all_plugins
add_event_listener = _registry.add_event_listener
remove_event_listener = _registry.remove_event_listener
add_scan_path = _registry.add_scan_path
add_package_path = _registry.add_package_path
set_auto_init = _registry.set_auto_init
discover_plugins = _registry.discover_plugins
initialize_plugin = _registry.initialize_plugin
cleanup_plugin = _registry.cleanup_plugin
initialize_all_plugins = _registry.initialize_all_plugins
cleanup_all_plugins = _registry.cleanup_all_plugins
