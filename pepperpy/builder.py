"""
Fluent Builder Pattern for PepperPy.

This module implements the builder pattern for PepperPy,
providing a fluent API for configuring and using plugins and providers.
"""

import asyncio
from typing import Any, Callable, Dict, Generic, List, Optional, Type, TypeVar, cast

from pepperpy.core.logging import get_logger
from pepperpy.plugins.lazy import LazyPlugin
from pepperpy.plugins.plugin import PepperpyPlugin
from pepperpy.plugins.validation import ValidationLevel, validate_plugin

T = TypeVar("T", bound=PepperpyPlugin)
P = TypeVar("P", bound=PepperpyPlugin)  # Changed from ProviderPlugin to PepperpyPlugin

logger = get_logger(__name__)


class PluginBuilder(Generic[T]):
    """Builder for generic plugins."""

    def __init__(self, plugin_class: Type[T], plugin_id: str, plugin_type: str):
        """Initialize plugin builder.

        Args:
            plugin_class: Plugin class
            plugin_id: Plugin ID
            plugin_type: Plugin type
        """
        self._plugin_class = plugin_class
        self._plugin_id = plugin_id
        self._plugin_type = plugin_type
        self._config: Dict[str, Any] = {}
        self._initialized = False
        self._instance: Optional[T] = None
        self._auto_initialize = True
        self._validators: List[Callable[[T], None]] = []

    def with_config(self, **kwargs: Any) -> "PluginBuilder[T]":
        """Set configuration options for the plugin.

        Args:
            **kwargs: Configuration options

        Returns:
            Self for chaining
        """
        self._config.update(kwargs)
        return self

    def with_api_key(self, api_key: str) -> "PluginBuilder[T]":
        """Set API key for the plugin.

        Args:
            api_key: API key

        Returns:
            Self for chaining
        """
        self._config["api_key"] = api_key
        return self

    def with_endpoint(self, endpoint: str) -> "PluginBuilder[T]":
        """Set endpoint URL for the plugin.

        Args:
            endpoint: Endpoint URL

        Returns:
            Self for chaining
        """
        self._config["endpoint"] = endpoint
        return self

    def with_auto_initialize(self, auto_initialize: bool) -> "PluginBuilder[T]":
        """Set auto initialization behavior.

        Args:
            auto_initialize: Whether to automatically initialize the plugin

        Returns:
            Self for chaining
        """
        self._auto_initialize = auto_initialize
        return self

    def add_validator(self, validator: Callable[[T], None]) -> "PluginBuilder[T]":
        """Add a custom validator function.

        Args:
            validator: Validator function that accepts the plugin instance

        Returns:
            Self for chaining
        """
        self._validators.append(validator)
        return self

    async def validate(self) -> bool:
        """Validate the plugin configuration.

        Returns:
            True if validation passed, False otherwise
        """
        # Get an instance for validation
        instance = await self.build(initialize=False)

        # Run validation
        validation_result = validate_plugin(
            type(instance),
            self._plugin_type,
            self._plugin_id,
            getattr(type(instance), "__metadata__", {}),
        )

        # Check if validation passed
        valid = validation_result.valid

        # Log validation issues
        if validation_result.has_warnings or validation_result.has_info:
            logger.info(
                f"Validation results for {self._plugin_id}:\n"
                + validation_result.format_issues(
                    [ValidationLevel.WARNING, ValidationLevel.INFO]
                )
            )

        # Run custom validators
        try:
            for validator in self._validators:
                validator(instance)
        except Exception as e:
            logger.error(f"Custom validation failed for {self._plugin_id}: {e}")
            valid = False

        return valid

    async def build(self, initialize: Optional[bool] = None) -> T:
        """Build and return the plugin instance.

        Args:
            initialize: Whether to initialize the plugin,
                       or None to use auto_initialize setting

        Returns:
            Plugin instance
        """
        should_initialize = self._auto_initialize if initialize is None else initialize

        # Return existing instance if already built
        if self._instance and (not should_initialize or self._initialized):
            return self._instance

        # Create new instance
        if not self._instance:
            # Pass the config dictionary through the config parameter
            self._instance = self._plugin_class(config=self._config)

        # Initialize if needed
        if should_initialize and not self._initialized:
            # Check if initialize is async
            if asyncio.iscoroutinefunction(self._instance.initialize):
                # Properly await the async function
                await self._instance.initialize()  # type: ignore
            else:
                self._instance.initialize()

            self._initialized = True

        return self._instance

    async def lazy_build(self) -> T:
        """Build a lazy-loading version of the plugin.

        Returns:
            Lazy-loading plugin instance
        """
        # Create a lazy plugin wrapper
        lazy_instance = LazyPlugin(
            plugin_id=self._plugin_id,
            plugin_type=self._plugin_type,
            plugin_class=self._plugin_class,
            config=self._config,
        )

        return cast(T, lazy_instance)


class ProviderBuilder(PluginBuilder[P]):
    """Builder for provider plugins."""

    def __init__(self, provider_class: Type[P], provider_id: str, provider_type: str):
        """Initialize provider builder.

        Args:
            provider_class: Provider class
            provider_id: Provider ID
            provider_type: Provider type
        """
        super().__init__(provider_class, provider_id, provider_type)

    def with_model(self, model: str) -> "ProviderBuilder[P]":
        """Set model for the provider.

        Args:
            model: Model name or ID

        Returns:
            Self for chaining
        """
        self._config["model"] = model
        return self

    def with_timeout(self, timeout: float) -> "ProviderBuilder[P]":
        """Set timeout for the provider.

        Args:
            timeout: Timeout in seconds

        Returns:
            Self for chaining
        """
        self._config["timeout"] = timeout
        return self

    def with_retry(
        self, max_retries: int, backoff: float = 1.0
    ) -> "ProviderBuilder[P]":
        """Set retry behavior for the provider.

        Args:
            max_retries: Maximum number of retries
            backoff: Backoff factor

        Returns:
            Self for chaining
        """
        self._config["max_retries"] = max_retries
        self._config["retry_backoff"] = backoff
        return self


