"""Plugin system for extensibility.

This module provides a plugin system for extending the PepperPy framework with
custom functionality. Plugins can register new providers, add new capabilities,
and hook into various parts of the framework.
"""

import importlib
import pkgutil
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union

from pepperpy.errors import PepperpyError
from pepperpy.utils.logging import get_logger

logger = get_logger(__name__)

# Type variables for generic plugin types
T = TypeVar("T")  # Plugin type


class PluginState(Enum):
    """Plugin state enum."""

    REGISTERED = auto()
    ENABLED = auto()
    DISABLED = auto()
    ERROR = auto()


@dataclass
class PluginInfo:
    """Plugin information."""

    name: str
    version: str
    description: str
    author: str
    license: str
    url: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    state: PluginState = PluginState.REGISTERED
    error: Optional[str] = None


class PluginHook(Enum):
    """Plugin hook points."""

    # Framework lifecycle hooks
    INITIALIZE = "initialize"
    SHUTDOWN = "shutdown"

    # Provider hooks
    PROVIDER_REGISTER = "provider_register"
    PROVIDER_UNREGISTER = "provider_unregister"

    # Request/response hooks
    REQUEST_PRE_PROCESS = "request_pre_process"
    REQUEST_POST_PROCESS = "request_post_process"
    RESPONSE_PRE_PROCESS = "response_pre_process"
    RESPONSE_POST_PROCESS = "response_post_process"

    # Data hooks
    DATA_PRE_SAVE = "data_pre_save"
    DATA_POST_SAVE = "data_post_save"
    DATA_PRE_LOAD = "data_pre_load"
    DATA_POST_LOAD = "data_post_load"

    # RAG hooks
    RAG_PRE_CHUNK = "rag_pre_chunk"
    RAG_POST_CHUNK = "rag_post_chunk"
    RAG_PRE_EMBED = "rag_pre_embed"
    RAG_POST_EMBED = "rag_post_embed"
    RAG_PRE_SEARCH = "rag_pre_search"
    RAG_POST_SEARCH = "rag_post_search"
    RAG_PRE_RERANK = "rag_pre_rerank"
    RAG_POST_RERANK = "rag_post_rerank"

    # Custom hooks (can be registered by plugins)
    CUSTOM = "custom"


class Plugin(ABC):
    """Base class for plugins.

    All plugins must inherit from this class and implement the required methods.
    """

    @property
    @abstractmethod
    def info(self) -> PluginInfo:
        """Get plugin information.

        Returns:
            Plugin information
        """
        pass

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the plugin.

        This method is called when the plugin is enabled.
        """
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown the plugin.

        This method is called when the plugin is disabled.
        """
        pass

    def register_hooks(self) -> Dict[str, List[Callable]]:
        """Register hooks for the plugin.

        Returns:
            A dictionary mapping hook names to lists of callables
        """
        return {}


