"""PepperPy plugin base class.

This module provides the base plugin class and decorators for PepperPy plugins,
including configuration handling and lifecycle management.
"""

import asyncio
import enum
import os
from collections.abc import Awaitable, Callable
from enum import Enum
from typing import (
    Any,
    ClassVar,
    Generic,
    TypeVar,
)

from pepperpy.core.config_manager import (
    get_plugin_configuration,
    get_provider_api_key,
)
from pepperpy.core.logging import get_logger
from pepperpy.plugins.resources import (
    ResourceType,
    async_scoped_resource,
    cleanup_owner_resources,
    cleanup_resource,
    get_resource,
    get_resource_metadata,
    get_resources_by_owner,
    has_resource,
    register_resource,
    scoped_resource,
    unregister_resource,
)

logger = get_logger(__name__)


# Define event priority enum that can be used even if events module is not available
class EventPriority(enum.IntEnum):
    """Priority for event handlers."""

    HIGHEST = 0
    HIGH = 25
    NORMAL = 50
    LOW = 75
    LOWEST = 100


# Define stub EventContext class that can be used if events module is not available
class EventContext:
    """Context for an event."""

    def __init__(self, event_id="", source="unknown", **kwargs):
        """Initialize event context."""
        self.event_id = event_id
        self.source = source
        self.canceled = False
        self.data = kwargs.get("data", {})
        self.results = {}

    def cancel(self) -> None:
        """Cancel the event."""
        self.canceled = True

    def add_result(self, plugin_id: str, result: Any) -> None:
        """Add a result from a handler."""
        self.results[plugin_id] = result

    def get_result(self, plugin_id: str) -> Any:
        """Get a result from a handler."""
        return self.results.get(plugin_id)


# Try to import real events module
try:
    from .events import CoreEventType, publish, subscribe, unsubscribe, unsubscribe_all
    from .events import EventContext as RealEventContext
    from .events import EventPriority as RealEventPriority

    # Replace stub classes with real ones
    EventContext = RealEventContext
    EventPriority = RealEventPriority
    _has_events = True
except ImportError:
    # Use stub functions if events module is not available
    def publish(*args, **kwargs):
        """Stub for publish."""
        return EventContext()

    def subscribe(*args, **kwargs):
        """Stub for subscribe."""
        pass

    def unsubscribe(*args, **kwargs):
        """Stub for unsubscribe."""
        return False

    def unsubscribe_all(*args, **kwargs):
        """Stub for unsubscribe_all."""
        return 0

    # Define stub CoreEventType
    class CoreEventType(enum.Enum):
        """Core event types (stub)."""

        PLUGIN_INITIALIZED = "core.plugin.initialized"
        PLUGIN_CLEANUP_COMPLETED = "core.plugin.cleanup_completed"

    _has_events = False

try:
    from .resources import (
        ResourceType,
        cleanup_owner_resources,
        cleanup_resource,
        get_resource,
        get_resource_metadata,
        get_resources_by_owner,
        has_resource,
        register_resource,
        unregister_resource,
    )

    _has_resources = True
except ImportError:

    class ResourceType(enum.Enum):
        """Resource type (stub)."""

        CUSTOM = "custom"
        MEMORY = "memory"
        CONNECTION = "connection"
        FILE = "file"

    _has_resources = False

    def register_resource(*args, **kwargs):
        """Stub for register_resource."""
        pass

    def unregister_resource(*args, **kwargs):
        """Stub for unregister_resource."""
        return None

    def get_resource(*args, **kwargs):
        """Stub for get_resource."""
        return None

    def get_resource_metadata(*args, **kwargs):
        """Stub for get_resource_metadata."""
        return {}

    def has_resource(*args, **kwargs):
        """Stub for has_resource."""
        return False

    def get_resources_by_owner(*args, **kwargs):
        """Stub for get_resources_by_owner."""
        return {}

    def cleanup_resource(*args, **kwargs):
        """Stub for cleanup_resource."""
        pass

    def cleanup_owner_resources(*args, **kwargs):
        """Stub for cleanup_owner_resources."""
        pass


