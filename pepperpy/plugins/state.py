"""Plugin state management for PepperPy.

This module provides functionality for managing the state and lifecycle
of plugins, including tracking initialization, cleanup, and errors.
"""

import enum
import threading
import time
from typing import Any, Dict, List, Optional, Set

from pepperpy.core.errors import PluginError
from pepperpy.core.logging import get_logger
from pepperpy.plugins.plugin import PepperpyPlugin

logger = get_logger(__name__)


# Define PluginStateError directly here since it might not be in core.errors yet
class PluginStateError(PluginError):
    """Error raised when a plugin is in an invalid state for an operation."""

    def __init__(
        self,
        message: str,
        plugin_id: Optional[str] = None,
        current_state: Optional[str] = None,
        expected_state: Optional[List[str]] = None,
        cause: Optional[Exception] = None,
    ):
        """Initialize a plugin state error.

        Args:
            message: Error message
            plugin_id: Optional plugin ID
            current_state: Optional current state of the plugin
            expected_state: Optional expected state(s) for the operation
            cause: Optional exception that caused this error
        """
        super().__init__(message, plugin_id=plugin_id, cause=cause)
        self.current_state = current_state
        self.expected_state = expected_state


class PluginState(enum.Enum):
    """State of a plugin in its lifecycle."""

    # Plugin is registered but not yet initialized
    REGISTERED = "registered"

    # Plugin is currently being initialized
    INITIALIZING = "initializing"

    # Plugin is initialized and ready to use
    INITIALIZED = "initialized"

    # Plugin is currently being cleaned up
    CLEANING_UP = "cleaning_up"

    # Plugin is cleaned up and no longer usable
    CLEANED_UP = "cleaned_up"

    # Plugin initialization failed
    INIT_FAILED = "init_failed"

    # Plugin cleanup failed
    CLEANUP_FAILED = "cleanup_failed"

    # Plugin is in an error state
    ERROR = "error"


class PluginStateInfo:
    """Information about the state of a plugin."""

    def __init__(
        self,
        plugin_id: str,
        initial_state: PluginState = PluginState.REGISTERED,
    ):
        """Initialize plugin state information.

        Args:
            plugin_id: ID of the plugin
            initial_state: Initial state of the plugin
        """
        self.plugin_id = plugin_id
        self.state = initial_state
        self.error: Optional[Exception] = None
        self.registered_at = time.time()
        self.initialized_at: Optional[float] = None
        self.cleaned_up_at: Optional[float] = None
        self.last_state_change = time.time()
        self.state_history: List[Dict[str, Any]] = [
            {
                "state": initial_state.value,
                "timestamp": self.last_state_change,
                "error": None,
            }
        ]

    def set_state(self, state: PluginState, error: Optional[Exception] = None) -> None:
        """Set the state of the plugin.

        Args:
            state: New state
            error: Optional error that caused the state change
        """
        self.state = state
        self.error = error

        timestamp = time.time()
        self.last_state_change = timestamp

        # Update timestamps for specific states
        if state == PluginState.INITIALIZED:
            self.initialized_at = timestamp
        elif state == PluginState.CLEANED_UP:
            self.cleaned_up_at = timestamp

        # Add to state history
        self.state_history.append(
            {
                "state": state.value,
                "timestamp": timestamp,
                "error": str(error) if error else None,
            }
        )

    def is_usable(self) -> bool:
        """Check if the plugin is in a usable state.

        Returns:
            True if the plugin is usable, False otherwise
        """
        return self.state == PluginState.INITIALIZED

    def is_failed(self) -> bool:
        """Check if the plugin is in a failed state.

        Returns:
            True if the plugin is in a failed state, False otherwise
        """
        return self.state in [
            PluginState.INIT_FAILED,
            PluginState.CLEANUP_FAILED,
            PluginState.ERROR,
        ]

    def is_terminated(self) -> bool:
        """Check if the plugin is terminated.

        Returns:
            True if the plugin is terminated, False otherwise
        """
        return self.state in [PluginState.CLEANED_UP, PluginState.CLEANUP_FAILED]

    def get_lifetime(self) -> Optional[float]:
        """Get the lifetime of the plugin in seconds.

        Returns:
            Lifetime in seconds, or None if not initialized or still active
        """
        if not self.initialized_at:
            return None

        if not self.cleaned_up_at:
            return None

        return self.cleaned_up_at - self.initialized_at

    def __str__(self) -> str:
        """Get string representation of the plugin state.

        Returns:
            String representation
        """
        parts = [f"Plugin {self.plugin_id}: {self.state.value}"]

        if self.error:
            parts.append(f"Error: {self.error}")

        if self.initialized_at:
            parts.append(
                f"Initialized: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.initialized_at))}"
            )

        if self.cleaned_up_at:
            parts.append(
                f"Cleaned up: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.cleaned_up_at))}"
            )

        lifetime = self.get_lifetime()
        if lifetime is not None:
            parts.append(f"Lifetime: {lifetime:.2f}s")

        return " | ".join(parts)


