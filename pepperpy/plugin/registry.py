"""
PepperPy Plugin Registry.

Core plugin registration and retrieval functionality.
"""

from typing import Any

from pepperpy.core.logging import get_logger

logger = get_logger(__name__)


class PluginRegistry:
    """Registry for PepperPy plugins."""

    def __init__(self) -> None:
        """Initialize plugin registry."""
        self._initialized = False
        self._init()

    def _init(self) -> None:
        """Initialize plugin registry."""
        if self._initialized:
            return

        self._plugins: dict[str, dict[str, dict[str, Any]]] = {
            "llm": {},
            "tts": {},
            "agent": {},
            "tool": {},
            "cache": {},
            "discovery": {},
            "storage": {},
            "rag": {},
            "content": {},
            "embeddings": {},
            "workflow": {},
        }
        self._initialized = True

    def register_plugin(
        self,
        domain: str,
        name: str,
        plugin_class: Any,
        meta: dict[str, Any] | None = None,
    ) -> None:
        """Register a plugin.

        Args:
            domain: Plugin domain (llm, tts, etc.)
            name: Plugin name
            plugin_class: Plugin class
            meta: Plugin metadata
        """
        if domain not in self._plugins:
            self._plugins[domain] = {}

        self._plugins[domain][name] = {
            "class": plugin_class,
            "meta": meta or {},
        }
        logger.info(f"Registered plugin: {domain}.{name}")

    def get_plugin(self, domain: str, name: str) -> Any | None:
        """Get a plugin class.

        Args:
            domain: Plugin domain
            name: Plugin name

        Returns:
            Plugin class or None if not found
        """
        if domain not in self._plugins:
            logger.warning(f"Unknown domain: {domain}")
            return None

        if name not in self._plugins[domain]:
            logger.warning(f"Plugin not found: {domain}.{name}")
            return None

        return self._plugins[domain][name]["class"]

    def get_plugin_metadata(self, domain: str, name: str) -> dict[str, Any]:
        """Get plugin metadata.

        Args:
            domain: Plugin domain
            name: Plugin name

        Returns:
            Plugin metadata or empty dict if not found
        """
        if domain not in self._plugins:
            return {}

        if name not in self._plugins[domain]:
            return {}

        return self._plugins[domain][name].get("meta", {})

    def list_plugins(self, domain: str | None = None) -> dict[str, Any]:
        """List available plugins.

        Args:
            domain: Optional domain to filter by

        Returns:
            Dictionary of available plugins
        """
        if domain:
            if domain not in self._plugins:
                logger.warning(f"Unknown domain: {domain}")
                return {}
            return {name: info["meta"] for name, info in self._plugins[domain].items()}

        # Return all plugins
        result = {}
        for domain, plugins in self._plugins.items():
            result[domain] = {name: info["meta"] for name, info in plugins.items()}
        return result


# Global plugin registry instance
plugin_registry = PluginRegistry()


def register_plugin(
    domain: str,
    name: str,
    plugin_class: Any,
    meta: dict[str, Any] | None = None,
) -> None:
    """Register a plugin.

    Args:
        domain: Plugin domain (llm, tts, etc.)
        name: Plugin name
        plugin_class: Plugin class
        meta: Plugin metadata
    """
    plugin_registry.register_plugin(domain, name, plugin_class, meta)


def get_plugin(domain: str, name: str) -> Any | None:
    """Get a plugin class.

    Args:
        domain: Plugin domain
        name: Plugin name

    Returns:
        Plugin class or None if not found
    """
    return plugin_registry.get_plugin(domain, name)


def get_plugin_metadata(domain: str, name: str) -> dict[str, Any]:
    """Get plugin metadata.

    Args:
        domain: Plugin domain
        name: Plugin name

    Returns:
        Plugin metadata or empty dict if not found
    """
    return plugin_registry.get_plugin_metadata(domain, name)


def list_plugins(domain: str | None = None) -> dict[str, Any]:
    """List available plugins.

    Args:
        domain: Optional domain to filter by

    Returns:
        Dictionary of available plugins
    """
    return plugin_registry.list_plugins(domain)
