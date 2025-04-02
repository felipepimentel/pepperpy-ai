"""Plugin discovery module."""

import asyncio
import importlib
import os
import sys
import time
from enum import Enum
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    Union,
)

import yaml

from pepperpy.core.errors import ValidationError
from pepperpy.core.logging import get_logger
from pepperpy.plugins.plugin import PepperpyPlugin

logger = get_logger(__name__)

# Global lazy loading flags
_discovery_initialized = False
_lazy_discovery_enabled = True
_plugin_paths_scanned = False
_available_paths = []

# Mapping of plugin aliases to actual implementations
_plugin_aliases: Dict[str, Dict[str, str]] = {
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
        self._plugin_paths: Dict[
            str, Dict[str, str]
        ] = {}  # Maps plugin types and names to paths
        self._scanned_paths: Set[str] = set()
        self._scan_timestamps: Dict[str, float] = {}
        self._initialized = False
        self._loaded_modules: Dict[str, Any] = {}  # Cache for loaded modules
        self._validation_errors: Dict[str, str] = {}  # Map paths to validation errors
        self._discovered_plugins: Dict[
            str, Dict[str, Dict[str, Any]]
        ] = {}  # Just discovered, not loaded
        self._loading_locks: Dict[
            str, asyncio.Lock
        ] = {}  # Locks for loading specific plugins

    async def discover_without_loading(
        self, paths: List[str]
    ) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """Discover plugins without loading them, just collecting metadata.

        Args:
            paths: List of paths to scan for plugins

        Returns:
            Dict of plugin types to provider types to metadata
        """
        result: Dict[str, Dict[str, Dict[str, Any]]] = {}

        for path in paths:
            if not os.path.exists(path) or not os.path.isdir(path):
                logger.warning(
                    f"Plugin path does not exist or is not a directory: {path}"
                )
                continue

            for plugin_type in os.listdir(path):
                type_path = os.path.join(path, plugin_type)
                if not os.path.isdir(type_path):
                    continue

                if plugin_type not in result:
                    result[plugin_type] = {}

                for provider_type in os.listdir(type_path):
                    provider_path = os.path.join(type_path, provider_type)
                    if not os.path.isdir(provider_path):
                        continue

                    yaml_path = os.path.join(provider_path, "plugin.yaml")
                    if not os.path.exists(yaml_path):
                        continue

                    try:
                        with open(yaml_path) as f:
                            metadata = yaml.safe_load(f)

                        # Minimal validation
                        if not metadata:
                            continue

                        # Add path information
                        metadata["_path"] = yaml_path

                        # Store discovery info
                        result[plugin_type][provider_type] = metadata

                    except Exception as e:
                        logger.warning(f"Failed to parse plugin.yaml: {yaml_path}: {e}")

        return result

    def register_plugin(
        self,
        plugin_type: str,
        provider_type: str,
        plugin_class: Type[PepperpyPlugin],
        source_path: Optional[str] = None,
    ) -> None:
        """Register a plugin.

        Args:
            plugin_type: Type of plugin (e.g., "llm", "rag")
            provider_type: Type of provider (e.g., "openai", "local")
            plugin_class: Plugin class to register
            source_path: Path to plugin.yaml file or similar source
        """
        if plugin_type not in self._plugins:
            self._plugins[plugin_type] = {}
        self._plugins[plugin_type][provider_type] = plugin_class

        # Track the source path for this plugin
        if source_path:
            if plugin_type not in self._plugin_paths:
                self._plugin_paths[plugin_type] = {}
            self._plugin_paths[plugin_type][provider_type] = source_path

        logger.debug(f"Registered plugin: {plugin_type}/{provider_type}")

    def register_discovered_plugin(
        self, plugin_type: str, provider_type: str, metadata: Dict[str, Any]
    ) -> None:
        """Register a discovered plugin without loading it.

        Args:
            plugin_type: Type of plugin
            provider_type: Type of provider
            metadata: Plugin metadata
        """
        if plugin_type not in self._discovered_plugins:
            self._discovered_plugins[plugin_type] = {}

        self._discovered_plugins[plugin_type][provider_type] = metadata
        logger.debug(f"Discovered plugin: {plugin_type}/{provider_type}")

    async def get_plugin(
        self, plugin_type: str, provider_type: str
    ) -> Optional[Type[PepperpyPlugin]]:
        """Get a plugin class, loading it if necessary.

        Args:
            plugin_type: Type of plugin
            provider_type: Type of provider

        Returns:
            Plugin class if found, None otherwise
        """
        # Check for alias resolution
        provider_type, config_override = self._resolve_alias(plugin_type, provider_type)

        # Check if already loaded
        if plugin_type in self._plugins and provider_type in self._plugins[plugin_type]:
            return self._plugins[plugin_type][provider_type]

        # Check if discovered but not loaded
        if (
            plugin_type in self._discovered_plugins
            and provider_type in self._discovered_plugins[plugin_type]
        ):
            # Load the plugin
            await self._load_plugin(
                plugin_type,
                provider_type,
                self._discovered_plugins[plugin_type][provider_type],
            )

            # Check again if loaded
            if (
                plugin_type in self._plugins
                and provider_type in self._plugins[plugin_type]
            ):
                return self._plugins[plugin_type][provider_type]

        # Try fallbacks if enabled
        if self._should_try_fallbacks(plugin_type, provider_type):
            fallback_provider = await self._find_fallback(plugin_type, provider_type)
            if fallback_provider:
                logger.info(
                    f"Using fallback provider {fallback_provider} for {plugin_type}/{provider_type}"
                )
                return await self.get_plugin(plugin_type, fallback_provider)

        return None

    def _should_try_fallbacks(self, plugin_type: str, provider_type: str) -> bool:
        """Check if fallbacks should be tried for this plugin.

        Args:
            plugin_type: Type of plugin
            provider_type: Type of provider

        Returns:
            True if fallbacks should be tried, False otherwise
        """
        # Don't try fallbacks if already using a fallback
        if (
            plugin_type in _plugin_fallbacks
            and provider_type in _plugin_fallbacks[plugin_type]
        ):
            idx = _plugin_fallbacks[plugin_type].index(provider_type)
            # If this is the last fallback or not the first choice, don't try further fallbacks
            if idx > 0 or idx == len(_plugin_fallbacks[plugin_type]) - 1:
                return False
        return True

    async def _find_fallback(
        self, plugin_type: str, provider_type: str
    ) -> Optional[str]:
        """Find a fallback provider for a given plugin type.

        Args:
            plugin_type: Type of plugin
            provider_type: Type of provider that failed

        Returns:
            Fallback provider type if found, None otherwise
        """
        if plugin_type not in _plugin_fallbacks:
            return None

        # Skip providers we've already tried
        try:
            idx = _plugin_fallbacks[plugin_type].index(provider_type)
            fallback_candidates = _plugin_fallbacks[plugin_type][idx + 1 :]
        except ValueError:
            fallback_candidates = _plugin_fallbacks[plugin_type]

        # Try each fallback in order
        for fallback in fallback_candidates:
            # Check if fallback is loaded
            if plugin_type in self._plugins and fallback in self._plugins[plugin_type]:
                return fallback

            # Check if fallback is discovered
            if (
                plugin_type in self._discovered_plugins
                and fallback in self._discovered_plugins[plugin_type]
            ):
                return fallback

        return None

    def _resolve_alias(
        self, plugin_type: str, provider_type: str
    ) -> Tuple[str, Dict[str, Any]]:
        """Resolve a plugin alias to the actual provider type and any config overrides.

        Args:
            plugin_type: Type of plugin
            provider_type: Type of provider or alias

        Returns:
            Tuple of (resolved_provider_type, config_override_dict)
        """
        config_override = {}

        # Check for aliases
        if (
            plugin_type in _plugin_aliases
            and provider_type in _plugin_aliases[plugin_type]
        ):
            alias_value = _plugin_aliases[plugin_type][provider_type]

            # Check if the alias specifies a provider:config format
            if ":" in alias_value:
                parts = alias_value.split(":", 1)
                resolved_provider = parts[0]

                # Add model or other config from alias
                if len(parts) > 1 and parts[1]:
                    # For LLM, assume the config is the model
                    if plugin_type == "llm":
                        config_override["model"] = parts[1]
                    # For embeddings, assume the config is the embedding model
                    elif plugin_type == "embeddings":
                        config_override["model"] = parts[1]
                    # Add other domain-specific handling here
            else:
                resolved_provider = alias_value

            logger.debug(
                f"Resolved alias {provider_type} to {resolved_provider} with config {config_override}"
            )
            return resolved_provider, config_override

        return provider_type, config_override

    async def _load_plugin(
        self, plugin_type: str, provider_type: str, metadata: Dict[str, Any]
    ) -> None:
        """Load a plugin from its metadata.

        Args:
            plugin_type: Type of plugin
            provider_type: Type of provider
            metadata: Plugin metadata
        """
        # Use a lock to prevent multiple concurrent loads of the same plugin
        lock_key = f"{plugin_type}/{provider_type}"
        if lock_key not in self._loading_locks:
            self._loading_locks[lock_key] = asyncio.Lock()

        async with self._loading_locks[lock_key]:
            # Check if already loaded (might have been loaded while waiting for lock)
            if (
                plugin_type in self._plugins
                and provider_type in self._plugins[plugin_type]
            ):
                return

            # Extract entry point information
            if "entry_point" not in metadata:
                logger.warning(
                    f"Missing entry_point in plugin metadata: {plugin_type}/{provider_type}"
                )
                return

            entry_point = metadata["entry_point"]

            # Module-based entry point format: module:class
            if ":" in entry_point:
                module_name, class_name = entry_point.split(":", 1)

                try:
                    # Dynamic import with caching
                    if module_name in self._loaded_modules:
                        module = self._loaded_modules[module_name]
                    else:
                        # Add parent directory to path if needed
                        if "_path" in metadata:
                            plugin_dir = os.path.dirname(metadata["_path"])
                            parent_dir = os.path.dirname(os.path.dirname(plugin_dir))
                            if parent_dir not in sys.path:
                                sys.path.insert(0, parent_dir)

                        # Import the module
                        module = importlib.import_module(module_name)
                        self._loaded_modules[module_name] = module

                    # Get the class
                    plugin_class = getattr(module, class_name)

                    # Register the plugin
                    self.register_plugin(
                        plugin_type,
                        provider_type,
                        plugin_class,
                        source_path=metadata.get("_path"),
                    )

                except Exception as e:
                    logger.error(
                        f"Failed to load plugin {plugin_type}/{provider_type}: {e}"
                    )
                    # Store the error
                    self.add_validation_error(
                        metadata.get("_path", f"{plugin_type}/{provider_type}"),
                        f"Failed to load plugin: {e}",
                    )

    def get_plugin_by_provider(
        self, plugin_type: str, provider_type: str
    ) -> Optional[Type[PepperpyPlugin]]:
        """Get a plugin by type and provider synchronously (for backward compatibility).

        Args:
            plugin_type: Type of plugin
            provider_type: Type of provider

        Returns:
            Plugin class if found, None otherwise
        """
        # This is just a synchronous wrapper around the async version
        # In a real implementation, you'd want to run the event loop or use a thread
        # For simplicity here, we just check already loaded plugins
        return self._plugins.get(plugin_type, {}).get(provider_type)

    def list_plugins(self) -> Dict[str, Dict[str, Type[PepperpyPlugin]]]:
        """List all loaded plugins.

        Returns:
            Dict of plugin types to dict of provider types to plugin classes
        """
        return dict(self._plugins)

    def list_discovered_plugins(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """List all discovered plugins (including those not loaded).

        Returns:
            Dict of plugin types to dict of provider types to metadata
        """
        return dict(self._discovered_plugins)

    def get_plugin_path(self, plugin_type: str, provider_type: str) -> Optional[str]:
        """Get the source path for a plugin.

        Args:
            plugin_type: Type of plugin
            provider_type: Type of provider

        Returns:
            Source path if found, None otherwise
        """
        return self._plugin_paths.get(plugin_type, {}).get(provider_type)

    def clear_path_cache(self, path: Optional[str] = None) -> None:
        """Clear cache for a specific path or all paths.

        Args:
            path: Path to clear from cache, or None to clear all
        """
        if path:
            if path in self._scanned_paths:
                self._scanned_paths.remove(path)
            if path in self._scan_timestamps:
                del self._scan_timestamps[path]
            # Remove any plugins loaded from this path
            for plugin_type in list(self._plugin_paths.keys()):
                for provider_type, source_path in list(
                    self._plugin_paths[plugin_type].items()
                ):
                    if source_path == path:
                        del self._plugin_paths[plugin_type][provider_type]
                        if provider_type in self._plugins.get(plugin_type, {}):
                            del self._plugins[plugin_type][provider_type]
        else:
            self._scanned_paths.clear()
            self._scan_timestamps.clear()
            self._plugin_paths.clear()
            self._plugins.clear()
            self._loaded_modules.clear()
            self._validation_errors.clear()
            self._discovered_plugins.clear()

    def is_path_cached(self, path: str, max_age: float = 300.0) -> bool:
        """Check if a path is already in the cache and not expired.

        Args:
            path: Path to check
            max_age: Maximum age in seconds before cache is considered stale

        Returns:
            True if path is cached and not expired
        """
        if path not in self._scanned_paths:
            return False

        # Check if cache is stale
        if path in self._scan_timestamps:
            elapsed = time.time() - self._scan_timestamps[path]
            if elapsed > max_age:
                return False

        return True

    def mark_path_scanned(self, path: str) -> None:
        """Mark a path as scanned and update timestamp.

        Args:
            path: Path that was scanned
        """
        self._scanned_paths.add(path)
        self._scan_timestamps[path] = time.time()

    def add_validation_error(self, path: str, error: str) -> None:
        """Add a validation error for a path.

        Args:
            path: Path with error
            error: Error message
        """
        self._validation_errors[path] = error

    def get_validation_errors(self) -> Dict[str, str]:
        """Get all validation errors.

        Returns:
            Dict mapping paths to error messages
        """
        return dict(self._validation_errors)

    def get_cached_module(self, module_path: str) -> Optional[Any]:
        """Get a cached module if available.

        Args:
            module_path: Import path of module

        Returns:
            Module if cached, None otherwise
        """
        return self._loaded_modules.get(module_path)


# Global plugin registry
_plugin_registry = PluginRegistry()


# Function to reset the registry (useful for testing)
def reset_registry() -> None:
    """Reset the plugin registry."""
    global _plugin_registry
    _plugin_registry = PluginRegistry()


# Get the plugin registry
def get_registry() -> PluginRegistry:
    """Get the plugin registry.

    Returns:
        Plugin registry
    """
    return _plugin_registry


# Async discovery function
async def discover_plugins(
    paths: List[str], lazy_load: bool = True, preload_types: Optional[List[str]] = None
) -> None:
    """Discover plugins.

    Args:
        paths: Paths to search for plugins
        lazy_load: Whether to lazily load plugins or load them all immediately
        preload_types: Types of plugins to preload even in lazy loading mode
    """
    global \
        _discovery_initialized, \
        _lazy_discovery_enabled, \
        _plugin_paths_scanned, \
        _available_paths

    # Store paths for later if needed
    _available_paths = paths

    # Set lazy loading flag
    _lazy_discovery_enabled = lazy_load

    # Mark discovery as initialized
    _discovery_initialized = True

    # If not using lazy loading, discover and load all plugins now
    if not lazy_load:
        await _discover_and_load_all(paths)
        _plugin_paths_scanned = True
        return

    # Otherwise, just discover plugin metadata without loading
    registry = get_registry()
    discovered = await registry.discover_without_loading(paths)

    # Register all discovered plugins
    for plugin_type, providers in discovered.items():
        for provider_type, metadata in providers.items():
            registry.register_discovered_plugin(plugin_type, provider_type, metadata)

    # Preload specified types if requested
    if preload_types:
        for plugin_type in preload_types:
            if plugin_type in discovered:
                for provider_type, metadata in discovered[plugin_type].items():
                    await registry._load_plugin(plugin_type, provider_type, metadata)

    # Mark paths as scanned
    _plugin_paths_scanned = True

    # Log discovery info
    logger.info(
        f"Discovered {sum(len(providers) for providers in discovered.values())} plugins"
    )


async def _discover_and_load_all(paths: List[str]) -> None:
    """Discover and load all plugins.

    Args:
        paths: Paths to search for plugins
    """
    registry = get_registry()
    discovered = await registry.discover_without_loading(paths)

    # Load all discovered plugins
    for plugin_type, providers in discovered.items():
        for provider_type, metadata in providers.items():
            await registry._load_plugin(plugin_type, provider_type, metadata)


async def ensure_discovery_initialized() -> None:
    """Ensure that plugin discovery has been initialized.

    This is called automatically when plugins are requested.
    """
    global _discovery_initialized, _plugin_paths_scanned, _available_paths

    if not _discovery_initialized:
        # Default paths if not specified
        default_paths = [
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "plugins"),
            os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "plugins"
            ),
            os.path.join(os.getcwd(), "plugins"),
        ]
        await discover_plugins(default_paths, lazy_load=True)

    # If paths are available but not scanned, scan them now
    if not _plugin_paths_scanned and _available_paths:
        registry = get_registry()
        discovered = await registry.discover_without_loading(_available_paths)

        # Register all discovered plugins
        for plugin_type, providers in discovered.items():
            for provider_type, metadata in providers.items():
                registry.register_discovered_plugin(
                    plugin_type, provider_type, metadata
                )

        _plugin_paths_scanned = True