class PluginManager:
    """Plugin manager for managing plugins.

    This class provides methods for registering, enabling, disabling, and
    managing plugins.
    """

    def __init__(self):
        """Initialize the plugin manager."""
        self._plugins: Dict[str, Plugin] = {}
        self._hooks: Dict[str, List[Callable]] = {}
        self._plugin_dirs: List[Path] = []
        self._plugin_modules: Dict[str, ModuleType] = {}

    @property
    def plugins(self) -> Dict[str, Plugin]:
        """Get all registered plugins.

        Returns:
            A dictionary mapping plugin names to plugin instances
        """
        return self._plugins

    @property
    def enabled_plugins(self) -> Dict[str, Plugin]:
        """Get all enabled plugins.

        Returns:
            A dictionary mapping plugin names to plugin instances
        """
        return {
            name: plugin
            for name, plugin in self._plugins.items()
            if plugin.info.state == PluginState.ENABLED
        }

    @property
    def disabled_plugins(self) -> Dict[str, Plugin]:
        """Get all disabled plugins.

        Returns:
            A dictionary mapping plugin names to plugin instances
        """
        return {
            name: plugin
            for name, plugin in self._plugins.items()
            if plugin.info.state == PluginState.DISABLED
        }

    @property
    def plugin_dirs(self) -> List[Path]:
        """Get all plugin directories.

        Returns:
            A list of plugin directories
        """
        return self._plugin_dirs

    def add_plugin_dir(self, plugin_dir: Union[str, Path]) -> None:
        """Add a plugin directory.

        Args:
            plugin_dir: The plugin directory to add
        """
        path = Path(plugin_dir)
        if not path.exists():
            raise PepperpyError(f"Plugin directory does not exist: {path}")
        if not path.is_dir():
            raise PepperpyError(f"Plugin directory is not a directory: {path}")
        if path not in self._plugin_dirs:
            self._plugin_dirs.append(path)

    def discover_plugins(self) -> List[str]:
        """Discover plugins in the plugin directories.

        Returns:
            A list of discovered plugin names
        """
        discovered_plugins = []

        for plugin_dir in self._plugin_dirs:
            # Add the plugin directory to the Python path
            sys.path.insert(0, str(plugin_dir))

            try:
                # Discover all modules in the plugin directory
                for _, name, is_pkg in pkgutil.iter_modules([str(plugin_dir)]):
                    if is_pkg and name.startswith("pepperpy_plugin_"):
                        try:
                            # Import the plugin module
                            module = importlib.import_module(name)
                            self._plugin_modules[name] = module
                            discovered_plugins.append(name)
                        except ImportError as e:
                            logger.error(f"Failed to import plugin {name}: {e}")
            finally:
                # Remove the plugin directory from the Python path
                if str(plugin_dir) in sys.path:
                    sys.path.remove(str(plugin_dir))

        return discovered_plugins

    def register_plugin(self, plugin: Plugin) -> None:
        """Register a plugin.

        Args:
            plugin: The plugin to register

        Raises:
            PepperpyError: If a plugin with the same name is already registered
        """
        name = plugin.info.name
        if name in self._plugins:
            raise PepperpyError(f"Plugin already registered: {name}")

        self._plugins[name] = plugin
        logger.info(f"Registered plugin: {name} (v{plugin.info.version})")

    def unregister_plugin(self, name: str) -> None:
        """Unregister a plugin.

        Args:
            name: The name of the plugin to unregister

        Raises:
            PepperpyError: If the plugin is not registered
        """
        if name not in self._plugins:
            raise PepperpyError(f"Plugin not registered: {name}")

        plugin = self._plugins[name]
        if plugin.info.state == PluginState.ENABLED:
            self.disable_plugin(name)

        del self._plugins[name]
        logger.info(f"Unregistered plugin: {name}")

    def enable_plugin(self, name: str) -> None:
        """Enable a plugin.

        Args:
            name: The name of the plugin to enable

        Raises:
            PepperpyError: If the plugin is not registered or already enabled
        """
        if name not in self._plugins:
            raise PepperpyError(f"Plugin not registered: {name}")

        plugin = self._plugins[name]
        if plugin.info.state == PluginState.ENABLED:
            logger.warning(f"Plugin already enabled: {name}")
            return

        try:
            # Initialize the plugin
            plugin.initialize()

            # Register plugin hooks
            hooks = plugin.register_hooks()
            for hook_name, callables in hooks.items():
                if hook_name not in self._hooks:
                    self._hooks[hook_name] = []
                self._hooks[hook_name].extend(callables)

            # Update plugin state
            plugin.info.state = PluginState.ENABLED
            plugin.info.error = None
            logger.info(f"Enabled plugin: {name}")
        except Exception as e:
            plugin.info.state = PluginState.ERROR
            plugin.info.error = str(e)
            logger.error(f"Failed to enable plugin {name}: {e}")
            raise PepperpyError(f"Failed to enable plugin {name}: {e}")

    def disable_plugin(self, name: str) -> None:
        """Disable a plugin.

        Args:
            name: The name of the plugin to disable

        Raises:
            PepperpyError: If the plugin is not registered or already disabled
        """
        if name not in self._plugins:
            raise PepperpyError(f"Plugin not registered: {name}")

        plugin = self._plugins[name]
        if plugin.info.state == PluginState.DISABLED:
            logger.warning(f"Plugin already disabled: {name}")
            return

        try:
            # Shutdown the plugin
            plugin.shutdown()

            # Unregister plugin hooks
            hooks = plugin.register_hooks()
            for hook_name, callables in hooks.items():
                if hook_name in self._hooks:
                    for callable_func in callables:
                        if callable_func in self._hooks[hook_name]:
                            self._hooks[hook_name].remove(callable_func)

            # Update plugin state
            plugin.info.state = PluginState.DISABLED
            plugin.info.error = None
            logger.info(f"Disabled plugin: {name}")
        except Exception as e:
            plugin.info.state = PluginState.ERROR
            plugin.info.error = str(e)
            logger.error(f"Failed to disable plugin {name}: {e}")
            raise PepperpyError(f"Failed to disable plugin {name}: {e}")

    def get_plugin(self, name: str) -> Plugin:
        """Get a plugin by name.

        Args:
            name: The name of the plugin to get

        Returns:
            The plugin instance

        Raises:
            PepperpyError: If the plugin is not registered
        """
        if name not in self._plugins:
            raise PepperpyError(f"Plugin not registered: {name}")
        return self._plugins[name]

    def has_plugin(self, name: str) -> bool:
        """Check if a plugin is registered.

        Args:
            name: The name of the plugin to check

        Returns:
            True if the plugin is registered, False otherwise
        """
        return name in self._plugins

    def is_plugin_enabled(self, name: str) -> bool:
        """Check if a plugin is enabled.

        Args:
            name: The name of the plugin to check

        Returns:
            True if the plugin is enabled, False otherwise

        Raises:
            PepperpyError: If the plugin is not registered
        """
        if name not in self._plugins:
            raise PepperpyError(f"Plugin not registered: {name}")
        return self._plugins[name].info.state == PluginState.ENABLED

    def get_hooks(self, hook_name: str) -> List[Callable]:
        """Get all hooks for a hook name.

        Args:
            hook_name: The name of the hook to get

        Returns:
            A list of callables for the hook
        """
        return self._hooks.get(hook_name, [])

    def register_hook(self, hook_name: str, callable_func: Callable) -> None:
        """Register a hook.

        Args:
            hook_name: The name of the hook to register
            callable_func: The callable to register for the hook
        """
        if hook_name not in self._hooks:
            self._hooks[hook_name] = []
        self._hooks[hook_name].append(callable_func)

    def unregister_hook(self, hook_name: str, callable_func: Callable) -> None:
        """Unregister a hook.

        Args:
            hook_name: The name of the hook to unregister
            callable_func: The callable to unregister for the hook

        Raises:
            PepperpyError: If the hook is not registered
        """
        if hook_name not in self._hooks:
            raise PepperpyError(f"Hook not registered: {hook_name}")
        if callable_func not in self._hooks[hook_name]:
            raise PepperpyError(f"Callable not registered for hook: {hook_name}")
        self._hooks[hook_name].remove(callable_func)

    def call_hooks(self, hook_name: str, *args: Any, **kwargs: Any) -> List[Any]:
        """Call all hooks for a hook name.

        Args:
            hook_name: The name of the hook to call
            *args: Positional arguments to pass to the hooks
            **kwargs: Keyword arguments to pass to the hooks

        Returns:
            A list of results from the hooks
        """
        results = []
        for callable_func in self.get_hooks(hook_name):
            try:
                result = callable_func(*args, **kwargs)
                results.append(result)
            except Exception as e:
                logger.error(f"Error calling hook {hook_name}: {e}")
        return results

    async def call_hooks_async(
        self, hook_name: str, *args: Any, **kwargs: Any
    ) -> List[Any]:
        """Call all hooks for a hook name asynchronously.

        Args:
            hook_name: The name of the hook to call
            *args: Positional arguments to pass to the hooks
            **kwargs: Keyword arguments to pass to the hooks

        Returns:
            A list of results from the hooks
        """
        import asyncio

        results = []
        for callable_func in self.get_hooks(hook_name):
            try:
                if asyncio.iscoroutinefunction(callable_func):
                    result = await callable_func(*args, **kwargs)
                else:
                    result = callable_func(*args, **kwargs)
                results.append(result)
            except Exception as e:
                logger.error(f"Error calling async hook {hook_name}: {e}")
        return results

    def clear_hooks(self) -> None:
        """Clear all hooks."""
        self._hooks.clear()

    def clear_plugins(self) -> None:
        """Clear all plugins."""
        # Disable all plugins first
        for name in list(self._plugins.keys()):
            try:
                if self.is_plugin_enabled(name):
                    self.disable_plugin(name)
            except Exception as e:
                logger.error(f"Error disabling plugin {name}: {e}")

        # Clear plugins
        self._plugins.clear()
        self._hooks.clear()