class PluginManager:
    """Manager for plugin builders and instances."""

    def __init__(self):
        """Initialize plugin manager."""
        self._plugin_builders: Dict[str, Dict[str, PluginBuilder[Any]]] = {}
        self._provider_builders: Dict[str, Dict[str, ProviderBuilder[Any]]] = {}

    def register_plugin(
        self, plugin_class: Type[T], plugin_id: str, plugin_type: str
    ) -> PluginBuilder[T]:
        """Register a plugin and get a builder for it.

        Args:
            plugin_class: Plugin class
            plugin_id: Plugin ID
            plugin_type: Plugin type

        Returns:
            Builder for the plugin
        """
        # Create builder
        builder = PluginBuilder(plugin_class, plugin_id, plugin_type)

        # Register plugin builder
        if plugin_type not in self._plugin_builders:
            self._plugin_builders[plugin_type] = {}

        self._plugin_builders[plugin_type][plugin_id] = builder

        return builder

    def register_provider(
        self, provider_class: Type[P], provider_id: str, provider_type: str
    ) -> ProviderBuilder[P]:
        """Register a provider and get a builder for it.

        Args:
            provider_class: Provider class
            provider_id: Provider ID
            provider_type: Provider type

        Returns:
            Builder for the provider
        """
        # Create builder
        builder = ProviderBuilder(provider_class, provider_id, provider_type)

        # Register provider builder
        if provider_type not in self._provider_builders:
            self._provider_builders[provider_type] = {}

        self._provider_builders[provider_type][provider_id] = builder

        return builder

    def get_plugin_builder(
        self, plugin_type: str, plugin_id: str
    ) -> Optional[PluginBuilder[Any]]:
        """Get a builder for a plugin.

        Args:
            plugin_type: Plugin type
            plugin_id: Plugin ID

        Returns:
            Builder for the plugin, or None if not found
        """
        if plugin_type not in self._plugin_builders:
            return None

        return self._plugin_builders[plugin_type].get(plugin_id)

    def get_provider_builder(
        self, provider_type: str, provider_id: str
    ) -> Optional[ProviderBuilder[Any]]:
        """Get a builder for a provider.

        Args:
            provider_type: Provider type
            provider_id: Provider ID

        Returns:
            Builder for the provider, or None if not found
        """
        if provider_type not in self._provider_builders:
            return None

        return self._provider_builders[provider_type].get(provider_id)

    def list_plugin_types(self) -> List[str]:
        """List all registered plugin types.

        Returns:
            List of plugin types
        """
        return list(self._plugin_builders.keys())

    def list_plugins(self, plugin_type: str) -> List[str]:
        """List all registered plugins of a type.

        Args:
            plugin_type: Plugin type

        Returns:
            List of plugin IDs
        """
        if plugin_type not in self._plugin_builders:
            return []

        return list(self._plugin_builders[plugin_type].keys())

    def list_provider_types(self) -> List[str]:
        """List all registered provider types.

        Returns:
            List of provider types
        """
        return list(self._provider_builders.keys())

    def list_providers(self, provider_type: str) -> List[str]:
        """List all registered providers of a type.

        Args:
            provider_type: Provider type

        Returns:
            List of provider IDs
        """
        if provider_type not in self._provider_builders:
            return []

        return list(self._provider_builders[provider_type].keys())

    async def build_plugin(
        self,
        plugin_type: str,
        plugin_id: str,
        config: Optional[Dict[str, Any]] = None,
        lazy: bool = False,
    ) -> Optional[PepperpyPlugin]:
        """Build a plugin instance.

        Args:
            plugin_type: Plugin type
            plugin_id: Plugin ID
            config: Optional configuration
            lazy: Whether to use lazy loading

        Returns:
            Plugin instance, or None if not found
        """
        builder = self.get_plugin_builder(plugin_type, plugin_id)
        if not builder:
            return None

        # Apply config if provided
        if config:
            builder.with_config(**config)

        # Build instance
        if lazy:
            return await builder.lazy_build()
        else:
            return await builder.build()

    async def build_provider(
        self,
        provider_type: str,
        provider_id: str,
        config: Optional[Dict[str, Any]] = None,
        lazy: bool = False,
    ) -> Optional[
        PepperpyPlugin
    ]:  # Changed return type from ProviderPlugin to PepperpyPlugin
        """Build a provider instance.

        Args:
            provider_type: Provider type
            provider_id: Provider ID
            config: Optional configuration
            lazy: Whether to use lazy loading

        Returns:
            Provider instance, or None if not found
        """
        builder = self.get_provider_builder(provider_type, provider_id)
        if not builder:
            return None

        # Apply config if provided
        if config:
            builder.with_config(**config)

        # Build instance
        if lazy:
            return await builder.lazy_build()
        else:
            return await builder.build()


# Singleton instance
_plugin_manager = PluginManager()

# Public API
register_plugin = _plugin_manager.register_plugin
register_provider = _plugin_manager.register_provider
get_plugin_builder = _plugin_manager.get_plugin_builder
get_provider_builder = _plugin_manager.get_provider_builder
list_plugin_types = _plugin_manager.list_plugin_types
list_plugins = _plugin_manager.list_plugins
list_provider_types = _plugin_manager.list_provider_types
list_providers = _plugin_manager.list_providers
build_plugin = _plugin_manager.build_plugin
build_provider = _plugin_manager.build_provider