class PluginStateManager:
    """Manager for plugin states."""

    def __init__(self):
        """Initialize the plugin state manager."""
        self._states: Dict[str, PluginStateInfo] = {}
        self._lock = threading.RLock()
        self._plugins_by_state: Dict[PluginState, Set[str]] = {
            state: set() for state in PluginState
        }

    def register_plugin(self, plugin_id: str) -> PluginStateInfo:
        """Register a plugin with the state manager.

        Args:
            plugin_id: ID of the plugin

        Returns:
            State information for the plugin
        """
        with self._lock:
            if plugin_id in self._states:
                return self._states[plugin_id]

            state_info = PluginStateInfo(plugin_id)
            self._states[plugin_id] = state_info
            self._plugins_by_state[PluginState.REGISTERED].add(plugin_id)

            logger.debug(f"Registered plugin state for {plugin_id}")
            return state_info

    def unregister_plugin(self, plugin_id: str) -> None:
        """Unregister a plugin from the state manager.

        Args:
            plugin_id: ID of the plugin

        Raises:
            KeyError: If the plugin is not registered
        """
        with self._lock:
            if plugin_id not in self._states:
                raise KeyError(f"Plugin {plugin_id} is not registered")

            # Remove from plugins by state
            current_state = self._states[plugin_id].state
            self._plugins_by_state[current_state].discard(plugin_id)

            # Remove state info
            del self._states[plugin_id]

            logger.debug(f"Unregistered plugin state for {plugin_id}")

    def get_state(self, plugin_id: str) -> PluginStateInfo:
        """Get the state information for a plugin.

        Args:
            plugin_id: ID of the plugin

        Returns:
            State information for the plugin

        Raises:
            KeyError: If the plugin is not registered
        """
        with self._lock:
            if plugin_id not in self._states:
                raise KeyError(f"Plugin {plugin_id} is not registered")

            return self._states[plugin_id]

    def has_plugin(self, plugin_id: str) -> bool:
        """Check if a plugin is registered.

        Args:
            plugin_id: ID of the plugin

        Returns:
            True if the plugin is registered, False otherwise
        """
        with self._lock:
            return plugin_id in self._states

    def set_state(
        self, plugin_id: str, state: PluginState, error: Optional[Exception] = None
    ) -> None:
        """Set the state of a plugin.

        Args:
            plugin_id: ID of the plugin
            state: New state
            error: Optional error that caused the state change

        Raises:
            KeyError: If the plugin is not registered
        """
        with self._lock:
            if plugin_id not in self._states:
                raise KeyError(f"Plugin {plugin_id} is not registered")

            # Get current state
            state_info = self._states[plugin_id]
            current_state = state_info.state

            # Update state info
            state_info.set_state(state, error)

            # Update plugins by state
            self._plugins_by_state[current_state].discard(plugin_id)
            self._plugins_by_state[state].add(plugin_id)

            logger.debug(f"Set state for plugin {plugin_id}: {state.value}")

    def get_plugins_in_state(self, state: PluginState) -> Set[str]:
        """Get all plugins in a specific state.

        Args:
            state: State to filter by

        Returns:
            Set of plugin IDs in the specified state
        """
        with self._lock:
            return self._plugins_by_state[state].copy()

    def get_usable_plugins(self) -> Set[str]:
        """Get all plugins that are in a usable state.

        Returns:
            Set of plugin IDs in a usable state
        """
        with self._lock:
            return self._plugins_by_state[PluginState.INITIALIZED].copy()

    def get_failed_plugins(self) -> Set[str]:
        """Get all plugins that are in a failed state.

        Returns:
            Set of plugin IDs in a failed state
        """
        with self._lock:
            result = set()
            for state in [
                PluginState.INIT_FAILED,
                PluginState.CLEANUP_FAILED,
                PluginState.ERROR,
            ]:
                result.update(self._plugins_by_state[state])
            return result

    def get_terminated_plugins(self) -> Set[str]:
        """Get all plugins that are terminated.

        Returns:
            Set of plugin IDs that are terminated
        """
        with self._lock:
            result = set()
            for state in [PluginState.CLEANED_UP, PluginState.CLEANUP_FAILED]:
                result.update(self._plugins_by_state[state])
            return result

    def get_all_states(self) -> Dict[str, PluginStateInfo]:
        """Get state information for all registered plugins.

        Returns:
            Dictionary of plugin ID to state information
        """
        with self._lock:
            return self._states.copy()

    def clear(self) -> None:
        """Clear all plugin states."""
        with self._lock:
            self._states.clear()
            self._plugins_by_state = {state: set() for state in PluginState}

            logger.debug("Cleared all plugin states")


# Singleton instance
_state_manager = PluginStateManager()


# Convenience functions
def register_plugin(plugin_id: str) -> PluginStateInfo:
    """Register a plugin with the state manager.

    Args:
        plugin_id: ID of the plugin

    Returns:
        State information for the plugin
    """
    return _state_manager.register_plugin(plugin_id)


def unregister_plugin(plugin_id: str) -> None:
    """Unregister a plugin from the state manager.

    Args:
        plugin_id: ID of the plugin

    Raises:
        KeyError: If the plugin is not registered
    """
    _state_manager.unregister_plugin(plugin_id)