# Global plugin manager instance
_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """Get the global plugin manager instance.

    Returns:
        The global plugin manager instance
    """
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager


def set_plugin_manager(plugin_manager: PluginManager) -> None:
    """Set the global plugin manager instance.

    Args:
        plugin_manager: The plugin manager instance to set
    """
    global _plugin_manager
    _plugin_manager = plugin_manager


def register_plugin(plugin: Plugin) -> None:
    """Register a plugin.

    Args:
        plugin: The plugin to register
    """
    get_plugin_manager().register_plugin(plugin)


def unregister_plugin(name: str) -> None:
    """Unregister a plugin.

    Args:
        name: The name of the plugin to unregister
    """
    get_plugin_manager().unregister_plugin(name)


def enable_plugin(name: str) -> None:
    """Enable a plugin.

    Args:
        name: The name of the plugin to enable
    """
    get_plugin_manager().enable_plugin(name)


def disable_plugin(name: str) -> None:
    """Disable a plugin.

    Args:
        name: The name of the plugin to disable
    """
    get_plugin_manager().disable_plugin(name)


def get_plugin(name: str) -> Plugin:
    """Get a plugin by name.

    Args:
        name: The name of the plugin to get

    Returns:
        The plugin instance
    """
    return get_plugin_manager().get_plugin(name)


