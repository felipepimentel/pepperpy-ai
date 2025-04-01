"""Plugin discovery module."""

import importlib
import sys
from enum import Enum
from importlib.metadata import EntryPoint, entry_points
from pathlib import Path
from typing import Dict, List, Optional, Type, cast, Iterable

import yaml

from pepperpy.core.errors import ValidationError
from pepperpy.core.logging import get_logger
from pepperpy.plugins.plugin import PepperpyPlugin

logger = get_logger(__name__)


class PluginValidationError(ValidationError):
    """Error raised when plugin validation fails."""

    def __init__(
        self,
        message: str,
        plugin_name: Optional[str] = None,
        plugin_path: Optional[str] = None,
        *args,
        **kwargs,
    ):
        super().__init__(message, *args, **kwargs)
        self.plugin_name = plugin_name
        self.plugin_path = plugin_path

    def __str__(self) -> str:
        parts = [self.message]
        if self.plugin_name:
            parts.append(f"Plugin: {self.plugin_name}")
        if self.plugin_path:
            parts.append(f"Path: {self.plugin_path}")
        return " | ".join(parts)


class PluginLoadError(ValidationError):
    """Error raised when plugin loading fails."""

    def __init__(
        self,
        message: str,
        plugin_name: Optional[str] = None,
        plugin_path: Optional[str] = None,
        cause: Optional[Exception] = None,
        *args,
        **kwargs,
    ):
        super().__init__(message, *args, **kwargs)
        self.plugin_name = plugin_name
        self.plugin_path = plugin_path
        self.cause = cause

    def __str__(self) -> str:
        parts = [self.message]
        if self.plugin_name:
            parts.append(f"Plugin: {self.plugin_name}")
        if self.plugin_path:
            parts.append(f"Path: {self.plugin_path}")
        if self.cause:
            parts.append(f"Cause: {self.cause!s}")
        return " | ".join(parts)


class PluginSource(Enum):
    """Source of plugin discovery."""

    LOCAL = "local"  # Local filesystem
    ENTRYPOINT = "entrypoint"  # Entry points from installed packages
    NAMESPACE = "namespace"  # Python namespace packages
    DYNAMIC = "dynamic"  # Dynamically registered


class PluginRegistry:
    """Registry for plugins."""

    def __init__(self) -> None:
        """Initialize plugin registry."""
        self._plugins: Dict[str, Dict[str, Type[PepperpyPlugin]]] = {}
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

    def get_plugin_by_provider(
        self, plugin_type: str, provider_type: str
    ) -> Optional[Type[PepperpyPlugin]]:
        """Get a plugin by type and provider.

        Args:
            plugin_type: Type of plugin
            provider_type: Type of provider

        Returns:
            Plugin class if found, None otherwise
        """
        return self._plugins.get(plugin_type, {}).get(provider_type)

    def list_plugins(self) -> Dict[str, Dict[str, Type[PepperpyPlugin]]]:
        """List all plugins.

        Returns:
            Dict of plugin types to dict of provider types to plugin classes
        """
        return dict(self._plugins)


# Global plugin registry instance
_plugin_registry: Optional[PluginRegistry] = None


def get_plugin_registry() -> PluginRegistry:
    """Get the global plugin registry.

    Returns:
        Plugin registry instance
    """
    global _plugin_registry
    if _plugin_registry is None:
        _plugin_registry = PluginRegistry()
    return _plugin_registry


