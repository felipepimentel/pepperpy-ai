"""Integration module for the PepperPy plugin system.

This module provides integration between the various components of the PepperPy plugin
system, including events, resources, state management, and validation.
"""

import importlib.util
import inspect
from typing import Any

from pepperpy.core.errors import PluginError
from pepperpy.core.logging import get_logger
from pepperpy.plugins import events
from pepperpy.plugins.discovery import (
    discover_plugins,
    register_scan_path,
)
from pepperpy.plugins.resources import (
    ResourceError,
    get_resources_by_owner,
    unregister_resource,
)
from pepperpy.plugins.state import PluginState
from pepperpy.plugins.validation import validate_plugin_instance

logger = get_logger(__name__)


class IntegrationError(PluginError):
    """Error raised during plugin integration."""

    pass


class PluginEventHandler:
    """Handler for plugin-related events."""

    def __init__(self, core_id: str = "core"):
        """Initialize the event handler.

        Args:
            core_id: ID of the core system (default: "core")
        """
        self.core_id = core_id

        # Register for events
        self._register_event_handlers()

    def _register_event_handlers(self) -> None:
        """Register event handlers."""
        # Plugin lifecycle events
        events.subscribe(
            events.CoreEventType.PLUGIN_REGISTERED,
            self._handle_plugin_registered,
            self.core_id,
            events.EventPriority.HIGHEST,
        )
        events.subscribe(
            events.CoreEventType.PLUGIN_UNREGISTERED,
            self._handle_plugin_unregistered,
            self.core_id,
            events.EventPriority.HIGHEST,
        )
        events.subscribe(
            events.CoreEventType.PLUGIN_INITIALIZED,
            self._handle_plugin_initialized,
            self.core_id,
            events.EventPriority.HIGHEST,
        )
        events.subscribe(
            events.CoreEventType.PLUGIN_CLEANUP_COMPLETED,
            self._handle_plugin_cleanup_completed,
            self.core_id,
            events.EventPriority.HIGHEST,
        )

        # Resource events
        events.subscribe(
            events.CoreEventType.RESOURCE_REGISTERED,
            self._handle_resource_registered,
            self.core_id,
            events.EventPriority.HIGHEST,
        )
        events.subscribe(
            events.CoreEventType.RESOURCE_UNREGISTERED,
            self._handle_resource_unregistered,
            self.core_id,
            events.EventPriority.HIGHEST,
        )

    def _handle_plugin_registered(
        self, event_type: str, context: events.EventContext, data: Any
    ) -> None:
        """Handle plugin registered event.

        Args:
            event_type: Type of event
            context: Event context
            data: Plugin instance
        """
        plugin = data
        logger.info(f"Plugin registered: {plugin.plugin_id}")

        # Validate plugin
        try:
            validate_plugin_instance(plugin)
        except Exception as e:
            logger.error(f"Plugin validation failed: {e}")
            # Emit initialization failed event
            events.publish(
                events.CoreEventType.PLUGIN_INITIALIZATION_FAILED,
                self.core_id,
                plugin,
            )
            return

        # Emit initializing event
        events.publish(
            events.CoreEventType.PLUGIN_INITIALIZING,
            self.core_id,
            plugin,
        )

    def _handle_plugin_unregistered(
        self, event_type: str, context: events.EventContext, data: Any
    ) -> None:
        """Handle plugin unregistered event.

        Args:
            event_type: Type of event
            context: Event context
            data: Plugin instance
        """
        plugin = data
        logger.info(f"Plugin unregistered: {plugin.plugin_id}")

        # Unsubscribe from all events
        count = events.unsubscribe_all(plugin.plugin_id)
        logger.debug(f"Unsubscribed from {count} events: {plugin.plugin_id}")

        # Cleanup resources
        self._cleanup_plugin_resources(plugin)

    def _handle_plugin_initialized(
        self, event_type: str, context: events.EventContext, data: Any
    ) -> None:
        """Handle plugin initialized event.

        Args:
            event_type: Type of event
            context: Event context
            data: Plugin instance
        """
        plugin = data
        logger.info(f"Plugin initialized: {plugin.plugin_id}")

    def _handle_plugin_cleanup_completed(
        self, event_type: str, context: events.EventContext, data: Any
    ) -> None:
        """Handle plugin cleanup completed event.

        Args:
            event_type: Type of event
            context: Event context
            data: Plugin instance
        """
        plugin = data
        logger.info(f"Plugin cleanup completed: {plugin.plugin_id}")

    def _handle_resource_registered(
        self, event_type: str, context: events.EventContext, data: Any
    ) -> None:
        """Handle resource registered event.

        Args:
            event_type: Type of event
            context: Event context
            data: Resource data (dict with plugin_id, resource_id, and resource)
        """
        resource_data = data
        logger.debug(
            f"Resource registered: {resource_data['resource_id']} "
            f"(plugin: {resource_data['plugin_id']})"
        )

    def _handle_resource_unregistered(
        self, event_type: str, context: events.EventContext, data: Any
    ) -> None:
        """Handle resource unregistered event.

        Args:
            event_type: Type of event
            context: Event context
            data: Resource data (dict with plugin_id and resource_id)
        """
        resource_data = data
        logger.debug(
            f"Resource unregistered: {resource_data['resource_id']} "
            f"(plugin: {resource_data['plugin_id']})"
        )

    def _cleanup_plugin_resources(self, plugin: Any) -> None:
        """Clean up resources for a plugin.

        Args:
            plugin: Plugin instance
        """
        # Emit cleanup started event
        events.publish(
            events.CoreEventType.PLUGIN_CLEANUP_STARTED,
            self.core_id,
            plugin,
        )

        try:
            # Get resources for plugin
            resources = get_resources_by_owner(plugin.plugin_id)
            for resource_id in resources.keys():
                try:
                    # Emit resource cleanup started event
                    events.publish(
                        events.CoreEventType.RESOURCE_CLEANUP_STARTED,
                        self.core_id,
                        {"plugin_id": plugin.plugin_id, "resource_id": resource_id},
                    )

                    # Clean up resource
                    unregister_resource(plugin.plugin_id, resource_id)

                    # Emit resource cleanup completed event
                    events.publish(
                        events.CoreEventType.RESOURCE_CLEANUP_COMPLETED,
                        self.core_id,
                        {"plugin_id": plugin.plugin_id, "resource_id": resource_id},
                    )
                except ResourceError as e:
                    logger.error(
                        f"Error cleaning up resource {resource_id} for plugin {plugin.plugin_id}: {e}"
                    )
                    # Emit resource cleanup failed event
                    events.publish(
                        events.CoreEventType.RESOURCE_CLEANUP_FAILED,
                        self.core_id,
                        {
                            "plugin_id": plugin.plugin_id,
                            "resource_id": resource_id,
                            "error": str(e),
                        },
                    )

            # Emit cleanup completed event
            events.publish(
                events.CoreEventType.PLUGIN_CLEANUP_COMPLETED,
                self.core_id,
                plugin,
            )
        except Exception as e:
            logger.error(f"Error cleaning up plugin {plugin.plugin_id}: {e}")
            # Emit cleanup failed event
            events.publish(
                events.CoreEventType.PLUGIN_CLEANUP_FAILED,
                self.core_id,
                {"plugin": plugin, "error": str(e)},
            )