def has_plugin(name: str) -> bool:
    """Check if a plugin is registered.

    Args:
        name: The name of the plugin to check

    Returns:
        True if the plugin is registered, False otherwise
    """
    return get_plugin_manager().has_plugin(name)


def is_plugin_enabled(name: str) -> bool:
    """Check if a plugin is enabled.

    Args:
        name: The name of the plugin to check

    Returns:
        True if the plugin is enabled, False otherwise
    """
    return get_plugin_manager().is_plugin_enabled(name)


def get_plugins() -> Dict[str, Plugin]:
    """Get all registered plugins.

    Returns:
        A dictionary mapping plugin names to plugin instances
    """
    return get_plugin_manager().plugins


def get_enabled_plugins() -> Dict[str, Plugin]:
    """Get all enabled plugins.

    Returns:
        A dictionary mapping plugin names to plugin instances
    """
    return get_plugin_manager().enabled_plugins


def get_disabled_plugins() -> Dict[str, Plugin]:
    """Get all disabled plugins.

    Returns:
        A dictionary mapping plugin names to plugin instances
    """
    return get_plugin_manager().disabled_plugins


def add_plugin_dir(plugin_dir: Union[str, Path]) -> None:
    """Add a plugin directory.

    Args:
        plugin_dir: The plugin directory to add
    """
    get_plugin_manager().add_plugin_dir(plugin_dir)


def discover_plugins() -> List[str]:
    """Discover plugins in the plugin directories.

    Returns:
        A list of discovered plugin names
    """
    return get_plugin_manager().discover_plugins()


def register_hook(hook_name: str, callable_func: Callable) -> None:
    """Register a hook.

    Args:
        hook_name: The name of the hook to register
        callable_func: The callable to register for the hook
    """
    get_plugin_manager().register_hook(hook_name, callable_func)


def unregister_hook(hook_name: str, callable_func: Callable) -> None:
    """Unregister a hook.

    Args:
        hook_name: The name of the hook to unregister
        callable_func: The callable to unregister for the hook
    """
    get_plugin_manager().unregister_hook(hook_name, callable_func)


def get_hooks(hook_name: str) -> List[Callable]:
    """Get all hooks for a hook name.

    Args:
        hook_name: The name of the hook to get

    Returns:
        A list of callables for the hook
    """
    return get_plugin_manager().get_hooks(hook_name)


