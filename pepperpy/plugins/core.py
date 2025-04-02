"""Core plugin functionality for PepperPy.

This module provides the essential functionality for plugin management,
discovery, and initialization. It consolidates the key functionality
from multiple files into a single, maintainable module.
"""

import importlib
import os
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Type, TypeVar

import yaml

from pepperpy.core.errors import ValidationError
from pepperpy.core.logging import get_logger
from pepperpy.plugins.plugin import PepperpyPlugin

logger = get_logger(__name__)

# Type variable for plugin classes
T = TypeVar("T", bound=PepperpyPlugin)

# Global state
_plugin_registry: Dict[str, Dict[str, Type[PepperpyPlugin]]] = {}
_plugin_metadata: Dict[str, Dict[str, Dict[str, Any]]] = {}
_plugin_paths: Set[str] = set()
_discovered_plugins: Dict[str, Dict[str, Dict[str, Any]]] = {}
_discovery_initialized = False


class PluginSource(Enum):
    """Source of plugin discovery."""

    FILE = "file"  # From filesystem
    PACKAGE = "package"  # From installed package
    REGISTRY = "registry"  # From plugin registry
    DYNAMIC = "dynamic"  # Dynamically registered


@dataclass
class PluginInfo:
    """Information about a plugin."""

    name: str
    version: str
    description: str
    plugin_type: str
    provider_type: str
    author: str = ""
    email: str = ""
    license: str = ""
    source: PluginSource = PluginSource.FILE
    path: Optional[str] = None
    module: Optional[str] = None
    class_name: Optional[str] = None
    requirements: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class PluginError(ValidationError):
    """Error raised when a plugin operation fails."""

    def __init__(
        self,
        message: str,
        plugin_type: Optional[str] = None,
        provider_type: Optional[str] = None,
        cause: Optional[Exception] = None,
    ):
        """Initialize a new plugin error.

        Args:
            message: Error message
            plugin_type: Type of plugin
            provider_type: Type of provider
            cause: Cause of error
        """
        super().__init__(message)
        self.plugin_type = plugin_type
        self.provider_type = provider_type
        self.cause = cause