async def discover_plugins(paths: List[str]) -> None:
    """Discover plugins in given paths.

    Args:
        paths: List of paths to search for plugins

    Raises:
        PluginValidationError: If plugin validation fails
        PluginLoadError: If plugin loading fails
    """
    registry = get_plugin_registry()
    if registry._initialized:
        return

    # Discover from filesystem
    for path in paths:
        path_obj = Path(path)
        if not path_obj.exists() or not path_obj.is_dir():
            logger.warning(f"Plugin path does not exist or is not a directory: {path}")
            continue

        # Add path to Python path temporarily
        if str(path_obj) not in sys.path:
            sys.path.insert(0, str(path_obj))

        try:
            # Look for plugin.yaml files
            for plugin_yaml in path_obj.glob("**/plugin.yaml"):
                try:
                    # Load plugin metadata
                    with open(plugin_yaml) as f:
                        metadata = yaml.safe_load(f)

                    # Validate metadata
                    if not isinstance(metadata, dict):
                        raise PluginValidationError(
                            "Invalid plugin metadata format",
                            plugin_path=str(plugin_yaml),
                        )

                    # Extract and validate required fields
                    plugin_type = metadata.get("type", "")
                    provider_type = metadata.get("provider", "")
                    module_path = metadata.get("module", "")
                    class_name = metadata.get("class", "")

                    # Validate all required fields are present and are strings
                    if not all(
                        [
                            isinstance(plugin_type, str) and plugin_type,
                            isinstance(provider_type, str) and provider_type,
                            isinstance(module_path, str) and module_path,
                            isinstance(class_name, str) and class_name,
                        ]
                    ):
                        raise PluginValidationError(
                            "Missing or invalid required metadata fields",
                            plugin_path=str(plugin_yaml),
                        )

                    # Import plugin module
                    try:
                        module = importlib.import_module(module_path)
                    except ImportError as e:
                        raise PluginLoadError(
                            f"Failed to import plugin module: {e}",
                            plugin_path=str(plugin_yaml),
                            cause=e,
                        ) from e

                    # Get plugin class
                    plugin_class = getattr(module, class_name)
                    if plugin_class is None:
                        raise PluginValidationError(
                            f"Plugin class {class_name} not found in module",
                            plugin_path=str(plugin_yaml),
                        )

                    if not issubclass(plugin_class, PepperpyPlugin):
                        raise PluginValidationError(
                            f"Plugin class {class_name} does not inherit from PepperpyPlugin",
                            plugin_path=str(plugin_yaml),
                        )

                    # Register plugin
                    registry.register_plugin(plugin_type, provider_type, plugin_class)

                except (PluginValidationError, PluginLoadError) as e:
                    logger.warning(str(e))
                except Exception as e:
                    logger.warning(f"Failed to load plugin from {plugin_yaml}: {e}")

        finally:
            # Remove path from Python path
            if str(path_obj) in sys.path:
                sys.path.remove(str(path_obj))

    # Discover from entry points
    try:
        eps = entry_points()
        pepperpy_eps: Iterable[EntryPoint] = []
        
        # Handle different entry_points() return type in Python 3.8 vs 3.9+
        if hasattr(eps, "select"):
            pepperpy_eps = eps.select(group="pepperpy.plugins")
        elif hasattr(eps, "get"):
            pepperpy_eps = cast(Iterable[EntryPoint], eps.get("pepperpy.plugins", []))

        for ep in pepperpy_eps:
            try:
                plugin_class = ep.load()
                if not issubclass(plugin_class, PepperpyPlugin):
                    logger.warning(
                        f"Entry point {ep.name} does not provide a PepperpyPlugin class"
                    )
                    continue

                plugin_type = cast(str, getattr(plugin_class, "plugin_type", ""))
                provider_type = cast(str, getattr(plugin_class, "provider_type", ""))

                if not plugin_type or not provider_type:
                    logger.warning(
                        f"Entry point {ep.name} plugin class missing type metadata"
                    )
                    continue

                registry.register_plugin(plugin_type, provider_type, plugin_class)

            except Exception as e:
                logger.warning(f"Failed to load entry point plugin {ep.name}: {e}")

    except Exception as e:
        logger.warning(f"Failed to discover entry point plugins: {e}")

    registry._initialized = True


def get_plugin(plugin_type: str, provider_type: str) -> Optional[Type[PepperpyPlugin]]:
    """Get plugin by type and provider.

    Args:
        plugin_type: Type of plugin
        provider_type: Type of provider

    Returns:
        Plugin class if found, None otherwise
    """
    registry = get_plugin_registry()
    return registry.get_plugin(plugin_type, provider_type)


def get_plugin_by_provider(
    plugin_type: str, provider_type: str
) -> Optional[Type[PepperpyPlugin]]:
    """Get plugin by type and provider.

    Args:
        plugin_type: Type of plugin
        provider_type: Type of provider

    Returns:
        Plugin class if found, None otherwise
    """
    registry = get_plugin_registry()
    return registry.get_plugin_by_provider(plugin_type, provider_type)
