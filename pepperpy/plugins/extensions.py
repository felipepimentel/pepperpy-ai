"""Plugin extensions for PepperPy.

This module provides extension mechanisms for PepperPy plugins,
including state persistence and hot-reloading capabilities.
"""

import asyncio
import importlib
import inspect
import os
import pickle
import sys
import time
import traceback
from threading import Thread
from typing import Any, Callable, Dict, List, Optional, Set, Type, TypeVar, cast

from pepperpy.core.logging import get_logger
from pepperpy.plugins.plugin import PepperpyPlugin

logger = get_logger(__name__)

# Type variables
T = TypeVar("T", bound=PepperpyPlugin)


class StateManager:
    """Manager for plugin state persistence."""

    def __init__(self, state_dir: Optional[str] = None) -> None:
        """Initialize state manager.

        Args:
            state_dir: Directory to store state files
        """
        self.state_dir = state_dir or os.path.join(
            os.path.expanduser("~"), ".pepperpy", "state"
        )
        os.makedirs(self.state_dir, exist_ok=True)
        self._locks: Dict[str, asyncio.Lock] = {}

    def _get_state_file(self, plugin_type: str, provider_type: str) -> str:
        """Get the state file path for a plugin.

        Args:
            plugin_type: Type of plugin
            provider_type: Type of provider

        Returns:
            Path to state file
        """
        return os.path.join(self.state_dir, f"{plugin_type}_{provider_type}.state")

    async def _get_lock(self, key: str) -> asyncio.Lock:
        """Get a lock for a state file.

        Args:
            key: Key for the lock

        Returns:
            Lock for the state file
        """
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()
        return self._locks[key]

    async def save_state(
        self, plugin_type: str, provider_type: str, state: Dict[str, Any]
    ) -> None:
        """Save plugin state.

        Args:
            plugin_type: Type of plugin
            provider_type: Type of provider
            state: State to save
        """
        state_file = self._get_state_file(plugin_type, provider_type)
        lock_key = f"{plugin_type}_{provider_type}"
        lock = await self._get_lock(lock_key)

        async with lock:
            try:
                with open(state_file, "wb") as f:
                    pickle.dump(state, f)
                logger.debug(f"Saved state for plugin: {plugin_type}/{provider_type}")
            except Exception as e:
                logger.error(
                    f"Failed to save state for plugin {plugin_type}/{provider_type}: {e}"
                )

    async def load_state(
        self, plugin_type: str, provider_type: str
    ) -> Optional[Dict[str, Any]]:
        """Load plugin state.

        Args:
            plugin_type: Type of plugin
            provider_type: Type of provider

        Returns:
            Loaded state if found, None otherwise
        """
        state_file = self._get_state_file(plugin_type, provider_type)
        lock_key = f"{plugin_type}_{provider_type}"
        lock = await self._get_lock(lock_key)

        if not os.path.exists(state_file):
            return None

        async with lock:
            try:
                with open(state_file, "rb") as f:
                    state = pickle.load(f)
                logger.debug(f"Loaded state for plugin: {plugin_type}/{provider_type}")
                return state
            except Exception as e:
                logger.error(
                    f"Failed to load state for plugin {plugin_type}/{provider_type}: {e}"
                )
                return None

    async def clear_state(self, plugin_type: str, provider_type: str) -> None:
        """Clear plugin state.

        Args:
            plugin_type: Type of plugin
            provider_type: Type of provider
        """
        state_file = self._get_state_file(plugin_type, provider_type)
        lock_key = f"{plugin_type}_{provider_type}"
        lock = await self._get_lock(lock_key)

        if not os.path.exists(state_file):
            return

        async with lock:
            try:
                os.remove(state_file)
                logger.debug(f"Cleared state for plugin: {plugin_type}/{provider_type}")
            except Exception as e:
                logger.error(
                    f"Failed to clear state for plugin {plugin_type}/{provider_type}: {e}"
                )


# Global state manager
_state_manager: Optional[StateManager] = None


def get_state_manager() -> StateManager:
    """Get the global state manager.

    Returns:
        Global state manager
    """
    global _state_manager
    if _state_manager is None:
        _state_manager = StateManager()
    return _state_manager