async def get_plugin(
    plugin_type: str, provider_type: str
) -> Optional[Type[PepperpyPlugin]]:
    """Get a plugin class.

    Args:
        plugin_type: Type of plugin
        provider_type: Type of provider

    Returns:
        Plugin class if found, None otherwise
    """
    # Ensure discovery is initialized
    await ensure_discovery_initialized()

    # Get plugin from registry
    return await get_registry().get_plugin(plugin_type, provider_type)


# For backward compatibility, sync version just delegates to registry
def get_plugin_by_provider(
    plugin_type: str, provider_type: str
) -> Optional[Type[PepperpyPlugin]]:
    """Get a plugin by provider type synchronously (for backward compatibility).

    Args:
        plugin_type: Type of plugin
        provider_type: Type of provider

    Returns:
        Plugin class if found, None otherwise
    """
    # This doesn't ensure discovery is initialized, it just checks the registry
    return get_registry().get_plugin_by_provider(plugin_type, provider_type)


# Add a utility function to register plugin aliases
def register_plugin_alias(
    plugin_type: str,
    alias: str,
    provider_type: str,
    config_override: Optional[str] = None,
) -> None:
    """Register a plugin alias.

    Args:
        plugin_type: Type of plugin
        alias: Alias name
        provider_type: Actual provider type
        config_override: Optional configuration override (e.g., model name)
    """
    global _plugin_aliases

    if plugin_type not in _plugin_aliases:
        _plugin_aliases[plugin_type] = {}

    value = provider_type
    if config_override:
        value = f"{provider_type}:{config_override}"

    _plugin_aliases[plugin_type][alias] = value
    logger.debug(f"Registered plugin alias: {plugin_type}/{alias} -> {value}")


