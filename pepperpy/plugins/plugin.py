"""PepperPy plugin base class.

This module provides the base plugin class and decorators for PepperPy plugins,
including configuration handling and lifecycle management.
"""

import asyncio
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import (
    Any,
    ClassVar,
    Dict,
    Optional,
    Self,
    Set,
    TypeVar,
)

from pepperpy.core.logging import get_logger
from pepperpy.plugins.resources import ResourceMixin

logger = get_logger(__name__)

# Global tracking for active plugins and instances in singleton mode
_singleton_instances: Dict[str, "PepperpyPlugin"] = {}
_active_plugins: Set[str] = set()
_auto_context_enabled = True

# Flag to track if we're inside an async context manager
_inside_context = False
_exiting_plugins: Set["PepperpyPlugin"] = set()

T = TypeVar("T", bound="PepperpyPlugin")


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

        # Load from environment if not explicitly provided
        self._load_from_environment()

    def _load_from_environment(self) -> None:
        """Load configuration from environment variables."""
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

    def as_dict(self) -> Dict[str, Any]:
        """Get configuration as dictionary.

        Returns:
            Dictionary of configuration values
        """
        return dict(self._config)

    def with_defaults(self, defaults: Dict[str, Any]) -> "PluginConfig":
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


class PepperpyPlugin(ResourceMixin):
    """Base class for all PepperPy plugins."""

    # Plugin metadata
    plugin_type: ClassVar[str] = ""
    provider_type: ClassVar[str] = ""

    # Singleton mode control
    _singleton_mode: ClassVar[bool] = False

    def __init__(
        self,
        name: str = "base",
        config: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize plugin with config.

        Args:
            name: Provider name
            config: Configuration dictionary
            **kwargs: Additional configuration parameters
        """
        # Initialize resource mixin
        ResourceMixin.__init__(self)

        # Store name
        self.name = name

        # Merge config and kwargs
        merged_config = {**(config or {}), **kwargs}

        # Create plugin configuration
        self._plugin_config = PluginConfig(
            self.plugin_type, self.provider_type, **merged_config
        )

        # Initialize state
        self._initialized = False
        self._logger = get_logger(
            f"{self.__class__.__module__}.{self.__class__.__name__}"
        )

        # Auto-bind configuration attributes for easy access
        for key, value in merged_config.items():
            if not hasattr(self, key) or getattr(self, key) is None:
                setattr(self, key, value)

        # Register this instance as a singleton if in singleton mode
        if (
            self.__class__._singleton_mode
            and self.plugin_id not in _singleton_instances
        ):
            _singleton_instances[self.plugin_id] = self

    @property
    def plugin_id(self) -> str:
        """Get unique plugin ID.

        Returns:
            Plugin ID string
        """
        return f"{self.plugin_type}/{self.provider_type}"

    @property
    def config(self) -> Dict[str, Any]:
        """Get plugin configuration.

        Returns:
            Configuration dictionary
        """
        return self._plugin_config.as_dict()

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key.

        Args:
            key: Configuration key
            default: Default value if key is not found

        Returns:
            Configuration value or default
        """
        return self._plugin_config.get(key, default)

    @property
    def initialized(self) -> bool:
        """Check if plugin is initialized.

        Returns:
            True if initialized, False otherwise
        """
        return self._initialized

    @initialized.setter
    def initialized(self, value: bool) -> None:
        """Set initialized state.

        Args:
            value: New initialized state
        """
        self._initialized = value

    @property
    def logger(self) -> Any:
        """Get plugin logger.

        Returns:
            Logger instance
        """
        return self._logger

    async def initialize(self) -> None:
        """Initialize the plugin.

        This should be overridden by plugin implementations to
        perform any initialization that needs to happen before use.
        """
        self._initialized = True

    async def cleanup(self) -> None:
        """Clean up plugin resources.

        This should be overridden by plugin implementations to
        release any resources they acquired during use.
        """
        # Clean up any registered resources
        await self._cleanup_resources()
        self._initialized = False

    async def __aenter__(self) -> Self:
        """Enter async context manager.

        Returns:
            Self for chaining
        """
        global _inside_context
        _inside_context = True

        # Add to active plugins set
        _active_plugins.add(self.plugin_id)

        if not self.initialized:
            await self.initialize()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context manager."""
        global _inside_context
        _inside_context = False

        # Prevent duplicate cleanup in nested context managers
        if self in _exiting_plugins:
            return

        _exiting_plugins.add(self)
        try:
            await self.cleanup()
        finally:
            _exiting_plugins.remove(self)
            _active_plugins.discard(self.plugin_id)

    async def _ensure_initialized(self) -> None:
        """Ensure the plugin is initialized."""
        if not self.initialized:
            await self.initialize()


# Decorator to automatically ensure plugin is initialized before method call
def auto_initialize(func):
    """Decorator to ensure plugin is initialized before method call."""
    if not asyncio.iscoroutinefunction(func):
        # For synchronous functions, we can't await, so we just call the function
        return func

    async def wrapper(self, *args, **kwargs):
        if isinstance(self, PepperpyPlugin):
            await self._ensure_initialized()
        return await func(self, *args, **kwargs)

    # Update metadata to match original function
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    wrapper.__module__ = func.__module__
    wrapper.__qualname__ = func.__qualname__

    return wrapper


# Decorator to automatically wrap a method in an async context manager
def auto_context(func):
    """Decorator to automatically wrap a method in an async context manager."""
    if not asyncio.iscoroutinefunction(func):
        # For synchronous functions, we can't await, so we just call the function
        return func

    async def wrapper(self, *args, **kwargs):
        if not isinstance(self, PepperpyPlugin) or not _auto_context_enabled:
            # If not a plugin or auto context is disabled, just call the function
            return await func(self, *args, **kwargs)

        if _inside_context:
            # Already inside a context manager, just call the function
            return await func(self, *args, **kwargs)

        # Create a new context manager and call the function inside it
        async with self:
            return await func(self, *args, **kwargs)

    # Update metadata to match original function
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    wrapper.__module__ = func.__module__
    wrapper.__qualname__ = func.__qualname__

    return wrapper


# Utility to create a plugin provider
@asynccontextmanager
async def with_provider(
    plugin_type: str, provider_type: str, **config: Any
) -> AsyncGenerator[PepperpyPlugin, None]:
    """Create and use a plugin provider with a context manager.

    Args:
        plugin_type: Type of plugin
        provider_type: Type of provider
        **config: Provider configuration

    Yields:
        Provider instance
    """
    from pepperpy.plugins.registry import create_provider_instance

    provider = create_provider_instance(plugin_type, provider_type, **config)
    async with provider:
        yield provider
