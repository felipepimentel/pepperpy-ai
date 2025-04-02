"""Plugin registry for PepperPy.

This module provides the plugin registry functionality for PepperPy,
including registration, discovery, and lookup of plugins.
"""

import importlib
import os
import sys
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Type, TypeVar, Union

import yaml

from pepperpy.core.errors import ValidationError
from pepperpy.core.logging import get_logger
from pepperpy.plugins.plugin import PepperpyPlugin

logger = get_logger(__name__)

# Type variable for plugin classes
T = TypeVar("T", bound=PepperpyPlugin)

# Global registry state
_plugin_registry: Dict[str, Dict[str, Type[PepperpyPlugin]]] = {}
_plugin_metadata: Dict[str, Dict[str, Dict[str, Any]]] = {}
_plugin_paths: Set[str] = set()
_scan_timestamps: Dict[str, float] = {}
_discovery_initialized = False

# Mapping of plugin aliases to actual implementations
_plugin_aliases: Dict[str, Dict[str, Union[str, Dict[str, Any]]]] = {
    "llm": {
        "gpt4": "openai:gpt-4",
        "gpt4o": "openrouter:openai/gpt-4o",
        "claude": "anthropic:claude-3-sonnet",
        "llama": "local:llama",
    },
    "embeddings": {
        "ada": "openai:text-embedding-ada-002",
        "e5": "huggingface:e5-large-v2",
    },
}

# Plugin fallback configuration
_plugin_fallbacks: Dict[str, List[str]] = {
    "llm": ["openrouter", "openai", "local"],
    "embeddings": ["openai", "huggingface", "local"],
    "rag": ["memory", "chroma", "faiss"],
}


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
    dependencies: List[Dict[str, Any]] = field(default_factory=list)
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
    # Check for alias resolution
    provider_type, config_override = _resolve_alias(plugin_type, provider_type)

    # Try to get plugin directly
    plugin_class = _plugin_registry.get(plugin_type, {}).get(provider_type)

    # If not found and not already loading, try to load it
    if plugin_class is None:
        plugin_class = load_plugin(plugin_type, provider_type)

    # If still not found, try fallbacks
    if plugin_class is None and _should_try_fallbacks(plugin_type, provider_type):
        # Get fallback provider
        fallback_provider = find_fallback(plugin_type, provider_type)
        if fallback_provider:
            logger.info(
                f"Using fallback provider {fallback_provider} for {plugin_type}/{provider_type}"
            )
            plugin_class = _plugin_registry.get(plugin_type, {}).get(fallback_provider)
            if plugin_class is None:
                plugin_class = load_plugin(plugin_type, fallback_provider)

    return plugin_class


def _should_try_fallbacks(plugin_type: str, provider_type: str) -> bool:
    """Determine if fallbacks should be tried for a plugin.

    Args:
        plugin_type: Type of plugin
        provider_type: Type of provider

    Returns:
        True if fallbacks should be tried, False otherwise
    """
    # Check if the plugin type has fallbacks defined
    if plugin_type not in _plugin_fallbacks:
        return False

    # Don't use fallbacks if the provider is explicitly specified and not in fallbacks
    fallbacks = _plugin_fallbacks[plugin_type]
    if provider_type not in fallbacks and provider_type != "auto":
        return False

    return True


def find_fallback(plugin_type: str, provider_type: str) -> Optional[str]:
    """Find a fallback provider for a plugin.

    Args:
        plugin_type: Type of plugin
        provider_type: Type of provider

    Returns:
        Fallback provider type if found, None otherwise
    """
    # Check if fallbacks are defined for this plugin type
    if plugin_type not in _plugin_fallbacks:
        return None

    # Get fallback list
    fallbacks = _plugin_fallbacks[plugin_type]

    # Try each fallback provider
    for fallback_provider in fallbacks:
        # Skip the original provider
        if fallback_provider == provider_type:
            continue

        # Check if provider exists
        if fallback_provider in _plugin_registry.get(plugin_type, {}):
            return fallback_provider

        # Try to load the provider
        if load_plugin(plugin_type, fallback_provider) is not None:
            return fallback_provider

    return None


def _resolve_alias(plugin_type: str, provider_type: str) -> Tuple[str, Dict[str, Any]]:
    """Resolve a plugin alias to a provider type and config override.

    Args:
        plugin_type: Type of plugin
        provider_type: Type of provider (or alias)

    Returns:
        Tuple of (resolved provider type, config override dict)
    """
    # Initialize empty config override
    config_override = {}

    # Check for provider aliases
    if plugin_type in _plugin_aliases and provider_type in _plugin_aliases[plugin_type]:
        alias_target = _plugin_aliases[plugin_type][provider_type]

        # Handle string aliases
        if isinstance(alias_target, str):
            # Check if the alias includes a specific model
            if ":" in alias_target:
                provider, model = alias_target.split(":", 1)
                # Set model in config
                config_override["model"] = model
                return provider, config_override
            else:
                # Just a provider alias
                return alias_target, config_override

        # Handle dictionary aliases with full config
        elif isinstance(alias_target, dict) and "provider" in alias_target:
            provider = alias_target["provider"]
            # Copy all other fields to config override
            for key, value in alias_target.items():
                if key != "provider":
                    config_override[key] = value
            return provider, config_override

    # No alias found, return original
    return provider_type, config_override


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
    # Resolve alias
    provider_type, _ = _resolve_alias(plugin_type, provider_type)
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