# Add a utility function to register plugin fallbacks
def register_plugin_fallbacks(plugin_type: str, fallbacks: List[str]) -> None:
    """Register fallback providers for a plugin type.

    Args:
        plugin_type: Type of plugin
        fallbacks: List of provider types to try in order
    """
    global _plugin_fallbacks

    _plugin_fallbacks[plugin_type] = fallbacks
    logger.debug(f"Registered plugin fallbacks for {plugin_type}: {fallbacks}")


# List all available plugins (both loaded and discovered)
def list_available_plugins() -> (
    Dict[str, Dict[str, Union[Type[PepperpyPlugin], Dict[str, Any]]]]
):
    """List all available plugins (both loaded and discovered).

    Returns:
        Dict of plugin types to provider types to plugin classes or metadata
    """
    registry = get_registry()

    # Combine loaded and discovered plugins
    result = {}

    # Add loaded plugins
    loaded = registry.list_plugins()
    for plugin_type, providers in loaded.items():
        if plugin_type not in result:
            result[plugin_type] = {}
        result[plugin_type].update(providers)

    # Add discovered but not loaded plugins
    discovered = registry.list_discovered_plugins()
    for plugin_type, providers in discovered.items():
        if plugin_type not in result:
            result[plugin_type] = {}

        # Only add providers that aren't already loaded
        for provider_type, metadata in providers.items():
            if provider_type not in result.get(plugin_type, {}):
                result[plugin_type][provider_type] = metadata

    return result