try:
    from .state import get_state, set_state

    _has_state = True
except ImportError:
    _has_state = False

    def get_state(*args, **kwargs):
        """Stub for get_state."""
        return None

    def set_state(*args, **kwargs):
        """Stub for set_state."""
        pass


try:
    from pepperpy.core.configuration import (
        get_plugin_configuration,
        get_provider_api_key,
    )

    _has_config = True
except ImportError:
    _has_config = False

    def get_plugin_configuration(*args, **kwargs):
        """Stub for get_plugin_configuration."""
        return {}

    def get_provider_api_key(*args, **kwargs):
        """Stub for get_provider_api_key."""
        return None


# Define dependency type enum
class DependencyType(Enum):
    """Dependency type for plugin dependencies."""

    REQUIRED = "required"
    OPTIONAL = "optional"
    ENHANCES = "enhances"
    CONFLICTS = "conflicts"


# Import dependencies module if available
try:
    from .dependencies import (
        add_dependency,
        check_conflicts,
        check_missing_dependencies,
    )

    _has_dependencies = True
except ImportError:
    _has_dependencies = False

    # Stub functions if not available
    def add_dependency(*args, **kwargs):
        """Stub for add_dependency."""
        pass

    def check_missing_dependencies(*args, **kwargs):
        """Stub for check_missing_dependencies."""
        return []

    def check_conflicts(*args, **kwargs):
        """Stub for check_conflicts."""
        return []


# Global tracking for active plugins and instances in singleton mode
_singleton_instances: dict[str, "PepperpyPlugin"] = {}
_active_plugins: set[str] = set()
_auto_context_enabled = True

# Flag to track if we're inside an async context manager
_inside_context = False
_exiting_plugins: set["PepperpyPlugin"] = set()

T = TypeVar("T", bound="PepperpyPlugin")
EventHandler = Callable[[str, EventContext, Any], Any]
AsyncEventHandler = Callable[[str, EventContext, Any], Awaitable[Any]]


