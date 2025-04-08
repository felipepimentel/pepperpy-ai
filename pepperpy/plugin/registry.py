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

        # Register the plugin with the provided name
        self._plugins[domain][name] = {
            "class": plugin_class,
            "meta": meta or {},
        }

        # For workflow plugins, also register without the domain prefix for compatibility
        if domain == "workflow" and "/" in name:
            # Extract the name without the domain prefix (after the slash)
            clean_name = name.split("/", 1)[1]

            # Also register with just the name part for direct lookup
            self._plugins[domain][clean_name] = {
                "class": plugin_class,
                "meta": meta or {},
            }
            logger.info(f"Registered plugin: {domain}/{name} (also as {clean_name})")
        else:
            logger.info(f"Registered plugin: {domain}/{name}")

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

        # Debug info about what we're looking for
        logger.info(f"Looking for plugin: {domain}/{name}")
        logger.info(f"Available keys in {domain}: {list(self._plugins[domain].keys())}")

        # Check if the plugin exists with the exact name
        if name in self._plugins[domain]:
            logger.info(f"Found plugin with exact match: {domain}/{name}")
            return self._plugins[domain][name]["class"]

        # Special case for workflow plugins: try different formats
        if domain == "workflow":
            # If name contains a slash, try the part after the slash
            if "/" in name:
                clean_name = name.split("/", 1)[1]
                logger.info(f"Trying with clean name: {clean_name}")
                if clean_name in self._plugins[domain]:
                    logger.info(f"Found plugin with clean name: {domain}/{clean_name}")
                    return self._plugins[domain][clean_name]["class"]

            # Try with workflow/ prefix if not already prefixed
            if not name.startswith("workflow/"):
                prefixed_name = f"workflow/{name}"
                logger.info(f"Trying with prefixed name: {prefixed_name}")
                if prefixed_name in self._plugins[domain]:
                    logger.info(
                        f"Found plugin with prefixed name: {domain}/{prefixed_name}"
                    )
                    return self._plugins[domain][prefixed_name]["class"]

        logger.warning(f"Plugin not found: {domain}/{name}")
        return None

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
_registry_instance = plugin_registry  # Create a separate reference

def get_registry() -> PluginRegistry:
    """Get the global plugin registry instance.
    
    Returns:
        The global plugin registry instance
    """
    global _registry_instance
    return _registry_instance


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
    registry = get_registry()
    registry.register_plugin(domain, name, plugin_class, meta)


def get_plugin(domain: str, name: str) -> Any | None:
    """Get a plugin class.

    Args:
        domain: Plugin domain
        name: Plugin name

    Returns:
        Plugin class or None if not found
    """
    registry = get_registry()
    return registry.get_plugin(domain, name)


def get_plugin_metadata(domain: str, name: str) -> dict[str, Any]:
    """Get plugin metadata.

    Args:
        domain: Plugin domain
        name: Plugin name

    Returns:
        Plugin metadata or empty dict if not found
    """
    registry = get_registry()
    return registry.get_plugin_metadata(domain, name)


def list_plugins(domain: str | None = None) -> dict[str, Any]:
    """List available plugins.

    Args:
        domain: Optional domain to filter by

    Returns:
        Dictionary of available plugins
    """
    registry = get_registry()
    return registry.list_plugins(domain)