def register_plugin(
    plugin_type: str,
    provider_type: str,
    plugin_class: Type[PepperpyPlugin],
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """Register a plugin.

    Args:
        plugin_type: Type of plugin
        provider_type: Type of provider
        plugin_class: Plugin class
        metadata: Additional metadata
    """
    global _plugin_registry, _plugin_metadata

    # Initialize dictionaries if needed
    if plugin_type not in _plugin_registry:
        _plugin_registry[plugin_type] = {}

    if plugin_type not in _plugin_metadata:
        _plugin_metadata[plugin_type] = {}

    # Register plugin class and metadata
    _plugin_registry[plugin_type][provider_type] = plugin_class

    if metadata:
        _plugin_metadata[plugin_type][provider_type] = metadata

    logger.debug(f"Registered plugin: {plugin_type}/{provider_type}")


def get_plugin(plugin_type: str, provider_type: str) -> Optional[Type[PepperpyPlugin]]:
    """Get a plugin class.

    Args:
        plugin_type: Type of plugin
        provider_type: Type of provider

    Returns:
        Plugin class if found, None otherwise
    """
    return _plugin_registry.get(plugin_type, {}).get(provider_type)


def get_plugin_metadata(
    plugin_type: str, provider_type: str
) -> Optional[Dict[str, Any]]:
    """Get plugin metadata.

    Args:
        plugin_type: Type of plugin
        provider_type: Type of provider

    Returns:
        Plugin metadata if found, None otherwise
    """
    return _plugin_metadata.get(plugin_type, {}).get(provider_type)


def get_plugins_by_type(plugin_type: str) -> Dict[str, Type[PepperpyPlugin]]:
    """Get all plugins of a specific type.

    Args:
        plugin_type: Type of plugin

    Returns:
        Dict of provider type to plugin class
    """
    return _plugin_registry.get(plugin_type, {})


def list_plugins() -> Dict[str, Dict[str, Type[PepperpyPlugin]]]:
    """List all registered plugins.

    Returns:
        Dict of plugin types to provider types to plugin classes
    """
    return _plugin_registry


def list_plugin_types() -> List[str]:
    """List all plugin types.

    Returns:
        List of plugin types
    """
    return list(_plugin_registry.keys())


def find_plugin_by_class(
    plugin_class: Type[PepperpyPlugin],
) -> Optional[Dict[str, str]]:
    """Find plugin type and provider type by class.

    Args:
        plugin_class: Plugin class to find

    Returns:
        Dict with plugin_type and provider_type if found, None otherwise
    """
    for plugin_type, providers in _plugin_registry.items():
        for provider_type, cls in providers.items():
            if cls == plugin_class:
                return {"plugin_type": plugin_type, "provider_type": provider_type}
    return None


async def _discover_plugins_in_path(path: str) -> Dict[str, Dict[str, Dict[str, Any]]]:
    """Discover plugins in a specific path.

    Args:
        path: Path to search for plugins

    Returns:
        Dict of plugin types to provider types to metadata
    """
    result: Dict[str, Dict[str, Dict[str, Any]]] = {}

    if not os.path.exists(path) or not os.path.isdir(path):
        logger.debug(f"Plugin path does not exist or is not a directory: {path}")
        return result

    # Check if path is a Python package
    if os.path.exists(os.path.join(path, "__init__.py")):
        # This is a package, look for plugin.yaml
        yaml_path = os.path.join(path, "plugin.yaml")
        if os.path.exists(yaml_path):
            try:
                with open(yaml_path) as f:
                    metadata = yaml.safe_load(f)

                plugin_type = metadata.get("type")
                provider_type = metadata.get("provider")

                if plugin_type and provider_type:
                    if plugin_type not in result:
                        result[plugin_type] = {}

                    metadata["_path"] = yaml_path
                    result[plugin_type][provider_type] = metadata
            except Exception as e:
                logger.warning(f"Failed to parse plugin.yaml: {yaml_path}: {e}")

    # Explore subdirectories
    for item in os.listdir(path):
        item_path = os.path.join(path, item)
        if os.path.isdir(item_path):
            # Check if this could be a plugin type directory
            for provider in os.listdir(item_path):
                provider_path = os.path.join(item_path, provider)
                if not os.path.isdir(provider_path):
                    continue

                # Look for plugin.yaml
                yaml_path = os.path.join(provider_path, "plugin.yaml")
                if os.path.exists(yaml_path):
                    try:
                        with open(yaml_path) as f:
                            metadata = yaml.safe_load(f)

                        # Use directory names for type/provider if not specified
                        plugin_type = metadata.get("type", item)
                        provider_type = metadata.get("provider", provider)

                        if plugin_type not in result:
                            result[plugin_type] = {}

                        metadata["_path"] = yaml_path
                        result[plugin_type][provider_type] = metadata
                    except Exception as e:
                        logger.warning(f"Failed to parse plugin.yaml: {yaml_path}: {e}")

    return result


async def discover_plugins(
    paths: Optional[List[str]] = None,
    force_reload: bool = False,
) -> None:
    """Discover plugins.

    Args:
        paths: Paths to search for plugins
        force_reload: Whether to force reload plugins
    """
    global _plugin_paths, _discovered_plugins, _discovery_initialized

    # Default paths if not specified
    if not paths:
        paths = [
            os.path.join(os.path.dirname(__file__)),
            os.path.join(os.getcwd(), "plugins"),
            os.path.expanduser("~/.pepperpy/plugins"),
        ]

    # Combine with existing paths
    for path in paths:
        if path not in _plugin_paths:
            _plugin_paths.add(path)

    # Skip if already initialized and not forcing reload
    if _discovery_initialized and not force_reload:
        return

    # Discover plugins in all paths
    for path in _plugin_paths:
        plugins = await _discover_plugins_in_path(path)

        # Merge results
        for plugin_type, providers in plugins.items():
            if plugin_type not in _discovered_plugins:
                _discovered_plugins[plugin_type] = {}

            for provider_type, metadata in providers.items():
                _discovered_plugins[plugin_type][provider_type] = metadata

    # Mark as initialized
    _discovery_initialized = True

    # Log discovery info
    total_plugins = sum(len(providers) for providers in _discovered_plugins.values())
    if total_plugins > 0:
        logger.info(f"Discovered {total_plugins} plugins")


async def load_plugin(
    plugin_type: str, provider_type: str
) -> Optional[Type[PepperpyPlugin]]:
    """Load a specific plugin.

    Args:
        plugin_type: Type of plugin
        provider_type: Type of provider

    Returns:
        Plugin class if found and loaded, None otherwise
    """
    # Check if already loaded
    if get_plugin(plugin_type, provider_type):
        return get_plugin(plugin_type, provider_type)

    # Check if discovered but not loaded
    if (
        plugin_type in _discovered_plugins
        and provider_type in _discovered_plugins[plugin_type]
    ):
        metadata = _discovered_plugins[plugin_type][provider_type]

        # Get plugin path
        plugin_path = os.path.dirname(metadata["_path"])

        # Get module and class name
        module_name = metadata.get("main_module", "provider")
        class_name = metadata.get("main_class")

        if not class_name:
            # Try to guess class name from provider name
            parts = provider_type.split("_")
            class_name = "".join(part.capitalize() for part in parts) + "Provider"

        # Add plugin path to sys.path temporarily
        original_path = sys.path.copy()
        plugin_parent = os.path.dirname(plugin_path)
        if plugin_parent not in sys.path:
            sys.path.insert(0, plugin_parent)

        try:
            # Import module
            module_path = f"{os.path.basename(plugin_path)}.{module_name}"
            module = importlib.import_module(module_path)

            # Get plugin class
            plugin_class = getattr(module, class_name)

            # Register plugin
            register_plugin(plugin_type, provider_type, plugin_class, metadata)

            return plugin_class
        except ImportError as e:
            logger.error(
                f"Failed to import plugin module: {plugin_type}/{provider_type}: {e}"
            )
        except AttributeError as e:
            logger.error(
                f"Failed to find plugin class: {plugin_type}/{provider_type}/{class_name}: {e}"
            )
        except Exception as e:
            logger.error(f"Error loading plugin: {plugin_type}/{provider_type}: {e}")
        finally:
            # Restore sys.path
            sys.path = original_path

    return None


async def create_provider_instance(
    plugin_type: str,
    provider_type: str,
    require_api_key: bool = False,
    **config: Any,
) -> PepperpyPlugin:
    """Create a plugin provider instance.

    Args:
        plugin_type: Type of plugin
        provider_type: Type of provider
        require_api_key: Whether to require API key
        **config: Provider configuration

    Returns:
        Provider instance

    Raises:
        ValidationError: If provider creation fails
    """
    # Ensure discovery is initialized
    if not _discovery_initialized:
        await discover_plugins()

    # Load plugin if needed
    plugin_class = get_plugin(plugin_type, provider_type)
    if not plugin_class:
        plugin_class = await load_plugin(plugin_type, provider_type)

    if not plugin_class:
        raise ValidationError(f"Provider not found: {plugin_type}/{provider_type}")

    # Get plugin metadata
    metadata = get_plugin_metadata(plugin_type, provider_type)

    # Check if API key is required
    if require_api_key and "api_key" not in config:
        # Try to get API key from environment
        env_var_list = [
            f"{provider_type.upper()}_API_KEY",
            f"PEPPERPY_{plugin_type.upper()}__{provider_type.upper()}_API_KEY",
            f"PEPPERPY_{plugin_type.upper()}__API_KEY",
        ]

        # Also check metadata for custom env var
        if metadata and "configuration" in metadata:
            api_key_config = metadata["configuration"].get("api_key", {})
            if api_key_config and "env_var" in api_key_config:
                env_var_list.insert(0, api_key_config["env_var"])

        # Try each env var
        for env_var in env_var_list:
            api_key = os.environ.get(env_var)
            if api_key:
                config["api_key"] = api_key
                break

        if "api_key" not in config:
            raise ValidationError(
                f"API key required for {plugin_type}/{provider_type}. "
                f"Set one of these environment variables: {', '.join(env_var_list)}"
            )

    # Create instance
    return plugin_class(**config)