class PluginConfig:
    """Configuration manager for plugins."""

    def __init__(self, plugin_type: str, provider_type: str, **config_kwargs: Any):
        """Initialize plugin configuration.

        Args:
            plugin_type: Type of plugin (e.g., "llm", "rag")
            provider_type: Type of provider (e.g., "openai", "openrouter")
            **config_kwargs: Initial configuration settings
        """
        self.plugin_type = plugin_type
        self.provider_type = provider_type
        self._config = {**config_kwargs}

        # Load from YAML configuration system
        self._load_from_config_system()

    def _load_from_config_system(self) -> None:
        """Load configuration from the YAML configuration system."""
        # Get plugin-specific config directly
        plugin_config = get_plugin_configuration(self.plugin_type, self.provider_type)

        if plugin_config:
            # Apply configuration (don't override explicit config)
            for key, value in plugin_config.items():
                if (
                    key != "key" and key not in self._config
                ):  # Skip key field, handled separately
                    self._config[key] = value
                    logger.debug(
                        f"Loaded config for {self.plugin_type}/{self.provider_type}: {key}={value}"
                    )

        # Get API key if not explicitly provided
        if "api_key" not in self._config:
            api_key = get_provider_api_key(self.plugin_type, self.provider_type)
            if api_key:
                logger.debug(
                    f"Found API key for {self.plugin_type}/{self.provider_type}"
                )
                self._config["api_key"] = api_key

        # Fallback to environment variables for backward compatibility
        if not self._config.get("api_key"):
            self._load_from_environment()

    def _load_from_environment(self) -> None:
        """Load configuration from environment variables (legacy mode)."""
        # Define environment variable prefixes to search in order of priority
        prefixes = [
            f"PEPPERPY_{self.plugin_type.upper()}__{self.provider_type.upper()}_",
            f"PEPPERPY_{self.plugin_type.upper()}__",
            f"{self.provider_type.upper()}_",
        ]

        # Special handling for API key
        if "api_key" not in self._config:
            for prefix in prefixes:
                api_key_var = f"{prefix}API_KEY"
                api_key = os.environ.get(api_key_var)
                if api_key:
                    logger.debug(
                        f"Found API key in environment variable: {api_key_var}"
                    )
                    self._config["api_key"] = api_key
                    break

        # Load all environment variables matching pattern
        for prefix in prefixes:
            for key, value in os.environ.items():
                if key.startswith(prefix):
                    # Extract config key from environment variable name
                    config_key = key[len(prefix) :].lower()
                    # Don't override values explicitly provided
                    if config_key not in self._config:
                        self._config[config_key] = value
                        logger.debug(
                            f"Loaded config from environment: {key} -> {config_key}"
                        )

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key.

        Args:
            key: Configuration key
            default: Default value if key is not found

        Returns:
            Configuration value or default
        """
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set configuration value.

        Args:
            key: Configuration key
            value: Configuration value
        """
        self._config[key] = value

    def update(self, **kwargs: Any) -> None:
        """Update configuration with new values.

        Args:
            **kwargs: New configuration values
        """
        self._config.update(kwargs)

    def as_dict(self) -> dict[str, Any]:
        """Get configuration as dictionary.

        Returns:
            Dictionary of configuration values
        """
        return dict(self._config)

    def with_defaults(self, defaults: dict[str, Any]) -> "PluginConfig":
        """Create new configuration with defaults.

        Args:
            defaults: Default values to use for missing keys

        Returns:
            New configuration instance
        """
        new_config = PluginConfig(self.plugin_type, self.provider_type)
        # Apply defaults first, then override with existing config
        new_config._config = {**defaults, **self._config}
        return new_config