class PersistentState:
    """Mixin for plugins with persistent state."""

    # Type hints for attributes expected from PepperpyPlugin
    plugin_type: str
    provider_type: str

    async def save_state(self) -> None:
        """Save plugin state."""
        if not hasattr(self, "plugin_type") or not hasattr(self, "provider_type"):
            logger.warning("Cannot save state for plugin without type information")
            return

        # Get state
        state = self.get_state()
        if not state:
            return

        # Save state
        state_manager = get_state_manager()
        await state_manager.save_state(
            self.plugin_type, self.provider_type, state
        )

    async def load_state(self) -> None:
        """Load plugin state."""
        if not hasattr(self, "plugin_type") or not hasattr(self, "provider_type"):
            logger.warning("Cannot load state for plugin without type information")
            return

        # Load state
        state_manager = get_state_manager()
        state = await state_manager.load_state(
            self.plugin_type, self.provider_type
        )
        if not state:
            return

        # Set state
        self.set_state(state)

    async def clear_state(self) -> None:
        """Clear plugin state."""
        if not hasattr(self, "plugin_type") or not hasattr(self, "provider_type"):
            logger.warning("Cannot clear state for plugin without type information")
            return

        # Clear state
        state_manager = get_state_manager()
        await state_manager.clear_state(
            self.plugin_type, self.provider_type
        )

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
                    pickle.dumps(attr_value)
                except (pickle.PickleError, TypeError):
                    continue

                # Store the attribute
                state[attr_name] = attr_value

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


# Make a plugin class state-persistent
def persistent_plugin(cls: Type[T]) -> Type[T]:
    """Decorator to make a plugin class state-persistent.

    Args:
        cls: Plugin class to make state-persistent

    Returns:
        State-persistent plugin class
    """

    # Create a new class that inherits from the plugin class and PersistentState
    class PersistentPlugin(cls, PersistentState):
        """State-persistent plugin class."""

        async def initialize(self) -> None:
            """Initialize plugin with state loading."""
            # Load state before initializing
            await self.load_state()
            # Initialize
            await super().initialize()

        async def cleanup(self) -> None:
            """Clean up plugin with state saving."""
            # Save state before cleaning up
            await self.save_state()
            # Clean up
            await super().cleanup()

    # Copy class attributes
    PersistentPlugin.__name__ = cls.__name__
    PersistentPlugin.__qualname__ = cls.__qualname__
    PersistentPlugin.__module__ = cls.__module__
    PersistentPlugin.__doc__ = cls.__doc__

    return cast(Type[T], PersistentPlugin)


class HotReloader:
    """Hot-reloader for plugins."""

    def __init__(
        self,
        plugin_dirs: Optional[List[str]] = None,
        reload_interval: float = 1.0,
    ) -> None:
        """Initialize hot-reloader.

        Args:
            plugin_dirs: Directories to watch for changes
            reload_interval: Interval in seconds to check for changes
        """
        self.plugin_dirs = plugin_dirs or []
        self.reload_interval = reload_interval
        self._file_timestamps: Dict[str, float] = {}
        self._module_files: Dict[str, Set[str]] = {}
        self._watching = False
        self._watcher_thread: Optional[Thread] = None
        self._reload_handlers: List[Callable[[str], Any]] = []

    def add_plugin_dir(self, plugin_dir: str) -> None:
        """Add a plugin directory to watch.

        Args:
            plugin_dir: Directory to watch
        """
        if os.path.isdir(plugin_dir) and plugin_dir not in self.plugin_dirs:
            self.plugin_dirs.append(plugin_dir)
            logger.debug(f"Added plugin directory to watch: {plugin_dir}")

    def register_reload_handler(self, handler: Callable[[str], Any]) -> None:
        """Register a handler to be called when a module is reloaded.

        Args:
            handler: Handler function
        """
        self._reload_handlers.append(handler)

    def start(self) -> None:
        """Start the hot-reloader."""
        if self._watching:
            return

        self._watching = True
        self._watcher_thread = Thread(target=self._watch_thread, daemon=True)
        self._watcher_thread.start()
        logger.debug("Started hot-reloader")

    def stop(self) -> None:
        """Stop the hot-reloader."""
        if not self._watching:
            return

        self._watching = False
        if self._watcher_thread:
            self._watcher_thread.join(timeout=1.0)
            self._watcher_thread = None
        logger.debug("Stopped hot-reloader")

    def _watch_thread(self) -> None:
        """Thread to watch for file changes."""
        # Initial scan
        self._scan_files()

        while self._watching:
            try:
                # Check for changes
                changed_modules = self._check_for_changes()

                # Reload changed modules
                for module_name in changed_modules:
                    self._reload_module(module_name)

                # Sleep
                time.sleep(self.reload_interval)
            except Exception as e:
                logger.error(f"Error in hot-reloader: {e}")
                time.sleep(self.reload_interval)

    def _scan_files(self) -> None:
        """Scan directories for Python files."""
        self._file_timestamps = {}
        self._module_files = {}

        # Scan each directory
        for plugin_dir in self.plugin_dirs:
            if not os.path.isdir(plugin_dir):
                continue

            # Find all Python files
            for root, _, files in os.walk(plugin_dir):
                for file in files:
                    if file.endswith(".py"):
                        file_path = os.path.join(root, file)
                        try:
                            self._file_timestamps[file_path] = os.path.getmtime(
                                file_path
                            )

                            # Get module name from file path
                            rel_path = os.path.relpath(file_path, plugin_dir)
                            module_name = (
                                os.path.splitext(rel_path)[0]
                                .replace(os.path.sep, ".")
                                .replace(".__init__", "")
                            )
                            if not module_name:
                                continue

                            # Add file to module files
                            if module_name not in self._module_files:
                                self._module_files[module_name] = set()
                            self._module_files[module_name].add(file_path)
                        except OSError:
                            pass

    def _check_for_changes(self) -> List[str]:
        """Check for file changes.

        Returns:
            List of changed module names
        """
        changed_modules = set()

        # Check each file
        for file_path, timestamp in list(self._file_timestamps.items()):
            try:
                current_timestamp = os.path.getmtime(file_path)
                if current_timestamp > timestamp:
                    # File has changed
                    self._file_timestamps[file_path] = current_timestamp

                    # Find modules that use this file
                    for module_name, files in self._module_files.items():
                        if file_path in files:
                            changed_modules.add(module_name)
            except OSError:
                # File no longer exists
                del self._file_timestamps[file_path]

        # Sort modules by name
        return sorted(list(changed_modules))

    def _reload_module(self, module_name: str) -> None:
        """Reload a module.

        Args:
            module_name: Name of the module to reload
        """
        try:
            # Check if module is loaded
            if module_name in sys.modules:
                # Reload module
                module = sys.modules[module_name]
                importlib.reload(module)
                logger.info(f"Reloaded module: {module_name}")

                # Call reload handlers
                for handler in self._reload_handlers:
                    try:
                        handler(module_name)
                    except Exception as e:
                        logger.error(f"Error in reload handler: {e}")
        except Exception as e:
            logger.error(f"Failed to reload module {module_name}: {e}")
            logger.debug(traceback.format_exc())