def get_state(plugin_id: str) -> PluginStateInfo:
    """Get the state information for a plugin.

    Args:
        plugin_id: ID of the plugin

    Returns:
        State information for the plugin

    Raises:
        KeyError: If the plugin is not registered
    """
    return _state_manager.get_state(plugin_id)


def has_plugin(plugin_id: str) -> bool:
    """Check if a plugin is registered.

    Args:
        plugin_id: ID of the plugin

    Returns:
        True if the plugin is registered, False otherwise
    """
    return _state_manager.has_plugin(plugin_id)


def set_state(
    plugin_id: str, state: PluginState, error: Optional[Exception] = None
) -> None:
    """Set the state of a plugin.

    Args:
        plugin_id: ID of the plugin
        state: New state
        error: Optional error that caused the state change

    Raises:
        KeyError: If the plugin is not registered
    """
    _state_manager.set_state(plugin_id, state, error)


def get_plugins_in_state(state: PluginState) -> Set[str]:
    """Get all plugins in a specific state.

    Args:
        state: State to filter by

    Returns:
        Set of plugin IDs in the specified state
    """
    return _state_manager.get_plugins_in_state(state)


def get_usable_plugins() -> Set[str]:
    """Get all plugins that are in a usable state.

    Returns:
        Set of plugin IDs in a usable state
    """
    return _state_manager.get_usable_plugins()


def get_failed_plugins() -> Set[str]:
    """Get all plugins that are in a failed state.

    Returns:
        Set of plugin IDs in a failed state
    """
    return _state_manager.get_failed_plugins()


def get_terminated_plugins() -> Set[str]:
    """Get all plugins that are terminated.

    Returns:
        Set of plugin IDs that are terminated
    """
    return _state_manager.get_terminated_plugins()


def get_all_states() -> Dict[str, PluginStateInfo]:
    """Get state information for all registered plugins.

    Returns:
        Dictionary of plugin ID to state information
    """
    return _state_manager.get_all_states()


def clear_states() -> None:
    """Clear all plugin states."""
    _state_manager.clear()


def get_state_manager() -> PluginStateManager:
    """Get the singleton state manager instance.

    Returns:
        State manager instance
    """
    return _state_manager


def verify_state(
    plugin_id: str, expected_states: List[PluginState], operation: str
) -> None:
    """Verify that a plugin is in one of the expected states.

    Args:
        plugin_id: ID of the plugin
        expected_states: List of expected states
        operation: Operation being performed

    Raises:
        PluginStateError: If the plugin is not in one of the expected states
    """
    try:
        state_info = get_state(plugin_id)
        if state_info.state not in expected_states:
            expected_values = [state.value for state in expected_states]
            raise PluginStateError(
                f"Plugin {plugin_id} is in state {state_info.state.value} but {operation} requires one of: {', '.join(expected_values)}",
                plugin_id=plugin_id,
                current_state=state_info.state.value,
                expected_state=expected_values,
            )
    except KeyError:
        raise PluginStateError(
            f"Plugin {plugin_id} is not registered",
            plugin_id=plugin_id,
        )


class StateTrackedPlugin(PepperpyPlugin):
    """Mixin that tracks plugin state automatically."""

    def __init__(self, *args, **kwargs):
        """Initialize the state tracked plugin.

        This method should be called from the plugin's __init__ method.
        """
        # Set default plugin_id if not already set
        if not hasattr(self, "plugin_id"):
            self.plugin_id = self.__class__.__name__

        super().__init__(*args, **kwargs)

        # Register with state manager
        register_plugin(self.plugin_id)

    async def initialize(self, **kwargs) -> None:
        """Initialize the plugin.

        Args:
            **kwargs: Keyword arguments for initialization
        """
        try:
            # Set state to initializing
            set_state(self.plugin_id, PluginState.INITIALIZING)

            # Call parent initialize
            await super().initialize(**kwargs)

            # Set state to initialized
            set_state(self.plugin_id, PluginState.INITIALIZED)
        except Exception as e:
            # Set state to init failed
            set_state(self.plugin_id, PluginState.INIT_FAILED, e)

            # Re-raise exception
            raise

    async def cleanup(self, **kwargs) -> None:
        """Clean up the plugin.

        Args:
            **kwargs: Keyword arguments for cleanup
        """
        try:
            # Set state to cleaning up
            set_state(self.plugin_id, PluginState.CLEANING_UP)

            # Call parent cleanup
            await super().cleanup(**kwargs)

            # Set state to cleaned up
            set_state(self.plugin_id, PluginState.CLEANED_UP)
        except Exception as e:
            # Set state to cleanup failed
            set_state(self.plugin_id, PluginState.CLEANUP_FAILED, e)

            # Re-raise exception
            raise

    def __del__(self):
        """Delete the plugin."""
        try:
            # Check if plugin is still registered
            if has_plugin(self.plugin_id):
                # Unregister from state manager
                unregister_plugin(self.plugin_id)
        except Exception:
            # Ignore exceptions during garbage collection
            pass