class PepperpyPlugin:
    """Base class for all PepperPy plugins."""

    # Plugin metadata - can be overridden by subclasses
    __metadata__ = {
        "name": "base_plugin",
        "version": "0.1.0",
        "description": "Base plugin class for PepperPy",
        "author": "PepperPy Team",
        "license": "MIT",
    }

    # Singleton mode control
    _singleton_mode: ClassVar[bool] = False

    # Dependencies
    __dependencies__: ClassVar[dict[str, Any]] = {}

    # Event subscriptions - can be overridden by subclasses
    __events__: ClassVar[dict[str, tuple[EventHandler, EventPriority, bool]]] = {}

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize plugin with config.

        Args:
            config: Configuration dictionary
        """
        self._config = config or {}
        self._initialized = False
        self._event_handlers: dict[
            str, list[tuple[EventHandler, EventPriority, bool]]
        ] = {}

        # Plugin ID is used as owner ID for resources
        if not hasattr(self, "plugin_id"):
            self.plugin_id = self.__class__.__name__

        # Register dependencies if the dependencies module is available
        if _has_dependencies:
            self._register_dependencies()

        # Register class-level event handlers
        self._register_class_event_handlers()

    def _register_dependencies(self) -> None:
        """Register plugin dependencies."""
        for dependency_id, dependency_type in self.__class__.__dependencies__.items():
            add_dependency(self.plugin_id, dependency_id, dependency_type)
            logger.debug(f"Registered dependency: {self.plugin_id} -> {dependency_id}")

    def _register_class_event_handlers(self) -> None:
        """Register event handlers defined in __events__ class variable."""
        for event_type, (
            handler,
            priority,
            call_if_canceled,
        ) in self.__class__.__events__.items():
            self.subscribe(event_type, handler, priority, call_if_canceled)

    def check_dependencies(self) -> list[str]:
        """Check if all required dependencies are available.

        Returns:
            List of missing dependencies
        """
        return check_missing_dependencies(self.plugin_id) if _has_dependencies else []

    def check_conflicts(self) -> list[str]:
        """Check if there are any conflicting dependencies.

        Returns:
            List of conflicting dependencies
        """
        return check_conflicts(self.plugin_id) if _has_dependencies else []

    def validate_dependencies(self) -> bool:
        """Validate that all dependencies are met and no conflicts exist.

        Returns:
            True if all dependencies are met and no conflicts exist
        """
        if not _has_dependencies:
            return True

        missing = self.check_dependencies()
        conflicts = self.check_conflicts()

        if missing:
            logger.error(
                f"Plugin {self.plugin_id} has missing dependencies: {', '.join(missing)}"
            )
            return False

        if conflicts:
            logger.error(
                f"Plugin {self.plugin_id} has conflicting dependencies: {', '.join(conflicts)}"
            )
            return False

        return True

    @classmethod
    def depends_on(cls, plugin_id: str, dependency_type: Any = None) -> None:
        """Declare a dependency on another plugin.

        Args:
            plugin_id: ID of the plugin to depend on
            dependency_type: Type of dependency
        """
        if not hasattr(cls, "__dependencies__"):
            cls.__dependencies__ = {}

        if dependency_type is None:
            dependency_type = DependencyType.REQUIRED

        cls.__dependencies__[plugin_id] = dependency_type

    def initialize(self) -> None:
        """Initialize the plugin.

        This method should be called after the plugin is created and
        before it is used. Subclasses should override this method to
        perform any necessary initialization.
        """
        # Check if dependencies are met before initializing
        if not self.validate_dependencies():
            logger.warning(
                f"Initializing plugin {self.plugin_id} with unmet dependencies"
            )

        self._initialized = True

    async def async_initialize(self) -> None:
        """Asynchronously initialize the plugin.

        This method can be used for async initialization tasks.
        By default, it calls the sync initialize method.
        """
        if not self._initialized:
            self.initialize()

    def cleanup(self) -> None:
        """Clean up resources used by the plugin.

        This method should be called when the plugin is no longer needed.
        Subclasses should override this method to release any resources.
        """
        # Unsubscribe from all events
        if _has_events:
            self.unsubscribe_all()

        self._initialized = False

    async def async_cleanup(self) -> None:
        """Asynchronously clean up plugin resources.

        This method is called for async cleanup. By default it calls
        the sync cleanup and then cleans up all registered resources.
        """
        if self._initialized:
            self.cleanup()

        await self.cleanup_all_resources()

    @property
    def initialized(self) -> bool:
        """Check if the plugin is initialized.

        Returns:
            True if the plugin is initialized, False otherwise
        """
        return self._initialized

    def ensure_initialized(self) -> None:
        """Ensure that the plugin is initialized.

        Raises:
            RuntimeError: If the plugin is not initialized
        """
        if not self.initialized:
            raise RuntimeError(f"Plugin {self.__class__.__name__} is not initialized")

    @property
    def config(self) -> dict[str, Any]:
        """Get the plugin configuration.

        Returns:
            Plugin configuration dictionary
        """
        return self._config

    @classmethod
    def get_metadata(cls) -> dict[str, Any]:
        """Get plugin metadata.

        Returns:
            Plugin metadata dictionary
        """
        return cls.__metadata__

    # Resource Management Methods

    def register_resource(
        self,
        resource_key: str,
        resource: Any,
        resource_type: ResourceType | str = ResourceType.CUSTOM,
        cleanup_func: Callable[[Any], None]
        | Callable[[Any], asyncio.Future]
        | None = None,
        metadata: dict[str, Any] | None = None,
        auto_cleanup: bool = True,
    ) -> None:
        """Register a resource associated with this plugin.

        Args:
            resource_key: Unique key for the resource within the plugin's scope
            resource: The resource object
            resource_type: Type of the resource
            cleanup_func: Optional function to call when cleaning up the resource
            metadata: Optional metadata about the resource
            auto_cleanup: Whether to automatically clean up the resource when it's garbage collected

        Raises:
            ResourceAlreadyExistsError: If a resource with the same key already exists for the plugin
        """
        register_resource(
            self.plugin_id,
            resource_key,
            resource,
            resource_type,
            cleanup_func,
            metadata,
            auto_cleanup,
        )
        logger.debug(f"Plugin {self.plugin_id} registered resource: {resource_key}")

    def unregister_resource(self, resource_key: str) -> Any:
        """Unregister a resource without cleaning it up.

        Args:
            resource_key: Unique key for the resource within the plugin's scope

        Returns:
            The resource object

        Raises:
            ResourceNotFoundError: If the resource is not found
        """
        resource = unregister_resource(self.plugin_id, resource_key)
        logger.debug(f"Plugin {self.plugin_id} unregistered resource: {resource_key}")
        return resource

    def get_resource(self, resource_key: str) -> Any:
        """Get a resource.

        Args:
            resource_key: Unique key for the resource within the plugin's scope

        Returns:
            The resource object

        Raises:
            ResourceNotFoundError: If the resource is not found
        """
        return get_resource(self.plugin_id, resource_key)

    def get_resource_metadata(self, resource_key: str) -> dict[str, Any]:
        """Get metadata for a resource.

        Args:
            resource_key: Unique key for the resource within the plugin's scope

        Returns:
            Metadata for the resource

        Raises:
            ResourceNotFoundError: If the resource is not found
        """
        return get_resource_metadata(self.plugin_id, resource_key)

    def has_resource(self, resource_key: str) -> bool:
        """Check if a resource exists.

        Args:
            resource_key: Unique key for the resource within the plugin's scope

        Returns:
            True if the resource exists, False otherwise
        """
        return has_resource(self.plugin_id, resource_key)

    def get_resources(self) -> dict[str, Any]:
        """Get all resources for the plugin.

        Returns:
            Dictionary of resource key to resource object
        """
        return get_resources_by_owner(self.plugin_id)

    async def cleanup_resource(self, resource_key: str) -> None:
        """Clean up a resource.

        Args:
            resource_key: Unique key for the resource within the plugin's scope

        Raises:
            ResourceNotFoundError: If the resource is not found
        """
        await cleanup_resource(self.plugin_id, resource_key)
        logger.debug(f"Plugin {self.plugin_id} cleaned up resource: {resource_key}")

    async def cleanup_all_resources(self) -> None:
        """Clean up all resources for the plugin."""
        await cleanup_owner_resources(self.plugin_id)
        logger.debug(f"Plugin {self.plugin_id} cleaned up all resources")

    def scoped_resource(
        self,
        resource_key: str,
        resource: Any,
        resource_type: ResourceType | str = ResourceType.CUSTOM,
        cleanup_func: Callable[[Any], None]
        | Callable[[Any], asyncio.Future]
        | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        """Context manager for a resource that automatically unregisters when the scope exits.

        Args:
            resource_key: Unique key for the resource within the plugin's scope
            resource: The resource object
            resource_type: Type of the resource
            cleanup_func: Optional function to call when cleaning up the resource
            metadata: Optional metadata about the resource

        Returns:
            Context manager that yields the resource object

        Raises:
            ResourceAlreadyExistsError: If a resource with the same key already exists for the plugin
        """
        return scoped_resource(
            self.plugin_id,
            resource_key,
            resource,
            resource_type,
            cleanup_func,
            metadata,
        )

    def async_scoped_resource(
        self,
        resource_key: str,
        resource: Any,
        resource_type: ResourceType | str = ResourceType.CUSTOM,
        cleanup_func: Callable[[Any], None]
        | Callable[[Any], asyncio.Future]
        | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        """Async context manager for a resource that automatically unregisters when the scope exits.

        Args:
            resource_key: Unique key for the resource within the plugin's scope
            resource: The resource object
            resource_type: Type of the resource
            cleanup_func: Optional function to call when cleaning up the resource
            metadata: Optional metadata about the resource

        Returns:
            Async context manager that yields the resource object

        Raises:
            ResourceAlreadyExistsError: If a resource with the same key already exists for the plugin
        """
        return async_scoped_resource(
            self.plugin_id,
            resource_key,
            resource,
            resource_type,
            cleanup_func,
            metadata,
        )

    # Event System Methods

    def subscribe(
        self,
        event_type: str | Enum,
        handler: EventHandler | AsyncEventHandler,
        priority: EventPriority = EventPriority.NORMAL,
        call_if_canceled: bool = False,
    ) -> None:
        """Subscribe to an event.

        Args:
            event_type: Type of event to subscribe to (string or enum)
            handler: Event handler function (can be sync or async)
            priority: Priority for the handler
            call_if_canceled: Whether to call the handler even if the event is canceled
        """
        if not _has_events:
            logger.warning(
                f"Event system not available, ignoring subscribe for {event_type}"
            )
            return

        # Convert enum to string if needed
        event_type_str = (
            event_type.value if isinstance(event_type, Enum) else event_type
        )

        # Store in local registry for cleanup
        if event_type_str not in self._event_handlers:
            self._event_handlers[event_type_str] = []
        self._event_handlers[event_type_str].append(
            (handler, priority, call_if_canceled)
        )

        # Register with the event system
        _subscribe_event(
            event_type_str, handler, self.plugin_id, priority, call_if_canceled
        )
        logger.debug(f"Plugin {self.plugin_id} subscribed to event: {event_type_str}")

    def unsubscribe(
        self,
        event_type: str | Enum,
        handler: EventHandler | AsyncEventHandler,
    ) -> None:
        """Unsubscribe from an event.

        Args:
            event_type: Type of event to unsubscribe from
            handler: Event handler function to unsubscribe
        """
        if not _has_events:
            return

        # Convert enum to string if needed
        event_type_str = (
            event_type.value if isinstance(event_type, Enum) else event_type
        )

        # Remove from local registry
        if event_type_str in self._event_handlers:
            self._event_handlers[event_type_str] = [
                h for h in self._event_handlers[event_type_str] if h[0] != handler
            ]

        # Unsubscribe from the event system
        _unsubscribe_event(event_type_str, handler, self.plugin_id)
        logger.debug(
            f"Plugin {self.plugin_id} unsubscribed from event: {event_type_str}"
        )

    def unsubscribe_all(self) -> None:
        """Unsubscribe from all events."""
        if not _has_events:
            return

        # Unsubscribe from the event system
        _unsubscribe_all_events(self.plugin_id)

        # Clear local registry
        self._event_handlers.clear()
        logger.debug(f"Plugin {self.plugin_id} unsubscribed from all events")

    async def publish(
        self,
        event_type: str | Enum,
        data: Any | None = None,
        context_data: dict[str, Any] | None = None,
    ) -> EventContext:
        """Publish an event.

        Args:
            event_type: Type of event to publish
            data: Event data
            context_data: Additional context data

        Returns:
            Event context
        """
        if not _has_events:
            logger.warning(
                f"Event system not available, using dummy context for {event_type}"
            )
            return EventContext(source=self.plugin_id, data=context_data or {})

        # Convert enum to string if needed
        event_type_str = (
            event_type.value if isinstance(event_type, Enum) else event_type
        )

        # Create context data if not provided
        if context_data is None:
            context_data = {}

        # Set source to this plugin
        context = await _publish_event(
            event_type_str,
            data,
            self.plugin_id,
            context_data,
        )

        return context

    @classmethod
    def event_handler(
        cls,
        event_type: str | Enum,
        priority: EventPriority = EventPriority.NORMAL,
        call_if_canceled: bool = False,
    ):
        """Decorator to register a method as an event handler.

        Args:
            event_type: Type of event to handle
            priority: Priority for the handler
            call_if_canceled: Whether to call the handler even if the event is canceled

        Returns:
            Decorator function
        """

        def decorator(method):
            # Convert enum to string if needed
            event_type_str = (
                event_type.value if isinstance(event_type, Enum) else event_type
            )

            # Add to class __events__ dict
            if not hasattr(cls, "__events__"):
                cls.__events__ = {}

            cls.__events__[event_type_str] = (method, priority, call_if_canceled)
            return method

        return decorator


class ProviderInterface:
    """Interface for provider plugins.

    Provider plugins are plugins that provide a specific functionality
    to PepperPy, such as text-to-speech, language model integration,
    content generation, etc. This interface defines the common methods
    that all provider plugins must implement.
    """

    def get_provider_type(self) -> str:
        """Get the type of provider.

        Returns:
            Provider type as a string (e.g., "tts", "llm", "content")
        """
        return "unknown"

    def get_provider_id(self) -> str:
        """Get the unique identifier of the provider.

        Returns:
            Provider identifier as a string
        """
        return "unknown"

    def get_capabilities(self) -> dict[str, Any]:
        """Get the capabilities of the provider.

        Returns:
            Dictionary of capability names to their values or descriptions
        """
        return {}


class ProviderPlugin(PepperpyPlugin, ProviderInterface):
    """Base class for provider plugins.

    Provider plugins are plugins that provide a specific functionality
    to PepperPy. This class extends the base plugin class with provider-specific
    functionality.
    """

    __metadata__ = {
        "name": "base_provider",
        "version": "0.1.0",
        "description": "Base provider plugin class for PepperPy",
        "author": "PepperPy Team",
        "license": "MIT",
        "provider_type": "base",
    }

    def get_provider_type(self) -> str:
        """Get the type of provider.

        Returns:
            Provider type as a string from metadata
        """
        return self.__metadata__.get("provider_type", "unknown")

    def get_provider_id(self) -> str:
        """Get the unique identifier of the provider.

        Returns:
            Provider identifier as a string from metadata
        """
        return self.__metadata__.get("name", "unknown")

    def get_capabilities(self) -> dict[str, Any]:
        """Get the capabilities of the provider.

        Returns:
            Empty dictionary by default, should be overridden by subclasses
        """
        return {}


class PluginStateManager(Generic[T]):
    """Manages the state of a plugin between hot reloads.

    This class is used to persist state between hot reloads of a plugin.
    It's particularly useful for plugins that maintain stateful connections
    or resources that shouldn't be recreated on every reload.
    """

    def __init__(self, plugin_id: str):
        """Initialize a new plugin state manager.

        Args:
            plugin_id: Unique identifier for the plugin
        """
        self.plugin_id = plugin_id
        self._state: T | None = None

    def set_state(self, state: T) -> None:
        """Set the state of the plugin.

        Args:
            state: New state to store
        """
        self._state = state

    def get_state(self) -> T | None:
        """Get the state of the plugin.

        Returns:
            Current plugin state, or None if not set
        """
        return self._state

    def clear_state(self) -> None:
        """Clear the plugin state."""
        self._state = None

    @property
    def has_state(self) -> bool:
        """Check if the plugin has state.

        Returns:
            True if the plugin has state, False otherwise
        """
        return self._state is not None


# Global state managers dictionary
_state_managers: dict[str, PluginStateManager[Any]] = {}


def get_state_manager(plugin_id: str) -> PluginStateManager[Any]:
    """Get or create a state manager for a plugin.

    Args:
        plugin_id: Unique identifier for the plugin

    Returns:
        State manager for the plugin
    """
    if plugin_id not in _state_managers:
        _state_managers[plugin_id] = PluginStateManager(plugin_id)

    return _state_managers[plugin_id]