def register_plugin_path(path: str) -> None:
    """Register a path for plugin discovery.

    Args:
        path: Path to register
    """
    global _plugin_paths
    if os.path.isdir(path):
        _plugin_paths.add(path)
        logger.debug(f"Registered plugin path: {path}")
    else:
        logger.warning(f"Plugin path does not exist: {path}")


def register_plugin_alias(
    plugin_type: str,
    alias: str,
    provider_type: str,
    config_override: Optional[Dict[str, Any]] = None,
) -> None:
    """Register a plugin alias.

    Args:
        plugin_type: Type of plugin
        alias: Alias name
        provider_type: Actual provider type
        config_override: Configuration overrides to apply
    """
    global _plugin_aliases

    # Initialize dict if needed
    if plugin_type not in _plugin_aliases:
        _plugin_aliases[plugin_type] = {}

    # If config_override is provided, store as dict with provider
    if config_override:
        alias_config = {"provider": provider_type}
        alias_config.update(config_override)
        _plugin_aliases[plugin_type][alias] = alias_config
    else:
        # Otherwise store as string or as provider:model if model is specified
        _plugin_aliases[plugin_type][alias] = provider_type

    logger.debug(f"Registered plugin alias: {plugin_type}/{alias} -> {provider_type}")


def register_plugin_fallbacks(plugin_type: str, fallbacks: List[str]) -> None:
    """Register fallbacks for a plugin type.

    Args:
        plugin_type: Type of plugin
        fallbacks: List of fallback provider types in order of preference
    """
    global _plugin_fallbacks
    _plugin_fallbacks[plugin_type] = fallbacks
    logger.debug(f"Registered fallbacks for {plugin_type}: {', '.join(fallbacks)}")


def create_provider_instance(
    plugin_type: str, provider_type: str, **config: Any
) -> PepperpyPlugin:
    """Create a provider instance.

    Args:
        plugin_type: Type of plugin
        provider_type: Type of provider
        **config: Configuration for provider

    Returns:
        Provider instance

    Raises:
        PluginError: If provider not found or creation fails
    """
    # Resolve alias
    resolved_provider, config_override = _resolve_alias(plugin_type, provider_type)

    # Merge config with config_override (config takes precedence)
    merged_config = config_override.copy()
    merged_config.update(config)

    # Ensure plugin is loaded
    plugin_class = get_plugin(plugin_type, resolved_provider)
    if not plugin_class:
        # If plugin not found and fallbacks are enabled, try fallbacks
        if _should_try_fallbacks(plugin_type, resolved_provider):
            fallback = find_fallback(plugin_type, resolved_provider)
            if fallback:
                logger.info(
                    f"Using fallback provider {fallback} for {plugin_type}/{provider_type}"
                )
                plugin_class = get_plugin(plugin_type, fallback)
                if not plugin_class:
                    raise PluginError(
                        f"Provider and fallbacks not found: {plugin_type}/{provider_type}",
                        plugin_type=plugin_type,
                        provider_type=provider_type,
                    )
            else:
                raise PluginError(
                    f"Provider not found and no fallbacks available: {plugin_type}/{provider_type}",
                    plugin_type=plugin_type,
                    provider_type=provider_type,
                )
        else:
            raise PluginError(
                f"Provider not found: {plugin_type}/{provider_type}",
                plugin_type=plugin_type,
                provider_type=provider_type,
            )

    # Create instance
    try:
        return plugin_class(**merged_config)
    except Exception as e:
        raise PluginError(
            f"Failed to create provider instance: {e}",
            plugin_type=plugin_type,
            provider_type=provider_type,
            cause=e,
        )


def load_plugin(plugin_type: str, provider_type: str) -> Optional[Type[PepperpyPlugin]]:
    """Load a specific plugin.

    Args:
        plugin_type: Type of plugin
        provider_type: Type of provider

    Returns:
        Plugin class if found and loaded, None otherwise
    """
    # Check if already loaded
    plugin_class = _plugin_registry.get(plugin_type, {}).get(provider_type)
    if plugin_class:
        return plugin_class

    # Check plugin paths for plugin configuration
    for plugin_path in _plugin_paths:
        provider_dir = os.path.join(plugin_path, plugin_type, provider_type)
        if not os.path.isdir(provider_dir):
            continue

        # Look for plugin.yaml
        plugin_yaml = os.path.join(provider_dir, "plugin.yaml")
        if not os.path.isfile(plugin_yaml):
            continue

        # Load plugin metadata
        try:
            with open(plugin_yaml) as f:
                metadata = yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load plugin metadata: {plugin_yaml}: {e}")
            continue

        # Get entry point
        entry_point = metadata.get("entry_point")
        if not entry_point:
            logger.error(f"No entry point found in plugin metadata: {plugin_yaml}")
            continue

        # Parse entry point
        if ":" not in entry_point:
            logger.error(
                f"Invalid entry point format in plugin metadata: {plugin_yaml}"
            )
            continue

        module_name, class_name = entry_point.split(":", 1)

        # Adjust sys.path for module import
        original_path = sys.path.copy()
        if plugin_path not in sys.path:
            sys.path.insert(0, plugin_path)

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