# Function to import plugin module
def import_plugin(path: str) -> Any:
    """Import a plugin module.

    Args:
        path: Path to the plugin module

    Returns:
        Imported module

    Raises:
        ImportError: If the plugin cannot be imported
    """
    if not path.endswith(".py"):
        path = f"{path}.py"

    try:
        module_name = path.replace("/", ".").replace("\\", ".").rstrip(".py")
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load spec for {path}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        raise ImportError(f"Error importing plugin from {path}: {e}") from e


class PluginManager:
    """Manager for PepperPy plugins.

    This class provides a centralized management system for plugins, handling
    discovery, registration, initialization, and cleanup.
    """

    def __init__(self, core_id: str = "core"):
        """Initialize the plugin manager.

        Args:
            core_id: ID of the core system (default: "core")
        """
        self.core_id = core_id

        # Plugin storage
        self._plugins: dict[str, Any] = {}

        # Plugin event handler
        self._event_handler = PluginEventHandler(core_id)

        # State manager is not used directly in this implementation
        self._state_manager = None

    def discover_and_register_plugins(
        self, directories: list[str] | None = None
    ) -> list[str]:
        """Discover and register plugins.

        Args:
            directories: Directories to search for plugins (default: None)

        Returns:
            List of plugin IDs that were registered
        """
        # Add scan paths if provided
        if directories:
            for directory in directories:
                register_scan_path(directory)

        # Discover plugins
        plugin_infos = discover_plugins()
        plugin_paths = []

        # Extract paths from discovered plugins
        for plugin_type, providers in plugin_infos.items():
            for provider_info in providers.values():
                if provider_info.path:
                    plugin_paths.append(provider_info.path)

        # Import and register plugins
        registered_ids = []
        for path in plugin_paths:
            try:
                # Import plugin
                plugin_module = import_plugin(path)

                # Check for plugin class
                for name, obj in inspect.getmembers(plugin_module):
                    if inspect.isclass(obj) and hasattr(obj, "plugin_id"):
                        try:
                            # Create plugin instance
                            plugin = obj()

                            # Register plugin
                            self.register_plugin(plugin)

                            # Add to registered IDs
                            registered_ids.append(plugin.plugin_id)

                            # Break after first plugin found
                            break
                        except Exception as e:
                            logger.error(
                                f"Error instantiating plugin class {name}: {e}"
                            )
            except ImportError as e:
                logger.error(f"Error importing plugin from {path}: {e}")

        return registered_ids

    def register_plugin(self, plugin: Any) -> None:
        """Register a plugin.

        Args:
            plugin: Plugin instance

        Raises:
            IntegrationError: If the plugin is already registered
        """
        # Check if plugin is already registered
        if plugin.plugin_id in self._plugins:
            raise IntegrationError(f"Plugin already registered: {plugin.plugin_id}")

        # Add to plugins
        self._plugins[plugin.plugin_id] = plugin

        # Emit registered event
        events.publish(
            events.CoreEventType.PLUGIN_REGISTERED,
            self.core_id,
            plugin,
        )

    def unregister_plugin(self, plugin_id: str) -> None:
        """Unregister a plugin.

        Args:
            plugin_id: ID of the plugin to unregister

        Raises:
            IntegrationError: If the plugin is not registered
        """
        # Check if plugin is registered
        if plugin_id not in self._plugins:
            raise IntegrationError(f"Plugin not registered: {plugin_id}")

        # Get plugin
        plugin = self._plugins[plugin_id]

        # Remove from plugins
        del self._plugins[plugin_id]

        # Emit unregistered event
        events.publish(
            events.CoreEventType.PLUGIN_UNREGISTERED,
            self.core_id,
            plugin,
        )

    def initialize_plugin(self, plugin_id: str) -> None:
        """Initialize a plugin.

        Args:
            plugin_id: ID of the plugin to initialize

        Raises:
            IntegrationError: If the plugin is not registered or already initialized
        """
        # Check if plugin is registered
        if plugin_id not in self._plugins:
            raise IntegrationError(f"Plugin not registered: {plugin_id}")

        # Get plugin
        plugin = self._plugins[plugin_id]

        # Initialize plugin
        try:
            # Call initialize method
            plugin.initialize()

            # Emit initialized event
            events.publish(
                events.CoreEventType.PLUGIN_INITIALIZED,
                self.core_id,
                plugin,
            )
        except Exception as e:
            logger.error(f"Error initializing plugin {plugin_id}: {e}")

            # Emit initialization failed event
            events.publish(
                events.CoreEventType.PLUGIN_INITIALIZATION_FAILED,
                self.core_id,
                {"plugin": plugin, "error": str(e)},
            )

            # Re-raise as integration error
            raise IntegrationError(f"Plugin initialization failed: {e}") from e

    def initialize_all_plugins(self) -> dict[str, bool]:
        """Initialize all registered plugins.

        Returns:
            Dictionary of plugin IDs to initialization success status
        """
        results = {}

        # Initialize plugins
        for plugin_id in self._plugins:
            try:
                self.initialize_plugin(plugin_id)
                results[plugin_id] = True
            except Exception:
                results[plugin_id] = False

        return results

    def cleanup_plugin(self, plugin_id: str) -> None:
        """Clean up a plugin.

        Args:
            plugin_id: ID of the plugin to clean up

        Raises:
            IntegrationError: If the plugin is not registered
        """
        # Check if plugin is registered
        if plugin_id not in self._plugins:
            raise IntegrationError(f"Plugin not registered: {plugin_id}")

        # Get plugin
        plugin = self._plugins[plugin_id]

        # Emit cleanup started event
        events.publish(
            events.CoreEventType.PLUGIN_CLEANUP_STARTED,
            self.core_id,
            plugin,
        )

        try:
            # Call cleanup method
            plugin.cleanup()

            # Emit cleanup completed event
            events.publish(
                events.CoreEventType.PLUGIN_CLEANUP_COMPLETED,
                self.core_id,
                plugin,
            )
        except Exception as e:
            logger.error(f"Error cleaning up plugin {plugin_id}: {e}")

            # Emit cleanup failed event
            events.publish(
                events.CoreEventType.PLUGIN_CLEANUP_FAILED,
                self.core_id,
                {"plugin": plugin, "error": str(e)},
            )

            # Re-raise as integration error
            raise IntegrationError(f"Plugin cleanup failed: {e}") from e

    def cleanup_all_plugins(self) -> dict[str, bool]:
        """Clean up all registered plugins.

        Returns:
            Dictionary of plugin IDs to cleanup success status
        """
        results = {}

        # Cleanup plugins
        for plugin_id in self._plugins:
            try:
                self.cleanup_plugin(plugin_id)
                results[plugin_id] = True
            except Exception:
                results[plugin_id] = False

        return results

    def get_plugin(self, plugin_id: str) -> Any:
        """Get a plugin.

        Args:
            plugin_id: ID of the plugin to get

        Returns:
            Plugin instance

        Raises:
            IntegrationError: If the plugin is not registered
        """
        # Check if plugin is registered
        if plugin_id not in self._plugins:
            raise IntegrationError(f"Plugin not registered: {plugin_id}")

        return self._plugins[plugin_id]

    def get_plugins(self) -> dict[str, Any]:
        """Get all plugins.

        Returns:
            Dictionary of plugin IDs to plugin instances
        """
        return self._plugins.copy()

    def get_plugin_state(self, plugin_id: str) -> PluginState | None:
        """Get the state of a plugin.

        Args:
            plugin_id: ID of the plugin to get state for

        Returns:
            Plugin state, or None if the plugin is not tracked

        Raises:
            IntegrationError: If the plugin is not registered
        """
        # Check if plugin is registered
        if plugin_id not in self._plugins:
            raise IntegrationError(f"Plugin not registered: {plugin_id}")

        return None

    def get_all_plugin_states(self) -> dict[str, PluginState | None]:
        """Get the states of all plugins.

        Returns:
            Dictionary of plugin IDs to plugin states
        """
        states = {}

        # Get states
        for plugin_id in self._plugins:
            states[plugin_id] = None

        return states


