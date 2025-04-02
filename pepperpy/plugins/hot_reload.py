"""Hot-reloading for PepperPy plugins.

This module provides utilities for hot-reloading plugins,
including file monitoring, automatic reloading, and graceful state transfer.
"""

import asyncio
import importlib
import importlib.util
import inspect
import os
import sys
import time
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Type

from watchfiles import Change, awatch

from pepperpy.core.errors import PluginError
from pepperpy.core.logging import get_logger
from pepperpy.plugins.plugin import PepperpyPlugin

from .discovery import PluginDiscovery

logger = get_logger(__name__)


class HotReloader:
    """Hot-reloader for PepperPy plugins.

    This class monitors plugin files for changes and reloads them automatically.
    It also handles graceful state transfer between plugin versions.
    """

    def __init__(
        self,
        plugin_discovery: PluginDiscovery,
        plugin_dirs: Optional[List[str]] = None,
        watch_patterns: Optional[List[str]] = None,
        debounce_seconds: float = 1.0,
        skip_patterns: Optional[List[str]] = None,
        reload_delay: float = 0.5,
    ) -> None:
        """Initialize the hot-reloader.

        Args:
            plugin_discovery: Plugin discovery instance to use for reloading
            plugin_dirs: Optional list of plugin directories to monitor
            watch_patterns: Optional list of file patterns to watch
            debounce_seconds: Minimum time between reloads of the same file
            skip_patterns: Optional list of file patterns to skip
            reload_delay: Delay in seconds before reloading after a change
        """
        self.plugin_discovery = plugin_discovery
        self.plugin_dirs = plugin_dirs or []
        self.watch_patterns = watch_patterns or ["*.py", "*.yaml", "*.yml"]
        self.debounce_seconds = debounce_seconds
        self.skip_patterns = skip_patterns or [
            "__pycache__/*",
            "*.pyc",
            "*.pyo",
            ".git/*",
        ]
        self.reload_delay = reload_delay

        self._watch_task: Optional[asyncio.Task] = None
        self._running = False
        self._file_timestamps: Dict[str, float] = {}
        self._plugins_to_reload: Set[str] = set()
        self._loaded_modules: Dict[str, Dict[str, Any]] = {}
        self._loaded_module_times: Dict[str, float] = {}
        self._plugin_states: Dict[str, Dict[str, Any]] = {}

    def start(self) -> None:
        """Start the hot-reloader."""
        if self._watch_task is not None:
            return

        self._running = True
        self._watch_task = asyncio.create_task(self._watch_files())
        logger.info("Hot-reloader started")

    def stop(self) -> None:
        """Stop the hot-reloader."""
        self._running = False

        if self._watch_task is not None:
            self._watch_task.cancel()
            self._watch_task = None

        logger.info("Hot-reloader stopped")

    async def _watch_files(self) -> None:
        """Watch files for changes and reload plugins as needed."""
        if not self.plugin_dirs:
            logger.warning("No plugin directories specified for hot-reloading")
            return

        try:
            # Validate plugin directories
            valid_dirs = []
            for plugin_dir in self.plugin_dirs:
                plugin_path = Path(plugin_dir)
                if not plugin_path.exists():
                    logger.warning(f"Plugin directory does not exist: {plugin_dir}")
                    continue

                if not plugin_path.is_dir():
                    logger.warning(f"Not a directory: {plugin_dir}")
                    continue

                valid_dirs.append(str(plugin_path.absolute()))

            if not valid_dirs:
                logger.warning("No valid plugin directories found for hot-reloading")
                return

            # Start watching
            logger.info(f"Watching plugin directories: {', '.join(valid_dirs)}")

            async for changes in awatch(
                *valid_dirs,
                watch_filter=self._filter_changes,
                debounce=int(self.debounce_seconds * 1000),
                step=50,
            ):
                if not self._running:
                    break

                # Process changes
                await self._process_changes(changes)

        except asyncio.CancelledError:
            # Task was cancelled, clean up
            logger.debug("Hot-reloader task cancelled")
        except Exception as e:
            logger.error(f"Error in hot-reloader: {e}")
            logger.debug(traceback.format_exc())

    def _filter_changes(self, change: Tuple[Change, str]) -> bool:
        """Filter changes to only include relevant files.

        Args:
            change: Change tuple from watchfiles

        Returns:
            True if the change should be processed, False otherwise
        """
        _, path = change

        # Skip files matching skip patterns
        for pattern in self.skip_patterns:
            if Path(path).match(pattern):
                return False

        # Only include files matching watch patterns
        for pattern in self.watch_patterns:
            if Path(path).match(pattern):
                return True

        return False

    async def _process_changes(self, changes: Set[Tuple[Change, str]]) -> None:
        """Process file changes and reload plugins as needed.

        Args:
            changes: Set of changes from watchfiles
        """
        if not changes:
            return

        plugin_files = set()

        # Process changes
        for change_type, path in changes:
            # Skip deleted files
            if change_type == Change.deleted:
                continue

            # Check if the file changed recently
            now = time.time()
            last_changed = self._file_timestamps.get(path, 0)
            if now - last_changed < self.debounce_seconds:
                continue

            # Update timestamp
            self._file_timestamps[path] = now

            # Add to plugin files
            plugin_files.add(path)

        # Wait for a brief period to let all related changes occur
        await asyncio.sleep(self.reload_delay)

        # Determine which plugins to reload
        plugins_to_reload = self._find_affected_plugins(plugin_files)

        # Reload plugins
        if plugins_to_reload:
            try:
                await self._reload_plugins(plugins_to_reload)
            except Exception as e:
                logger.error(f"Error reloading plugins: {e}")
                logger.debug(traceback.format_exc())

    def _find_affected_plugins(self, changed_files: Set[str]) -> List[str]:
        """Find plugins affected by changed files.

        Args:
            changed_files: Set of files that changed

        Returns:
            List of plugin IDs to reload
        """
        plugins_to_reload = set()

        # Get all loaded plugins
        loaded_plugins = self.plugin_discovery.get_loaded_plugins()

        for plugin_id, plugin_metadata in loaded_plugins.items():
            # Get plugin module
            plugin_module = plugin_metadata.module_name

            if not plugin_module:
                continue

            try:
                # Check if the module exists
                module_spec = importlib.util.find_spec(plugin_module)

                if not module_spec or not module_spec.origin:
                    continue

                # Get the module path
                module_path = module_spec.origin

                # Check if any changed file affects this plugin
                plugin_dir = os.path.dirname(module_path)

                for file_path in changed_files:
                    if file_path == module_path or file_path.startswith(plugin_dir):
                        plugins_to_reload.add(plugin_id)
                        break

            except (ImportError, AttributeError) as e:
                logger.debug(f"Error checking module for plugin {plugin_id}: {e}")

        return list(plugins_to_reload)

    async def _reload_plugins(self, plugin_ids: List[str]) -> None:
        """Reload plugins.

        Args:
            plugin_ids: List of plugin IDs to reload
        """
        if not plugin_ids:
            return

        logger.info(f"Reloading plugins: {', '.join(plugin_ids)}")

        # Get current plugin manager
        plugin_manager = self.plugin_discovery.plugin_manager

        if not plugin_manager:
            logger.warning("No plugin manager available for reloading plugins")
            return

        # Reload each plugin
        for plugin_id in plugin_ids:
            try:
                # Get current plugin
                current_plugin = plugin_manager.get_plugin(plugin_id)

                if not current_plugin:
                    logger.warning(f"Plugin not found for reloading: {plugin_id}")
                    continue

                # Get plugin metadata
                plugin_metadata = self.plugin_discovery.get_plugin_metadata(plugin_id)

                if not plugin_metadata:
                    logger.warning(
                        f"Plugin metadata not found for reloading: {plugin_id}"
                    )
                    continue

                # Save plugin state
                plugin_state = await self._extract_plugin_state(current_plugin)
                self._plugin_states[plugin_id] = plugin_state

                # Unload the plugin
                await plugin_manager.unload_plugin(plugin_id)

                # Reload the module
                module_name = plugin_metadata.module_name

                if module_name:
                    await self._reload_module(module_name)

                # Rediscover the plugin
                await self.plugin_discovery.discover_plugins(force_reload=True)

                # Get the new plugin metadata
                new_metadata = self.plugin_discovery.get_plugin_metadata(plugin_id)

                if not new_metadata:
                    logger.warning(f"Reloaded plugin metadata not found: {plugin_id}")
                    continue

                # Load the new plugin
                await plugin_manager.load_plugin(plugin_id)

                # Get the new plugin instance
                new_plugin = plugin_manager.get_plugin(plugin_id)

                if not new_plugin:
                    logger.warning(f"Reloaded plugin not found: {plugin_id}")
                    continue

                # Restore plugin state
                await self._restore_plugin_state(new_plugin, plugin_state)

                logger.info(f"Successfully reloaded plugin: {plugin_id}")

            except Exception as e:
                logger.error(f"Error reloading plugin {plugin_id}: {e}")
                logger.debug(traceback.format_exc())

    async def _reload_module(self, module_name: str) -> None:
        """Reload a module and its dependencies.

        Args:
            module_name: Name of the module to reload
        """
        try:
            # Check if module is loaded
            if module_name not in sys.modules:
                logger.debug(f"Module not loaded, importing fresh: {module_name}")
                importlib.import_module(module_name)
                return

            # Save module state
            if module_name not in self._loaded_modules:
                self._loaded_modules[module_name] = {}

            module = sys.modules[module_name]

            # Store module attributes
            self._loaded_modules[module_name] = {
                name: getattr(module, name)
                for name in dir(module)
                if not name.startswith("_")
                and not inspect.ismodule(getattr(module, name))
            }

            # Store module timestamp
            self._loaded_module_times[module_name] = time.time()

            # Reload the module
            logger.debug(f"Reloading module: {module_name}")
            importlib.reload(module)

            # Reload submodules if needed
            for submodule_name in list(sys.modules.keys()):
                if submodule_name != module_name and submodule_name.startswith(
                    f"{module_name}."
                ):
                    await self._reload_module(submodule_name)

        except Exception as e:
            logger.error(f"Error reloading module {module_name}: {e}")
            logger.debug(traceback.format_exc())

    async def _extract_plugin_state(self, plugin: PepperpyPlugin) -> Dict[str, Any]:
        """Extract state from a plugin for hot-reloading.

        Args:
            plugin: Plugin to extract state from

        Returns:
            Dictionary containing plugin state
        """
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

            # Get public attributes
            for attr_name in dir(plugin):
                if attr_name.startswith("_") or callable(getattr(plugin, attr_name)):
                    continue

                try:
                    attr_value = getattr(plugin, attr_name)

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

        except Exception as e:
            logger.error(f"Error extracting plugin state: {e}")

        return state

    async def _restore_plugin_state(
        self, plugin: PepperpyPlugin, state: Dict[str, Any]
    ) -> None:
        """Restore state to a plugin after hot-reloading.

        Args:
            plugin: Plugin to restore state to
            state: Dictionary containing plugin state
        """
        try:
            # Check if the plugin has a set_state method
            if hasattr(plugin, "set_state") and callable(plugin.set_state):
                set_state_method = plugin.set_state

                if asyncio.iscoroutinefunction(set_state_method):
                    await set_state_method(state)
                else:
                    set_state_method(state)

                return

            # Set public attributes
            for attr_name, attr_value in state.items():
                if hasattr(plugin, attr_name):
                    try:
                        setattr(plugin, attr_name, attr_value)
                    except (AttributeError, TypeError):
                        pass

        except Exception as e:
            logger.error(f"Error restoring plugin state: {e}")