# Global hot-reloader
_hot_reloader: Optional[HotReloader] = None


def get_hot_reloader() -> HotReloader:
    """Get the global hot-reloader.

    Returns:
        Global hot-reloader
    """
    global _hot_reloader
    if _hot_reloader is None:
        _hot_reloader = HotReloader()
    return _hot_reloader


def start_hot_reload(plugin_dirs: Optional[List[str]] = None) -> None:
    """Start hot-reloading for plugins.

    Args:
        plugin_dirs: Directories to watch for changes
    """
    reloader = get_hot_reloader()

    if plugin_dirs:
        for plugin_dir in plugin_dirs:
            reloader.add_plugin_dir(plugin_dir)

    reloader.start()


def stop_hot_reload() -> None:
    """Stop hot-reloading for plugins."""
    if _hot_reloader is not None:
        _hot_reloader.stop()


class HotReloadablePlugin:
    """Mixin for plugins that support hot-reloading."""

    def get_state(self) -> Dict[str, Any]:
        """Get plugin state for hot-reloading.

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

                # Skip complex objects and modules
                if (
                    inspect.ismodule(attr_value)
                    or inspect.isclass(attr_value)
                    or inspect.isfunction(attr_value)
                    or inspect.ismethod(attr_value)
                ):
                    continue

                # Store the attribute
                state[attr_name] = attr_value

            except (AttributeError, TypeError):
                pass

        return state

    def set_state(self, state: Dict[str, Any]) -> None:
        """Set plugin state after hot-reloading.

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


# Make a plugin class hot-reloadable
def hot_reloadable_plugin(cls: Type[T]) -> Type[T]:
    """Decorator to make a plugin class hot-reloadable.

    Args:
        cls: Plugin class to make hot-reloadable

    Returns:
        Hot-reloadable plugin class
    """

    # Create a new class that inherits from the plugin class and HotReloadablePlugin
    class HotReloadablePluginClass(cls, HotReloadablePlugin):
        """Hot-reloadable plugin class."""

        pass

    # Copy class attributes
    HotReloadablePluginClass.__name__ = cls.__name__
    HotReloadablePluginClass.__qualname__ = cls.__qualname__
    HotReloadablePluginClass.__module__ = cls.__module__
    HotReloadablePluginClass.__doc__ = cls.__doc__

    return cast(Type[T], HotReloadablePluginClass)


# Combine persistent and hot-reloadable
def extended_plugin(cls: Type[T]) -> Type[T]:
    """Decorator to make a plugin class both persistent and hot-reloadable.

    Args:
        cls: Plugin class to extend

    Returns:
        Extended plugin class
    """
    return hot_reloadable_plugin(persistent_plugin(cls))
