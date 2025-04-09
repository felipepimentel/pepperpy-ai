"""
PepperPy Plugin Registry.

Core plugin registration and retrieval functionality.
"""

from typing import Any

from pepperpy.core.logging import get_logger
from pepperpy.plugin.base import PluginInfo

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
        # Dictionary to store plugin info objects for lazy loading
        self._plugin_info: dict[str, dict[str, PluginInfo]] = {
            domain: {} for domain in self._plugins.keys()
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

    def register_plugin_info(
        self,
        domain: str,
        name: str,
        plugin_info: PluginInfo,
    ) -> None:
        """Register plugin information for lazy loading.

        Args:
            domain: Plugin domain (llm, tts, etc.)
            name: Plugin name
            plugin_info: Plugin information
        """
        if domain not in self._plugin_info:
            self._plugin_info[domain] = {}

        # Register the plugin info
        self._plugin_info[domain][name] = plugin_info

        # For workflow plugins, also register without the domain prefix for compatibility
        if domain == "workflow" and "/" in name:
            # Extract the name without the domain prefix (after the slash)
            clean_name = name.split("/", 1)[1]
            self._plugin_info[domain][clean_name] = plugin_info
            logger.info(
                f"Registered plugin info: {domain}/{name} (also as {clean_name})"
            )
        else:
            logger.info(f"Registered plugin info: {domain}/{name}")

    async def load_plugin_if_needed(self, domain: str, name: str) -> Any | None:
        """Load a plugin if it hasn't been loaded yet.

        Args:
            domain: Plugin domain
            name: Plugin name

        Returns:
            Plugin class or None if not found
        """
        from pepperpy.plugin.discovery import load_plugin

        # Check if plugin is already loaded
        if domain in self._plugins and name in self._plugins[domain]:
            return self._plugins[domain][name]["class"]

        # Check if we have plugin info for lazy loading
        plugin_info = None
        if domain in self._plugin_info and name in self._plugin_info[domain]:
            plugin_info = self._plugin_info[domain][name]
        elif domain == "workflow":
            # Special handling for workflow plugins
            if "/" in name and name.split("/", 1)[1] in self._plugin_info[domain]:
                plugin_info = self._plugin_info[domain][name.split("/", 1)[1]]
            elif f"workflow/{name}" in self._plugin_info[domain]:
                plugin_info = self._plugin_info[domain][f"workflow/{name}"]

        if plugin_info:
            try:
                # Load the plugin
                logger.info(f"Lazily loading plugin: {domain}/{name}")
                plugin_class = await load_plugin(plugin_info)

                # Register it in the normal registry
                self.register_plugin(
                    domain,
                    name,
                    plugin_class,
                    {"name": plugin_info.name, "description": plugin_info.description},
                )

                return plugin_class
            except Exception as e:
                logger.error(f"Error lazily loading plugin {domain}/{name}: {e}")
                return None

        return None

    async def get_plugin(self, domain: str, name: str) -> Any | None:
        """Get a plugin class, loading it if necessary.

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

        # Plugin not found in loaded plugins, try to load it
        plugin_class = await self.load_plugin_if_needed(domain, name)
        if plugin_class:
            return plugin_class

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


def register_plugin_info(
    domain: str,
    name: str,
    plugin_info: PluginInfo,
) -> None:
    """Register plugin information for lazy loading.

    Args:
        domain: Plugin domain (llm, tts, etc.)
        name: Plugin name
        plugin_info: Plugin information
    """
    registry = get_registry()
    registry.register_plugin_info(domain, name, plugin_info)


async def get_plugin(domain: str, name: str) -> Any | None:
    """Get a plugin class, loading it if necessary.

    Args:
        domain: Plugin domain
        name: Plugin name

    Returns:
        Plugin class or None if not found
    """
    registry = get_registry()
    return await registry.get_plugin(domain, name)


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
