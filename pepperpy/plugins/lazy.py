"""Lazy loading support for PepperPy plugins.

This module provides lazy loading functionality for PepperPy plugins,
allowing plugins to be initialized only when they are first used.
"""

import asyncio
import functools
import importlib.util
import inspect
import sys
from typing import Any, Callable, Dict, Optional, Type, TypeVar, cast

from pepperpy.core.errors import PluginError
from pepperpy.core.logging import get_logger
from pepperpy.plugins.plugin import PepperpyPlugin

logger = get_logger(__name__)

T = TypeVar("T", bound=PepperpyPlugin)
F = TypeVar("F", bound=Callable[..., Any])


class LazyLoadingError(PluginError):
    """Error raised when lazy loading fails."""

    pass


class LazyPlugin(PepperpyPlugin):
    """A proxy for a plugin that hasn't been loaded yet.

    This class acts as a proxy for a plugin that will be loaded and
    initialized on first use. It's useful for reducing startup time
    and memory usage by only loading plugins when they are needed.
    """

    def __init__(
        self,
        plugin_id: str,
        plugin_type: str,
        plugin_class: Optional[Type[PepperpyPlugin]] = None,
        module_path: Optional[str] = None,
        entry_point: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        """Initialize a lazy plugin.

        Args:
            plugin_id: ID of the plugin
            plugin_type: Type of the plugin
            plugin_class: Class of the plugin (if already imported)
            module_path: Path to the module containing the plugin (for dynamic import)
            entry_point: Entry point for the plugin (for entry point discovery)
            config: Configuration for the plugin

        Raises:
            LazyLoadingError: If neither plugin_class, module_path, nor entry_point is provided
        """
        # Initialize with empty config and set config separately
        super().__init__({})
        if config:
            self._config = config

        if not any([plugin_class, module_path, entry_point]):
            raise LazyLoadingError(
                "At least one of plugin_class, module_path, or entry_point must be provided"
            )

        self._plugin_id = plugin_id
        self._plugin_type = plugin_type
        self._plugin_class = plugin_class
        self._module_path = module_path
        self._entry_point = entry_point
        self._instance: Optional[PepperpyPlugin] = None
        self._initialized = False
        self._loading = False
        self._load_error: Optional[Exception] = None

    async def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Create and initialize the actual plugin instance.

        Args:
            *args: Positional arguments for the plugin
            **kwargs: Keyword arguments for the plugin

        Returns:
            The initialized plugin instance

        Raises:
            LazyLoadingError: If the plugin fails to load or initialize
        """
        # Check if already initialized
        if self._instance and self._initialized:
            return self._instance

        # Check if already failed to load
        if self._load_error:
            raise LazyLoadingError(
                f"Failed to load plugin {self._plugin_id}: {self._load_error}"
            ) from self._load_error

        # Prevent concurrent loading
        if self._loading:
            # Wait for the other loading operation to complete
            for _ in range(100):  # Wait up to 10 seconds
                await asyncio.sleep(0.1)
                if not self._loading or self._instance:
                    break

            if self._loading:
                raise LazyLoadingError(
                    f"Timeout waiting for plugin {self._plugin_id} to load"
                )

            if self._load_error:
                raise LazyLoadingError(
                    f"Failed to load plugin {self._plugin_id}: {self._load_error}"
                ) from self._load_error

            if self._instance:
                return self._instance

        self._loading = True

        try:
            # Load the plugin class if needed
            if not self._plugin_class:
                self._plugin_class = await self._load_instance()

            # Create an instance with merged configs
            merged_config = self.config.copy()
            if "config" in kwargs:
                merged_config.update(kwargs["config"])
            kwargs["config"] = merged_config

            # Create instance
            self._instance = self._plugin_class(*args, **kwargs)

            # Initialize the instance
            if asyncio.iscoroutinefunction(self._instance.initialize):
                await self._instance.initialize()  # type: ignore
            else:
                self._instance.initialize()

            self._initialized = True

            return self._instance
        except Exception as e:
            self._load_error = e
            logger.error(f"Error lazy loading plugin {self._plugin_id}: {e}")
            raise LazyLoadingError(f"Failed to load plugin {self._plugin_id}") from e
        finally:
            self._loading = False

    async def _load_instance(self) -> Type[PepperpyPlugin]:
        """Load the actual plugin class.

        Returns:
            Plugin class

        Raises:
            LazyLoadingError: If the plugin class fails to load
        """
        # Try entry point first
        if self._entry_point:
            try:
                from importlib import metadata
            except ImportError:
                # Python < 3.8
                import importlib_metadata as metadata  # type: ignore

            try:
                entry_points = metadata.entry_points()
                plugin_points = []

                # Handle different entry_points() return type in Python 3.10+
                if hasattr(entry_points, "select"):
                    # Python 3.10+: use select method
                    plugin_points = list(entry_points.select(group="pepperpy.plugins"))
                elif isinstance(entry_points, dict):
                    # Python 3.8-3.9 (dict-like): access by key
                    plugin_points = list(entry_points.get("pepperpy.plugins", []))
                else:
                    # Fallback: filter entry_points manually
                    plugin_points = [
                        ep for ep in entry_points if ep.group == "pepperpy.plugins"
                    ]

                for entry_point in plugin_points:
                    if entry_point.name == self._entry_point:
                        plugin_class = entry_point.load()
                        if not issubclass(plugin_class, PepperpyPlugin):
                            raise LazyLoadingError(
                                f"Entry point {self._entry_point} is not a PepperpyPlugin"
                            )
                        return plugin_class

                raise LazyLoadingError(f"Entry point {self._entry_point} not found")
            except Exception as e:
                logger.error(
                    f"Error loading plugin from entry point {self._entry_point}: {e}"
                )
                if self._module_path:
                    logger.info(f"Falling back to module path: {self._module_path}")
                else:
                    raise LazyLoadingError(
                        f"Failed to load plugin from entry point {self._entry_point}"
                    ) from e

        # Try module path
        if self._module_path:
            try:
                # Import the module
                if self._module_path in sys.modules:
                    module = sys.modules[self._module_path]
                else:
                    module = importlib.import_module(self._module_path)

                # Find the plugin class in the module
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if (
                        issubclass(obj, PepperpyPlugin)
                        and obj != PepperpyPlugin
                        and hasattr(obj, "__metadata__")
                    ):
                        metadata = getattr(obj, "__metadata__", {})
                        if metadata.get("name") == self._plugin_id:
                            return obj

                # If we didn't find a class with the right name, try to find any plugin class
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, PepperpyPlugin) and obj != PepperpyPlugin:
                        return obj

                raise LazyLoadingError(
                    f"No PepperpyPlugin class found in module {self._module_path}"
                )
            except Exception as e:
                logger.error(
                    f"Error loading plugin from module {self._module_path}: {e}"
                )
                raise LazyLoadingError(
                    f"Failed to load plugin from module {self._module_path}"
                ) from e

        # This should never happen due to the check in __init__
        raise LazyLoadingError("No plugin_class, module_path, or entry_point provided")

    def __getattr__(self, name: str) -> Any:
        """Forward attribute access to the loaded instance.

        Args:
            name: Name of the attribute

        Returns:
            The attribute value

        Raises:
            LazyLoadingError: If the plugin is not loaded
            AttributeError: If the attribute doesn't exist
        """
        if self._instance:
            return getattr(self._instance, name)

        # Special case for initialize and cleanup
        if name in ("initialize", "cleanup"):
            return getattr(self, f"_{name}_wrapper")

        # Only allow direct access to metadata
        if name == "__metadata__":
            return {
                "name": self._plugin_id,
                "type": self._plugin_type,
                "lazy": True,
            }

        raise AttributeError(
            f"Cannot access {name} on lazy plugin {self._plugin_id} before loading"
        )

    async def _initialize_wrapper(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the lazy-loaded plugin.

        Args:
            *args: Positional arguments for initialize
            **kwargs: Keyword arguments for initialize

        Raises:
            LazyLoadingError: If the plugin fails to load or initialize
        """
        instance = await self(*args, **kwargs)
        # Already initialized by __call__

    async def _cleanup_wrapper(self, *args: Any, **kwargs: Any) -> None:
        """Clean up the lazy-loaded plugin.

        Args:
            *args: Positional arguments for cleanup
            **kwargs: Keyword arguments for cleanup

        Raises:
            LazyLoadingError: If the plugin is not loaded
        """
        if not self._instance:
            return

        if asyncio.iscoroutinefunction(self._instance.cleanup):
            await self._instance.cleanup(*args, **kwargs)  # type: ignore
        else:
            self._instance.cleanup(*args, **kwargs)

        self._initialized = False


def lazy_load(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator to lazy load a plugin instance.

    This decorator can be applied to factory functions that create
    plugin instances. The plugin will only be loaded and initialized
    when the factory function is called.

    Args:
        func: Factory function that creates a plugin instance

    Returns:
        Wrapped function that returns a lazy-loaded plugin
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        # Extract plugin information from the factory function
        plugin_id = kwargs.get("plugin_id", func.__name__)
        plugin_type = kwargs.get("plugin_type", "unknown")

        # Create lazy plugin
        lazy_plugin = LazyPlugin(
            plugin_id=plugin_id,
            plugin_type=plugin_type,
            module_path=func.__module__,
            config=kwargs.get("config"),
        )

        return cast(T, lazy_plugin)

    return wrapper