class HotReloadablePlugin:
    """Mixin for plugins that support hot-reloading.

    This mixin provides methods for plugins to save and restore their state
    during hot-reloading.
    """

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

    def __new__(cls, *args: Any, **kwargs: Any) -> Any:
        """Create a new instance of the plugin.

        This method adds the hot-reloadable methods to the plugin class
        if they don't already exist.
        """
        instance = super().__new__(cls)

        # Add get_state method if it doesn't exist
        if not hasattr(cls, "get_state"):
            cls.get_state = HotReloadablePlugin.get_state

        # Add set_state method if it doesn't exist
        if not hasattr(cls, "set_state"):
            cls.set_state = HotReloadablePlugin.set_state

        return instance


# Add hot-reloading capability to a plugin class
def hot_reloadable(plugin_class: Type[PepperpyPlugin]) -> Type[PepperpyPlugin]:
    """Decorator to make a plugin class hot-reloadable.

    Args:
        plugin_class: Plugin class to make hot-reloadable

    Returns:
        Hot-reloadable plugin class
    """

    # Create a new class that inherits from the plugin class and HotReloadablePlugin
    class HotReloadable(plugin_class, HotReloadablePlugin):
        pass

    # Copy class attributes
    HotReloadable.__name__ = plugin_class.__name__
    HotReloadable.__qualname__ = plugin_class.__qualname__
    HotReloadable.__module__ = plugin_class.__module__
    HotReloadable.__doc__ = plugin_class.__doc__

    return HotReloadable


