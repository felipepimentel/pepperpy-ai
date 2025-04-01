"""Plugin manager for PepperPy."""

import os
from typing import Any, Dict, Optional, Type

from pepperpy.core.errors import ValidationError
from pepperpy.core.logging import get_logger
from pepperpy.plugins.discovery import (
    get_plugin_by_provider,
)
from pepperpy.plugins.plugin import PepperpyPlugin

logger = get_logger(__name__)


class PluginManager:
    """Manager for PepperPy plugins."""

    def __init__(self) -> None:
        """Initialize plugin manager."""
        self._plugins: Dict[str, Dict[str, Type[PepperpyPlugin]]] = {}
        self._instances: Dict[str, Dict[str, PepperpyPlugin]] = {}
        self._initialized = False

    def register_plugin(
        self, plugin_type: str, provider_type: str, plugin_class: Type[PepperpyPlugin]
    ) -> None:
        """Register a plugin.

        Args:
            plugin_type: Type of plugin (e.g., "llm", "rag")
            provider_type: Type of provider (e.g., "openai", "local")
            plugin_class: Plugin class to register
        """
        if plugin_type not in self._plugins:
            self._plugins[plugin_type] = {}
        self._plugins[plugin_type][provider_type] = plugin_class
        logger.debug(f"Registered plugin: {plugin_type}/{provider_type}")

    def get_plugin(
        self, plugin_type: str, provider_type: str
    ) -> Optional[Type[PepperpyPlugin]]:
        """Get a plugin class.

        Args:
            plugin_type: Type of plugin
            provider_type: Type of provider

        Returns:
            Plugin class if found, None otherwise
        """
        return self._plugins.get(plugin_type, {}).get(provider_type)

    def create_instance(
        self, plugin_type: str, provider_type: str, **config: Any
    ) -> PepperpyPlugin:
        """Create a plugin instance.

        Args:
            plugin_type: Type of plugin
            provider_type: Type of provider
            **config: Plugin configuration

        Returns:
            Plugin instance

        Raises:
            ValidationError: If plugin not found or creation fails
        """
        # Get plugin class
        plugin_class = self.get_plugin(plugin_type, provider_type)
        if not plugin_class:
            raise ValidationError(f"Plugin not found: {plugin_type}/{provider_type}")

        # Create instance
        try:
            instance = plugin_class(**config)
            if plugin_type not in self._instances:
                self._instances[plugin_type] = {}
            self._instances[plugin_type][provider_type] = instance
            return instance
        except Exception as e:
            raise ValidationError(f"Failed to create plugin instance: {e}") from e

    def get_instance(
        self, plugin_type: str, provider_type: str
    ) -> Optional[PepperpyPlugin]:
        """Get a plugin instance.

        Args:
            plugin_type: Type of plugin
            provider_type: Type of provider

        Returns:
            Plugin instance if found, None otherwise
        """
        return self._instances.get(plugin_type, {}).get(provider_type)

    async def initialize(self) -> None:
        """Initialize plugin manager."""
        if self._initialized:
            return

        # Initialize all instances
        for instances in self._instances.values():
            for instance in instances.values():
                await instance.initialize()

        self._initialized = True

    async def cleanup(self) -> None:
        """Clean up plugin manager."""
        # Clean up all instances
        for instances in self._instances.values():
            for instance in instances.values():
                await instance.cleanup()

        self._instances.clear()
        self._initialized = False


# Global plugin manager instance
_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """Get the global plugin manager.

    Returns:
        Plugin manager instance
    """
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager


def create_provider_instance(
    plugin_type: str,
    provider_type: Optional[str] = None,
    **config: Any,
) -> PepperpyPlugin:
    """Create a provider instance.

    This is the main factory function for creating provider instances.
    It handles provider type resolution from environment variables and
    plugin discovery.

    Args:
        plugin_type: Type of plugin (e.g., "llm", "rag")
        provider_type: Type of provider (default from env or discovery)
        **config: Provider configuration

    Returns:
        Provider instance

    Raises:
        ValidationError: If provider creation fails
    """
    # Get provider type from environment if not specified
    if provider_type is None:
        env_key = f"PEPPERPY_{plugin_type.upper()}__PROVIDER"
        provider_type = os.environ.get(env_key)

    if not provider_type:
        raise ValidationError(
            f"Provider type not specified for {plugin_type} " f"and {env_key} not set"
        )

    # Get plugin class
    plugin_class = get_plugin_by_provider(plugin_type, provider_type)
    if not plugin_class:
        raise ValidationError(f"Provider not found: {plugin_type}/{provider_type}")

    # Create instance
    try:
        instance = plugin_class(**config)
        return instance
    except Exception as e:
        raise ValidationError(f"Failed to create provider instance: {e}") from e