def call_hooks(hook_name: str, *args: Any, **kwargs: Any) -> List[Any]:
    """Call all hooks for a hook name.

    Args:
        hook_name: The name of the hook to call
        *args: Positional arguments to pass to the hooks
        **kwargs: Keyword arguments to pass to the hooks

    Returns:
        A list of results from the hooks
    """
    return get_plugin_manager().call_hooks(hook_name, *args, **kwargs)


async def call_hooks_async(hook_name: str, *args: Any, **kwargs: Any) -> List[Any]:
    """Call all hooks for a hook name asynchronously.

    Args:
        hook_name: The name of the hook to call
        *args: Positional arguments to pass to the hooks
        **kwargs: Keyword arguments to pass to the hooks

    Returns:
        A list of results from the hooks
    """
    return await get_plugin_manager().call_hooks_async(hook_name, *args, **kwargs)


def clear_hooks() -> None:
    """Clear all hooks."""
    get_plugin_manager().clear_hooks()


def clear_plugins() -> None:
    """Clear all plugins."""
    get_plugin_manager().clear_plugins()


class PluginDecorator:
    """Decorator for creating plugins.

    This decorator simplifies the creation of plugins by automatically
    generating the required methods and properties.
    """

    def __init__(
        self,
        name: str,
        version: str,
        description: str,
        author: str,
        license: str,
        url: Optional[str] = None,
        dependencies: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
    ):
        """Initialize the plugin decorator.

        Args:
            name: The name of the plugin
            version: The version of the plugin
            description: The description of the plugin
            author: The author of the plugin
            license: The license of the plugin
            url: The URL of the plugin
            dependencies: The dependencies of the plugin
            tags: The tags of the plugin
        """
        self.info = PluginInfo(
            name=name,
            version=version,
            description=description,
            author=author,
            license=license,
            url=url,
            dependencies=dependencies or [],
            tags=tags or [],
        )
        self.hooks: Dict[str, List[Callable]] = {}

    def __call__(self, cls: Type) -> Type:
        """Call the decorator.

        Args:
            cls: The class to decorate

        Returns:
            The decorated class
        """
        # Create a new class that inherits from both the original class and Plugin
        if not issubclass(cls, Plugin):
            original_init = cls.__init__

            class PluginWrapper(cls, Plugin):  # type: ignore
                @property
                def info(self) -> PluginInfo:
                    return self._info

                def __init__(self, *args: Any, **kwargs: Any):
                    self._info = PluginInfo(
                        name=self.decorator.info.name,
                        version=self.decorator.info.version,
                        description=self.decorator.info.description,
                        author=self.decorator.info.author,
                        license=self.decorator.info.license,
                        url=self.decorator.info.url,
                        dependencies=self.decorator.info.dependencies,
                        tags=self.decorator.info.tags,
                    )
                    original_init(self, *args, **kwargs)

                def initialize(self) -> None:
                    if hasattr(self, "on_initialize"):
                        self.on_initialize()

                def shutdown(self) -> None:
                    if hasattr(self, "on_shutdown"):
                        self.on_shutdown()

                def register_hooks(self) -> Dict[str, List[Callable]]:
                    return self.decorator.hooks

            PluginWrapper.decorator = self
            return PluginWrapper
        else:
            # If the class already inherits from Plugin, just add the hooks
            original_register_hooks = cls.register_hooks

            def register_hooks(self) -> Dict[str, List[Callable]]:
                hooks = original_register_hooks(self)
                hooks.update(self.decorator.hooks)
                return hooks

            cls.register_hooks = register_hooks  # type: ignore
            cls.decorator = self  # type: ignore
            return cls

    def hook(self, hook_name: str) -> Callable[[Callable], Callable]:
        """Decorator for registering a hook.

        Args:
            hook_name: The name of the hook to register

        Returns:
            A decorator function
        """

        def decorator(func: Callable) -> Callable:
            if hook_name not in self.hooks:
                self.hooks[hook_name] = []
            self.hooks[hook_name].append(func)
            return func

        return decorator