# Singleton instance
_plugin_manager = PluginManager()


# Public API
def discover_and_register_plugins(directories: list[str] | None = None) -> list[str]:
    """Discover and register plugins.

    Args:
        directories: Directories to search for plugins (default: None)

    Returns:
        List of plugin IDs that were registered
    """
    return _plugin_manager.discover_and_register_plugins(directories)


def register_plugin(plugin: Any) -> None:
    """Register a plugin.

    Args:
        plugin: Plugin instance

    Raises:
        IntegrationError: If the plugin is already registered
    """
    _plugin_manager.register_plugin(plugin)


def unregister_plugin(plugin_id: str) -> None:
    """Unregister a plugin.

    Args:
        plugin_id: ID of the plugin to unregister

    Raises:
        IntegrationError: If the plugin is not registered
    """
    _plugin_manager.unregister_plugin(plugin_id)


def initialize_plugin(plugin_id: str) -> None:
    """Initialize a plugin.

    Args:
        plugin_id: ID of the plugin to initialize

    Raises:
        IntegrationError: If the plugin is not registered or already initialized
    """
    _plugin_manager.initialize_plugin(plugin_id)


def initialize_all_plugins() -> dict[str, bool]:
    """Initialize all registered plugins.

    Returns:
        Dictionary of plugin IDs to initialization success status
    """
    return _plugin_manager.initialize_all_plugins()


