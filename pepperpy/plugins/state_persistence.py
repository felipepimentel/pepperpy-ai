"""State persistence for PepperPy plugins.

This module provides utilities for persisting plugin state across sessions,
including serialization, storage, and recovery mechanisms.
"""

import asyncio
import json
import os
import pickle
import time
import traceback
from enum import Enum
from typing import Any, Dict, Optional, Type

from pepperpy.core.logging import get_logger
from pepperpy.plugins.plugin import PepperpyPlugin

logger = get_logger(__name__)


class StorageFormat(Enum):
    """Format for storing plugin state."""

    # JSON format (human-readable, compatible with other systems)
    JSON = "json"

    # Pickle format (better for complex Python objects)
    PICKLE = "pickle"


class StatePersister:
    """Manager for persisting plugin state.

    This class handles saving and loading plugin state to/from disk.
    """

    def __init__(
        self,
        storage_dir: Optional[str] = None,
        format: StorageFormat = StorageFormat.JSON,
        auto_save_interval: Optional[float] = 300.0,  # 5 minutes
    ) -> None:
        """Initialize the state persister.

        Args:
            storage_dir: Directory to store state files (default: ~/.pepperpy/state)
            format: Format to use for storage
            auto_save_interval: Interval in seconds for auto-saving state (None to disable)
        """
        # Set storage directory
        if storage_dir is None:
            home_dir = os.path.expanduser("~")
            storage_dir = os.path.join(home_dir, ".pepperpy", "state")

        self.storage_dir = storage_dir
        self.format = format
        self.auto_save_interval = auto_save_interval

        # Create directory if it doesn't exist
        os.makedirs(self.storage_dir, exist_ok=True)

        self._lock = asyncio.Lock()
        self._auto_save_task: Optional[asyncio.Task] = None
        self._last_save_time: Dict[str, float] = {}
        self._plugins: Dict[str, PepperpyPlugin] = {}
        self._plugin_metadata: Dict[str, Dict[str, Any]] = {}

    def _get_state_file_path(self, plugin_id: str) -> str:
        """Get the path to the state file for a plugin.

        Args:
            plugin_id: ID of the plugin

        Returns:
            Path to the state file
        """
        extension = self.format.value
        safe_id = plugin_id.replace("/", "_").replace("\\", "_")
        return os.path.join(self.storage_dir, f"{safe_id}.{extension}")

    async def register_plugin(
        self,
        plugin_id: str,
        plugin: PepperpyPlugin,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Register a plugin for state persistence.

        Args:
            plugin_id: ID of the plugin
            plugin: Plugin instance
            metadata: Optional plugin metadata
        """
        async with self._lock:
            self._plugins[plugin_id] = plugin

            if metadata:
                self._plugin_metadata[plugin_id] = metadata

        # Start auto-save task if not already running
        await self._ensure_auto_save_task()

        logger.debug(f"Registered plugin for state persistence: {plugin_id}")

    async def unregister_plugin(self, plugin_id: str) -> None:
        """Unregister a plugin from state persistence.

        Args:
            plugin_id: ID of the plugin
        """
        async with self._lock:
            if plugin_id in self._plugins:
                del self._plugins[plugin_id]

            if plugin_id in self._plugin_metadata:
                del self._plugin_metadata[plugin_id]

        logger.debug(f"Unregistered plugin from state persistence: {plugin_id}")

    async def _ensure_auto_save_task(self) -> None:
        """Ensure the auto-save task is running."""
        if self.auto_save_interval is None:
            return

        if self._auto_save_task is None or self._auto_save_task.done():
            self._auto_save_task = asyncio.create_task(self._auto_save_loop())

    async def _auto_save_loop(self) -> None:
        """Auto-save loop for periodically saving plugin state."""
        try:
            # Make sure auto_save_interval is not None (already checked in _ensure_auto_save_task)
            interval = self.auto_save_interval
            if interval is None:
                interval = 300.0  # Default to 5 minutes if None somehow slips through

            while True:
                await asyncio.sleep(interval)
                await self.save_all()

        except asyncio.CancelledError:
            # Task was cancelled, clean up
            logger.debug("Auto-save task cancelled")
        except Exception as e:
            logger.error(f"Error in auto-save task: {e}")
            logger.debug(traceback.format_exc())

    async def save_state(self, plugin_id: str, force: bool = False) -> bool:
        """Save the state of a plugin.

        Args:
            plugin_id: ID of the plugin
            force: Force saving even if the state hasn't changed

        Returns:
            True if the state was saved, False otherwise
        """
        # Check if the plugin is registered
        if plugin_id not in self._plugins:
            logger.warning(f"Plugin not registered for state persistence: {plugin_id}")
            return False

        # Get the plugin
        plugin = self._plugins[plugin_id]

        # Check if enough time has passed since the last save
        if not force and plugin_id in self._last_save_time:
            last_save = self._last_save_time[plugin_id]

            if time.time() - last_save < 1.0:  # Minimum interval of 1 second
                return False

        # Get plugin state
        state: Dict[str, Any] = {}

        try:
            # Check if the plugin has a get_state method
            if hasattr(plugin, "get_state") and callable(plugin.get_state):
                get_state_method = plugin.get_state

                if asyncio.iscoroutinefunction(get_state_method):
                    plugin_state = await get_state_method()
                else:
                    plugin_state = get_state_method()

                if isinstance(plugin_state, dict):
                    state.update(plugin_state)

            # Add metadata
            if plugin_id in self._plugin_metadata:
                state["__metadata__"] = self._plugin_metadata[plugin_id]

            # Save timestamp
            state["__last_saved__"] = time.time()
        except Exception as e:
            logger.error(f"Error getting state for plugin {plugin_id}: {e}")
            logger.debug(traceback.format_exc())
            return False

        # Save the state
        file_path = self._get_state_file_path(plugin_id)

        try:
            if self.format == StorageFormat.JSON:
                # Save as JSON
                with open(file_path, "w") as f:
                    json.dump(state, f, indent=2)
            else:
                # Save as pickle
                with open(file_path, "wb") as f:
                    pickle.dump(state, f)

            # Update last save time
            self._last_save_time[plugin_id] = time.time()

            logger.debug(f"Saved state for plugin {plugin_id}")
            return True

        except Exception as e:
            logger.error(f"Error saving state for plugin {plugin_id}: {e}")
            logger.debug(traceback.format_exc())
            return False

    async def load_state(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """Load the state of a plugin.

        Args:
            plugin_id: ID of the plugin

        Returns:
            Dictionary containing plugin state, or None if state couldn't be loaded
        """
        file_path = self._get_state_file_path(plugin_id)

        # Check if the file exists
        if not os.path.exists(file_path):
            logger.debug(f"No state file found for plugin {plugin_id}")
            return None

        try:
            if self.format == StorageFormat.JSON:
                # Load from JSON
                with open(file_path) as f:
                    state = json.load(f)
            else:
                # Load from pickle
                with open(file_path, "rb") as f:
                    state = pickle.load(f)

            # Extract metadata
            if "__metadata__" in state:
                self._plugin_metadata[plugin_id] = state["__metadata__"]
                del state["__metadata__"]

            # Remove timestamp
            if "__last_saved__" in state:
                del state["__last_saved__"]

            logger.debug(f"Loaded state for plugin {plugin_id}")
            return state

        except Exception as e:
            logger.error(f"Error loading state for plugin {plugin_id}: {e}")
            logger.debug(traceback.format_exc())
            return None

    async def restore_state(self, plugin_id: str, plugin: PepperpyPlugin) -> bool:
        """Restore state to a plugin.

        Args:
            plugin_id: ID of the plugin
            plugin: Plugin instance to restore state to

        Returns:
            True if the state was restored, False otherwise
        """
        # Load state
        state = await self.load_state(plugin_id)

        if state is None:
            return False

        try:
            # Check if the plugin has a set_state method
            if hasattr(plugin, "set_state") and callable(plugin.set_state):
                set_state_method = plugin.set_state

                if asyncio.iscoroutinefunction(set_state_method):
                    await set_state_method(state)
                else:
                    set_state_method(state)

                logger.debug(f"Restored state for plugin {plugin_id}")
                return True

            # Default implementation: set public attributes
            for attr_name, attr_value in state.items():
                if hasattr(plugin, attr_name):
                    try:
                        setattr(plugin, attr_name, attr_value)
                    except (AttributeError, TypeError):
                        pass

            logger.debug(
                f"Restored state for plugin {plugin_id} (default implementation)"
            )
            return True

        except Exception as e:
            logger.error(f"Error restoring state for plugin {plugin_id}: {e}")
            logger.debug(traceback.format_exc())
            return False

    async def delete_state(self, plugin_id: str) -> bool:
        """Delete the state of a plugin.

        Args:
            plugin_id: ID of the plugin

        Returns:
            True if the state was deleted, False otherwise
        """
        file_path = self._get_state_file_path(plugin_id)

        # Check if the file exists
        if not os.path.exists(file_path):
            return True

        try:
            os.remove(file_path)

            # Remove from last save time
            if plugin_id in self._last_save_time:
                del self._last_save_time[plugin_id]

            logger.debug(f"Deleted state for plugin {plugin_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting state for plugin {plugin_id}: {e}")
            logger.debug(traceback.format_exc())
            return False

    async def save_all(self) -> int:
        """Save the state of all registered plugins.

        Returns:
            Number of plugins whose state was saved
        """
        saved_count = 0

        async with self._lock:
            plugins = list(self._plugins.items())

        for plugin_id, _ in plugins:
            if await self.save_state(plugin_id):
                saved_count += 1

        logger.debug(f"Saved state for {saved_count} plugins")
        return saved_count

    async def shutdown(self) -> None:
        """Save all state and shut down the persister."""
        # Cancel auto-save task
        if self._auto_save_task is not None:
            self._auto_save_task.cancel()
            try:
                await self._auto_save_task
            except asyncio.CancelledError:
                pass
            self._auto_save_task = None

        # Save all state
        await self.save_all()

        logger.debug("State persister shut down")


class PersistentState:
    """Mixin for plugins that support state persistence.

    This mixin provides methods for plugins to save and restore their state
    for persistence across sessions.
    """

    def get_state(self) -> Dict[str, Any]:
        """Get plugin state for persistence.

        Returns:
            Dictionary containing plugin state
        """
        state: Dict[str, Any] = {}

        # Get public attributes
        for attr_name in dir(self):
            if attr_name.startswith("_") or callable(getattr(self, attr_name)):
                continue

            try:
                attr_value = getattr(self, attr_name)

                # Skip unpicklable objects
                try:
                    json.dumps({attr_name: attr_value})
                    state[attr_name] = attr_value
                except (TypeError, OverflowError):
                    continue

            except (AttributeError, TypeError):
                pass

        return state

    def set_state(self, state: Dict[str, Any]) -> None:
        """Set plugin state from persistence.

        Args:
            state: Dictionary containing plugin state
        """
        # Set public attributes
        for attr_name, attr_value in state.items():
            if hasattr(self, attr_name):
                try:
                    setattr(self, attr_name, attr_value)
                except (AttributeError, TypeError):
                    pass

    def __new__(cls, *args: Any, **kwargs: Any) -> Any:
        """Create a new instance of the plugin.

        This method adds the persistent state methods to the plugin class
        if they don't already exist.
        """
        instance = super().__new__(cls)

        # Add get_state method if it doesn't exist
        if not hasattr(cls, "get_state"):
            cls.get_state = PersistentState.get_state

        # Add set_state method if it doesn't exist
        if not hasattr(cls, "set_state"):
            cls.set_state = PersistentState.set_state

        return instance


# Add state persistence capability to a plugin class
def persistent_state(plugin_class: Type[PepperpyPlugin]) -> Type[PepperpyPlugin]:
    """Decorator to make a plugin class state-persistent.

    Args:
        plugin_class: Plugin class to make state-persistent

    Returns:
        State-persistent plugin class
    """

    # Create a new class that inherits from the plugin class and PersistentState
    class PersistentPlugin(plugin_class, PersistentState):
        pass

    # Copy class attributes
    PersistentPlugin.__name__ = plugin_class.__name__
    PersistentPlugin.__qualname__ = plugin_class.__qualname__
    PersistentPlugin.__module__ = plugin_class.__module__
    PersistentPlugin.__doc__ = plugin_class.__doc__

    return PersistentPlugin


# Global state persister instance
_state_persister: Optional[StatePersister] = None


def get_state_persister(
    storage_dir: Optional[str] = None,
    format: StorageFormat = StorageFormat.JSON,
    auto_save_interval: Optional[float] = 300.0,
) -> StatePersister:
    """Get the global state persister instance.

    Args:
        storage_dir: Optional storage directory
        format: Optional storage format
        auto_save_interval: Optional auto-save interval

    Returns:
        StatePersister instance
    """
    global _state_persister

    if _state_persister is None:
        _state_persister = StatePersister(storage_dir, format, auto_save_interval)

    return _state_persister


async def register_plugin_for_persistence(
    plugin_id: str, plugin: PepperpyPlugin, metadata: Optional[Dict[str, Any]] = None
) -> None:
    """Register a plugin for state persistence.

    Args:
        plugin_id: ID of the plugin
        plugin: Plugin instance
        metadata: Optional plugin metadata
    """
    persister = get_state_persister()
    await persister.register_plugin(plugin_id, plugin, metadata)

    # Restore state if available
    await persister.restore_state(plugin_id, plugin)


async def save_plugin_state(plugin_id: str, force: bool = False) -> bool:
    """Save the state of a plugin.

    Args:
        plugin_id: ID of the plugin
        force: Force saving even if the state hasn't changed

    Returns:
        True if the state was saved, False otherwise
    """
    persister = get_state_persister()
    return await persister.save_state(plugin_id, force)


async def save_all_plugin_states() -> int:
    """Save the state of all registered plugins.

    Returns:
        Number of plugins whose state was saved
    """
    persister = get_state_persister()
    return await persister.save_all()


async def shutdown_persistence() -> None:
    """Shut down state persistence."""
    global _state_persister

    if _state_persister is not None:
        await _state_persister.shutdown()
        _state_persister = None
