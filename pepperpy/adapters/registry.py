"""Adapter registry module.
from pepperpy.adapters.base import BaseAdapter

This module provides a registry for adapter plugins and adapter classes.
"""

from typing import Any, Dict, Optional, Type

from pepperpy.adapters.types import AdapterType
from pepperpy.core.logging import get_logger

logger = get_logger(__name__)


class AdapterRegistry:
    """Registry for adapter plugins and adapter classes."""

    _instance = None
    _adapters: Dict[str, Type["BaseAdapter"]] = {}
    _plugins: Dict[str, Dict[str, Any]] = {}

    def __new__(cls):
        """Ensure singleton instance."""
        if cls._instance is None:
            cls._instance = super(AdapterRegistry, cls).__new__(cls)
        return cls._instance

    def register_adapter(
        self, adapter_id: str, adapter_class: Type["BaseAdapter"]
    ) -> None:
        """Register an adapter class with the registry.

        Args:
            adapter_id: Unique identifier for the adapter
            adapter_class: The adapter class to register
        """
        if adapter_id in self._adapters:
            logger.warning(f"Adapter {adapter_id} already registered, overwriting")

        self._adapters[adapter_id] = adapter_class
        logger.debug(f"Registered adapter: {adapter_id}")

    def register_plugin(self, plugin_id: str, plugin_info: Dict[str, Any]) -> None:
        """Register an adapter plugin with the registry.

        Args:
            plugin_id: Unique identifier for the plugin
            plugin_info: Plugin metadata and configuration
        """
        if plugin_id in self._plugins:
            logger.warning(f"Plugin {plugin_id} already registered, overwriting")

        self._plugins[plugin_id] = plugin_info
        logger.debug(f"Registered adapter plugin: {plugin_id}")

    def get_adapter(self, adapter_id: str) -> Optional[Type["BaseAdapter"]]:
        """Get an adapter class by ID.

        Args:
            adapter_id: Unique identifier for the adapter

        Returns:
            The adapter class if found, None otherwise
        """
        return self._adapters.get(adapter_id)

    def get_adapters(self) -> Dict[str, Type["BaseAdapter"]]:
        """Get all registered adapter classes.

        Returns:
            Dictionary mapping adapter IDs to adapter classes
        """
        return self._adapters.copy()

    def get_plugin(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """Get an adapter plugin by ID.

        Args:
            plugin_id: Unique identifier for the plugin

        Returns:
            Plugin information if found, None otherwise
        """
        return self._plugins.get(plugin_id)

    def get_plugins(self) -> Dict[str, Dict[str, Any]]:
        """Get all registered adapter plugins.

        Returns:
            Dictionary mapping plugin IDs to plugin information
        """
        return self._plugins.copy()

    def get_adapters_by_type(
        self, adapter_type: AdapterType
    ) -> Dict[str, Type["BaseAdapter"]]:
        """Get all adapters of a specific type.

        Args:
            adapter_type: The type of adapter to filter by

        Returns:
            Dictionary mapping adapter IDs to adapter classes
        """
        return {
            adapter_id: adapter_class
            for adapter_id, adapter_class in self._adapters.items()
            if hasattr(adapter_class, "adapter_type")
            and adapter_class.adapter_type == adapter_type
        }

    def clear(self) -> None:
        """Clear all registered adapters and plugins."""
        self._adapters.clear()
        self._plugins.clear()
        logger.debug("Cleared adapter registry")


# Circular import prevention