# Global hot-reloader instance
_hot_reloader: Optional[HotReloader] = None


def get_hot_reloader(
    plugin_discovery: Optional[PluginDiscovery] = None,
    plugin_dirs: Optional[List[str]] = None,
) -> HotReloader:
    """Get the global hot-reloader instance.

    Args:
        plugin_discovery: Optional plugin discovery instance
        plugin_dirs: Optional list of plugin directories

    Returns:
        HotReloader instance
    """
    global _hot_reloader

    if _hot_reloader is None and plugin_discovery is not None:
        _hot_reloader = HotReloader(plugin_discovery, plugin_dirs)

    if _hot_reloader is None:
        raise PluginError("Hot-reloader not initialized")

    return _hot_reloader


async def start_hot_reloading(
    plugin_discovery: PluginDiscovery, plugin_dirs: Optional[List[str]] = None
) -> HotReloader:
    """Start hot-reloading for plugins.

    Args:
        plugin_discovery: Plugin discovery instance
        plugin_dirs: Optional list of plugin directories

    Returns:
        HotReloader instance
    """
    reloader = get_hot_reloader(plugin_discovery, plugin_dirs)
    reloader.start()
    return reloader


async def stop_hot_reloading() -> None:
    """Stop hot-reloading for plugins."""
    global _hot_reloader

    if _hot_reloader is not None:
        _hot_reloader.stop()
        _hot_reloader = None