def cleanup_plugin(plugin_id: str) -> None:
    """Clean up a plugin.

    Args:
        plugin_id: ID of the plugin to clean up

    Raises:
        IntegrationError: If the plugin is not registered
    """
    _plugin_manager.cleanup_plugin(plugin_id)


def cleanup_all_plugins() -> dict[str, bool]:
    """Clean up all registered plugins.

    Returns:
        Dictionary of plugin IDs to cleanup success status
    """
    return _plugin_manager.cleanup_all_plugins()


def get_plugin(plugin_id: str) -> Any:
    """Get a plugin.

    Args:
        plugin_id: ID of the plugin to get

    Returns:
        Plugin instance

    Raises:
        IntegrationError: If the plugin is not registered
    """
    return _plugin_manager.get_plugin(plugin_id)


def get_plugins() -> dict[str, Any]:
    """Get all plugins.

    Returns:
        Dictionary of plugin IDs to plugin instances
    """
    return _plugin_manager.get_plugins()


def get_plugin_state(plugin_id: str) -> PluginState | None:
    """Get the state of a plugin.

    Args:
        plugin_id: ID of the plugin to get state for

    Returns:
        Plugin state, or None if the plugin is not tracked

    Raises:
        IntegrationError: If the plugin is not registered
    """
    return _plugin_manager.get_plugin_state(plugin_id)


def get_all_plugin_states() -> dict[str, PluginState | None]:
    """Get the states of all plugins.

    Returns:
        Dictionary of plugin IDs to plugin states
    """
    return _plugin_manager.get_all_plugin_states()


def get_plugin_manager() -> PluginManager:
    """Get the plugin manager instance.

    Returns:
        Plugin manager instance
    """
    return _plugin_manager