def discover_plugins() -> Dict[str, Dict[str, Dict[str, Any]]]:
    """Discover all plugins in registered paths.

    Returns:
        Dictionary of discovered plugins by type and provider
    """
    discovered: Dict[str, Dict[str, Dict[str, Any]]] = {}

    # Discover plugins in registered paths
    for plugin_path in _plugin_paths:
        if not os.path.isdir(plugin_path):
            continue

        # Check if we've scanned this path recently
        if _is_path_cached(plugin_path):
            logger.debug(f"Skipping cached plugin path: {plugin_path}")
            continue

        # Mark path as scanned
        _mark_path_scanned(plugin_path)

        # Discover plugin types (directories in plugin path)
        for plugin_type in os.listdir(plugin_path):
            type_dir = os.path.join(plugin_path, plugin_type)
            if not os.path.isdir(type_dir):
                continue

            # Discover provider types (directories in plugin type directory)
            for provider_type in os.listdir(type_dir):
                provider_dir = os.path.join(type_dir, provider_type)
                if not os.path.isdir(provider_dir):
                    continue

                # Look for plugin.yaml
                plugin_yaml = os.path.join(provider_dir, "plugin.yaml")
                if not os.path.isfile(plugin_yaml):
                    continue

                # Load plugin metadata
                try:
                    with open(plugin_yaml) as f:
                        metadata = yaml.safe_load(f)
                except Exception as e:
                    logger.error(f"Failed to load plugin metadata: {plugin_yaml}: {e}")
                    continue

                # Add plugin to discovered dict
                if plugin_type not in discovered:
                    discovered[plugin_type] = {}

                metadata["_path"] = plugin_yaml
                discovered[plugin_type][provider_type] = metadata

                logger.debug(f"Discovered plugin: {plugin_type}/{provider_type}")

    return discovered


def _is_path_cached(path: str, max_age: float = 300.0) -> bool:
    """Check if a path has been scanned recently.

    Args:
        path: Path to check
        max_age: Maximum age in seconds for cached path

    Returns:
        True if path is cached and not expired, False otherwise
    """
    if path not in _scan_timestamps:
        return False

    timestamp = _scan_timestamps[path]
    return (time.time() - timestamp) < max_age


def _mark_path_scanned(path: str) -> None:
    """Mark a path as scanned.

    Args:
        path: Path to mark
    """
    _scan_timestamps[path] = time.time()


def clear_path_cache(path: Optional[str] = None) -> None:
    """Clear path scan cache.

    Args:
        path: Specific path to clear, or all paths if None
    """
    global _scan_timestamps
    if path:
        if path in _scan_timestamps:
            del _scan_timestamps[path]
    else:
        _scan_timestamps.clear()


async def initialize_discovery() -> None:
    """Initialize plugin discovery.

    This should be called at startup to discover plugins.
    """
    global _discovery_initialized

    if _discovery_initialized:
        return

    # Add default plugin paths
    _ensure_default_paths()

    # Discover plugins
    plugins = discover_plugins()

    # Load common plugin types eagerly
    for plugin_type in ["llm", "embeddings", "rag"]:
        if plugin_type in plugins:
            for provider_type in plugins[plugin_type]:
                try:
                    load_plugin(plugin_type, provider_type)
                except Exception as e:
                    logger.warning(
                        f"Failed to load plugin: {plugin_type}/{provider_type}: {e}"
                    )

    _discovery_initialized = True
    logger.info("Plugin discovery initialized")


def _ensure_default_paths() -> None:
    """Ensure default plugin paths are registered."""
    # Add built-in plugin path
    builtin_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "plugins")
    if os.path.isdir(builtin_path):
        register_plugin_path(builtin_path)

    # Add user plugin path
    user_plugin_path = os.path.join(os.path.expanduser("~"), ".pepperpy", "plugins")
    if os.path.isdir(user_plugin_path):
        register_plugin_path(user_plugin_path)

    # Add current working directory plugins
    cwd_plugins = os.path.join(os.getcwd(), "plugins")
    if os.path.isdir(cwd_plugins):
        register_plugin_path(cwd_plugins)


async def ensure_discovery_initialized() -> None:
    """Ensure discovery is initialized.

    This is a convenience function that can be called from anywhere.
    """
    if not _discovery_initialized:
        await initialize_discovery()
