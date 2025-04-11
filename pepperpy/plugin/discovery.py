"""
PepperPy Plugin Discovery.

Functionality for discovering PepperPy plugins.
"""

from __future__ import annotations

import importlib.metadata
import importlib.util
import inspect
import os
import sys
from pathlib import Path
from typing import Any

import yaml

from pepperpy.core.logging import get_logger
from pepperpy.plugin.base import PepperpyPlugin, PluginDiscoveryProtocol, PluginInfo
from pepperpy.plugin.provider import BasePluginProvider
from pepperpy.plugin.registry import get_plugin, register_plugin_info

logger = get_logger(__name__)

# Known discovery providers
_discovery_providers: dict[str, Any] = {}

DEFAULT_PLUGIN_TYPES = [
    "llm",
    "tts",
    "agent",
    "tool",
    "cache",
    "discovery",
    "storage",
    "rag",
    "content",
    "embeddings",
    "workflow",
]

PROVIDER_PLUGIN_MAP = {
    "llm": "LLMProvider",
    "tts": "TTSProvider",
    "agent": "AgentProvider",
    "tool": "ToolProvider",
    "cache": "CacheProvider",
    "storage": "StorageProvider",
    "rag": "RAGProvider",
    "content": "ContentProvider",
    "embeddings": "EmbeddingsProvider",
    "workflow": "WorkflowProvider",
}

# Global flag to track if we've already set the environment variable
_set_modules_env = False


class DiscoveryError(Exception):
    """Error during plugin discovery."""


async def load_plugin(plugin_info: PluginInfo) -> Any:
    """Load a plugin from its information.

    Args:
        plugin_info: Plugin information

    Returns:
        Plugin class

    Raises:
        DiscoveryError: If plugin cannot be loaded
    """
    plugin_class = None

    # Check if the plugin is already loaded
    if plugin_info.module_path and plugin_info.module_name:
        # Import the module
        try:
            logger.info(f"Loading plugin from {plugin_info.module_path}")
            spec = importlib.util.spec_from_file_location(
                plugin_info.module_name, plugin_info.module_path
            )

            if not spec or not spec.loader:
                raise DiscoveryError(
                    f"Cannot load module spec for {plugin_info.module_path}"
                )

            module = importlib.util.module_from_spec(spec)
            sys.modules[plugin_info.module_name] = module
            spec.loader.exec_module(module)

            # Find the plugin class
            plugin_type = plugin_info.plugin_type
            provider_name = plugin_info.provider_name

            if not plugin_type or not provider_name:
                raise DiscoveryError(
                    f"Missing plugin_type or provider_name in {plugin_info.module_path}"
                )

            plugin_class = _find_plugin_class(
                module, plugin_type, provider_name, plugin_info
            )

        except Exception as e:
            logger.exception(
                f"Error loading plugin from {plugin_info.module_path}: {e}"
            )
            raise DiscoveryError(f"Error loading plugin: {e}")

    return plugin_class


class FileSystemDiscovery(PluginDiscoveryProtocol):
    """Discovery provider for plugins in the filesystem."""

    def __init__(self, plugin_directories: list[str] | None = None):
        """Initialize."""
        self._dirs: set[str] = set()
        self._plugins: dict[str, Any] = {}
        if plugin_directories:
            for directory in plugin_directories:
                self.add_directory(directory)

    def add_directory(self, directory: str | Path) -> None:
        """Add a directory to scan for plugins.

        Args:
            directory: Directory path
        """
        directory_str = str(directory)
        self._dirs.add(directory_str)

    def add_default_directories(self) -> None:
        """Add default directories to scan."""
        # Add the "plugins" directory in the current working directory
        self.add_directory(os.path.join(os.getcwd(), "plugins"))

    async def discover_plugins(self) -> dict[str, Any]:
        """Discover plugins.

        Returns:
            Dict of plugins by domain
        """
        for directory in self._dirs:
            self._scan_directory(directory)
        return self._plugins

    async def load_plugin(self, plugin_info: PluginInfo) -> Any:
        """Load a plugin from its information.

        Args:
            plugin_info: Plugin information

        Returns:
            Loaded plugin class
        """
        return await load_plugin(plugin_info)

    def _scan_directory(self, directory: str, recursion_depth: int = 0) -> None:
        """Scan a directory for plugins.

        Args:
            directory: Directory path
            recursion_depth: Recursion depth
        """
        max_recursion_depth = 2  # Limit recursion to 2 levels

        logger.info(f"Scanning directory: {directory}")

        if not os.path.exists(directory):
            logger.warning(f"Directory does not exist: {directory}")
            return

        # List all items in the directory
        try:
            items = os.listdir(directory)
        except OSError as e:
            logger.error(f"Error listing directory {directory}: {e}")
            return

        for item in items:
            item_path = os.path.join(directory, item)

            # Check if the item is a directory
            if os.path.isdir(item_path):
                # Skip directories with a .disabled file
                if os.path.exists(os.path.join(item_path, ".disabled")):
                    logger.info(f"Skipping disabled plugin in directory: {item_path}")
                continue

                # Check if plugin.yaml exists in the directory
                plugin_yaml = os.path.join(item_path, "plugin.yaml")
                if os.path.exists(plugin_yaml):
                    # Load plugin information
                    plugin_info = self._load_plugin_info(plugin_yaml, item_path)

                if plugin_info:
                    # Register plugin info for lazy loading instead of loading it immediately
                    domain = plugin_info.plugin_type
                    name = (
                        f"{domain}/{plugin_info.provider_name}"
                        if domain != "discovery"
                        else plugin_info.provider_name
                    )

                    register_plugin_info(domain, name, plugin_info)
                    logger.debug(f"Registered plugin info: {domain}/{name}")

                    # Add to the local plugins dict for compatibility
                    if domain not in self._plugins:
                        self._plugins[domain] = {}
                    self._plugins[domain][name] = plugin_info
                # Recurse into subdirectories up to max_recursion_depth
                elif recursion_depth < max_recursion_depth:
                    self._scan_directory(item_path, recursion_depth + 1)

    def _load_plugin_info(self, yaml_file: str, plugin_dir: str) -> PluginInfo | None:
        """Load plugin information from a yaml file.

        Args:
            yaml_file: Path to plugin.yaml file
            plugin_dir: Plugin directory

        Returns:
            Plugin information or None
        """
        try:
            with open(yaml_file, encoding="utf-8") as f:
                data = yaml.safe_load(f)

            # Check required fields
            required_fields = [
                "name",
                "version",
                "description",
                "plugin_type",
                "provider_name",
            ]
            for field in required_fields:
                if field not in data:
                    logger.warning(f"Missing required field '{field}' in {yaml_file}")
                    return None

            plugin_type = data["plugin_type"]
            provider_name = data["provider_name"]

            # Look for the plugin implementation
            if plugin_type in [
                "llm",
                "tts",
                "agent",
                "tool",
                "cache",
                "storage",
                "rag",
                "content",
                "embeddings",
                "workflow",
            ]:
                # Look for <plugin_type>_provider.py or provider.py
                provider_file = os.path.join(plugin_dir, f"{plugin_type}_provider.py")
                if not os.path.exists(provider_file):
                    provider_file = os.path.join(plugin_dir, "provider.py")

                if not os.path.exists(provider_file):
                    # Look for <provider_name>.py
                    provider_file = os.path.join(plugin_dir, f"{provider_name}.py")

                # For workflow plugins, also check for workflow.py
                if not os.path.exists(provider_file) and plugin_type == "workflow":
                    workflow_file = os.path.join(plugin_dir, "workflow.py")
                    if os.path.exists(workflow_file):
                        provider_file = workflow_file

                if not os.path.exists(provider_file):
                    logger.warning(
                        f"Cannot find provider implementation in {plugin_dir}"
                    )
                    return None

                # Create a unique module name based on plugin directory path
                module_name = f"pepperpy_plugin_{plugin_type}_{provider_name}_{hash(plugin_dir) & 0xFFFFFFFF}"

                return PluginInfo(
                    name=data["name"],
                    version=data["version"],
                    description=data["description"],
                    provider_name=provider_name,
                    plugin_type=plugin_type,
                    module_path=provider_file,
                    module_name=module_name,
                    class_name=None,  # Will be discovered during loading
                    config=data.get("config", {}),
                )
            else:
                logger.warning(f"Unknown plugin type '{plugin_type}' in {yaml_file}")
                return None

        except Exception as e:
            logger.exception(f"Error loading plugin info from {yaml_file}: {e}")
            return None

        return None


def _find_plugin_class(
    module: Any, plugin_type: str, provider_name: str, plugin_info: PluginInfo
) -> Any:
    """Find the plugin class in the given module.

    Args:
    module: Module to search
    plugin_type: Plugin type (llm, tts, etc.)
    provider_name: Provider name
        plugin_info: Plugin information

    Returns:
    Plugin class or None

    Raises:
        DiscoveryError: If plugin class cannot be found
    """
    # Check if there's a class with the expected name pattern
    provider_class_name = PROVIDER_PLUGIN_MAP.get(plugin_type)
    if not provider_class_name:
        raise DiscoveryError(
            f"No provider class mapping for plugin type: {plugin_type}"
        )

    logger.debug(
        f"Looking for provider class {provider_class_name} in {module.__name__}"
    )

    # Store all potential matches to prioritize them later
    potential_matches = []

    # First pass - collect all potential classes
    for name, obj in inspect.getmembers(module):
        if not inspect.isclass(obj):
            continue

        # Skip abstract classes - this is the key fix
        if inspect.isabstract(obj):
            logger.debug(f"Skipping abstract class: {name}")
            continue

        # If the class name is already known, it's a strong match
        if plugin_info.class_name and name == plugin_info.class_name:
            return obj

        # Check if this class inherits from ProviderPlugin
        if _is_provider_plugin(obj, plugin_type):
            logger.info(f"Found provider class: {name}")
            potential_matches.append((obj, 100))  # Highest priority
            continue

        # Check for exact match with provider class name
        if name == provider_class_name:
            potential_matches.append((obj, 90))
            continue

        # Check for name that ends with the provider class name
        if name.endswith(provider_class_name):
            potential_matches.append((obj, 80))
            continue

        # Check for any *Provider class
        if "Provider" in name:
            potential_matches.append((obj, 70))
            continue

        # Finally, check for any class that inherits from Plugin
        if _is_plugin(obj):
            potential_matches.append((obj, 60))
            continue

    # Sort by priority (highest first) and return the best match
    if potential_matches:
        potential_matches.sort(key=lambda x: x[1], reverse=True)
        logger.info(f"Selected provider class: {potential_matches[0][0].__name__}")
        return potential_matches[0][0]

    # If we couldn't find a non-abstract class, we can look for the best abstract class as fallback
    for name, obj in inspect.getmembers(module):
        if not inspect.isclass(obj) or not inspect.isabstract(obj):
            continue

        if _is_plugin(obj):
            logger.warning(
                f"Found only abstract plugin class: {name}, this may cause instantiation errors"
            )
            return obj

    raise DiscoveryError(
        f"Cannot find provider class for {plugin_type}/{provider_name} in {module.__name__}"
    )


def _is_plugin(obj: Any) -> bool:
    """Check if the given object is a Plugin.

    Args:
        obj: Object to check

    Returns:
        True if the object is a Plugin
    """
    return inspect.isclass(obj) and issubclass(obj, PepperpyPlugin)


def _is_provider_plugin(obj: Any, plugin_type: str) -> bool:
    """Check if the given object is a ProviderPlugin of the specified type.

    Args:
        obj: Object to check
        plugin_type: Plugin type (llm, tts, etc.)

    Returns:
        True if the object is a ProviderPlugin of the specified type
    """
    if not inspect.isclass(obj) or not issubclass(obj, BasePluginProvider):
        return False

    # Check if plugin_type is defined in the class attributes or via class annotation
    # For BasePluginProvider, we need to check attributes more carefully
    try:
        # Try direct attribute access safely without triggering the linter
        plugin_type_value = getattr(obj, "plugin_type", None)
        if plugin_type_value is not None and plugin_type_value == plugin_type:
            return True

        # Check class annotations or attributes
        class_annotations = getattr(obj, "__annotations__", {})
        if "plugin_type" in class_annotations:
            return True

        return False
    except Exception:
        return False


class PackageDiscovery(PluginDiscoveryProtocol):
    """Discovery provider for plugins in installed packages."""

    def __init__(self) -> None:
        """Initialize."""
        self._plugins: dict[str, Any] = {}

    async def discover_plugins(self) -> dict[str, Any]:
        """Discover plugins.

        Returns:
            Dict of plugins by domain
        """
        try:
            # Look for entry points in the group "pepperpy.plugins"
            # Handle different versions of importlib.metadata
            try:
                # Python 3.10+
                entry_points = importlib.metadata.entry_points(group="pepperpy.plugins")
                # Convert to list for compatibility with both versions
                entry_points_list = list(entry_points)
            except TypeError:
                # Python < 3.10
                entry_points = importlib.metadata.entry_points()
                # Filter entry points manually for older Python versions
                entry_points_list = [
                    ep for ep in entry_points if ep.group == "pepperpy.plugins"
                ]

            for entry_point in entry_points_list:
                plugin_info = self._load_entry_point(entry_point)
                if plugin_info:
                    # Register plugin info for lazy loading
                    domain = plugin_info.plugin_type
                    name = (
                        f"{domain}/{plugin_info.provider_name}"
                        if domain != "discovery"
                        else plugin_info.provider_name
                    )

                    register_plugin_info(domain, name, plugin_info)
                    logger.debug(
                        f"Registered plugin info from entry point: {domain}/{name}"
                    )

                    # Add to the local plugins dict for compatibility
                    if domain not in self._plugins:
                        self._plugins[domain] = {}
                    self._plugins[domain][name] = plugin_info

        except Exception as e:
            logger.exception(f"Error discovering plugins from packages: {e}")

        return self._plugins

    async def load_plugin(self, plugin_info: PluginInfo) -> Any:
        """Load a plugin from its information.

        Args:
            plugin_info: Plugin information

        Returns:
            Loaded plugin class
        """
        return await load_plugin(plugin_info)

    def _load_entry_point(self, entry_point: Any) -> PluginInfo | None:
        """Load plugin information from an entry point.

        Args:
            entry_point: Entry point

        Returns:
            Plugin information or None
        """
        try:
            # Load the entry point
            plugin_class = entry_point.load()

            # Check if it's a Plugin
            if not _is_plugin(plugin_class):
                logger.warning(
                    f"Entry point {entry_point.name} does not provide a Plugin"
                )
                return None

            # Extract plugin information
            name = getattr(plugin_class, "name", entry_point.name)
            version = getattr(plugin_class, "version", "0.0.0")
            description = getattr(plugin_class, "description", "")
            plugin_type = getattr(plugin_class, "plugin_type", None)
            provider_name = getattr(plugin_class, "provider_name", None)

            if not plugin_type:
                logger.warning(
                    f"Entry point {entry_point.name} does not specify a plugin_type"
                )
                return None

            if not provider_name:
                logger.warning(
                    f"Entry point {entry_point.name} does not specify a provider_name"
                )
                return None

            # Create plugin info
            plugin_info = PluginInfo(
                name=name,
                version=version,
                description=description,
                provider_name=provider_name,
                plugin_type=plugin_type,
                class_name=plugin_class.__name__,
                module_name=plugin_class.__module__,
                module_path=None,  # Not applicable for entry points
                config={},
            )

            return plugin_info

        except Exception as e:
            logger.exception(f"Error loading entry point {entry_point.name}: {e}")
            return None


class PluginDiscoveryProvider(PluginDiscoveryProtocol):
    """Plugin discovery provider."""

    def __init__(
        self, discovery_providers: list[PluginDiscoveryProtocol] | None = None
    ):
        """Initialize."""
        self._discovery_providers: list[PluginDiscoveryProtocol] = []
        self.config: dict[str, Any] = {}
        if discovery_providers:
            self._discovery_providers.extend(discovery_providers)
        self._init_discovery_providers()

    def _init_discovery_providers(self) -> None:
        """Initialize discovery providers."""
        # Add file system discovery
        fs_discovery = FileSystemDiscovery()

        # Add default directory if no custom paths provided
        if self.config.get("scan_paths"):
            # Add custom paths from config
            for path in self.config["scan_paths"]:
                fs_discovery.add_directory(path)
        else:
            # Use default discovery path
            fs_discovery.add_default_directories()

        self._discovery_providers.append(fs_discovery)

        # Add package discovery
        package_discovery = PackageDiscovery()
        self._discovery_providers.append(package_discovery)

    async def discover_plugins(self) -> dict[str, Any]:
        """Discover plugins.

        Returns:
            Dict of plugins by domain
        """
        all_plugins: dict[str, dict[str, Any]] = {}

        for provider in self._discovery_providers:
            plugins = await provider.discover_plugins()

            # Merge plugins
            for domain, domain_plugins in plugins.items():
                if domain not in all_plugins:
                    all_plugins[domain] = {}
                all_plugins[domain].update(domain_plugins)

        return all_plugins

    async def load_plugin(self, plugin_info: PluginInfo) -> Any:
        """Load a plugin from its information.

        Args:
            plugin_info: Plugin information

        Returns:
            Loaded plugin class
        """
        return await load_plugin(plugin_info)


_discovery_provider = PluginDiscoveryProvider()


def get_discovery_provider() -> PluginDiscoveryProtocol:
    """Get the default discovery provider.

    Returns:
        The default discovery provider
    """
    global _discovery_provider
    return _discovery_provider


async def discover_plugins() -> dict[str, Any]:
    """Discover plugins.

    Returns:
        Dict of plugins by domain
    """
    provider = get_discovery_provider()
    return await provider.discover_plugins()


async def load_specific_plugin(domain: str, plugin_name: str) -> Any:
    """Load a specific plugin by domain and name.

    Args:
        domain: The plugin domain (e.g., "workflow", "llm", etc.)
        plugin_name: The name of the plugin to load

    Returns:
        The loaded plugin instance

    Raises:
        DiscoveryError: If the plugin cannot be found or loaded
    """
    logger.info(f"Loading specific plugin: {domain}/{plugin_name}")

    # First, try to get it from the registry if it's already registered
    plugin_class = await get_plugin(domain, plugin_name)
    if plugin_class:
        logger.info(f"Found plugin in registry: {domain}/{plugin_name}")
        return plugin_class

    # If not in registry, determine the likely plugin path
    base_plugin_dir = Path.cwd() / "plugins"
    plugin_dir = base_plugin_dir / domain / plugin_name

    # If not found in the main plugins directory, try alternate locations
    if not plugin_dir.exists():
        # Try looking in domain subdirectories (some plugins might be nested)
        for subdir in base_plugin_dir.glob(f"{domain}/*/{plugin_name}"):
            if subdir.is_dir():
                plugin_dir = subdir
                break

    if not plugin_dir.exists():
        raise DiscoveryError(f"Plugin directory not found: {plugin_dir}")

    # Check if plugin is disabled
    if (plugin_dir / ".disabled").exists():
        raise DiscoveryError(f"Plugin is disabled: {domain}/{plugin_name}")

    # Check for plugin.yaml
    plugin_config_path = plugin_dir / "plugin.yaml"
    if not plugin_config_path.exists():
        raise DiscoveryError(
            f"Plugin configuration file not found: {plugin_config_path}"
        )

    try:
        # Create a FileSystemDiscovery instance just for this plugin
        discovery = FileSystemDiscovery([str(plugin_dir.parent)])

        # Discover plugins (this will register them for lazy loading)
        await discovery.discover_plugins()

        # Now try to get the plugin from the registry again
        plugin_class = await get_plugin(domain, plugin_name)
        if plugin_class:
            return plugin_class

        # If still not found, try direct loading
        # Load the plugin config
        with open(plugin_config_path) as f:
            plugin_config = yaml.safe_load(f)

        # Create plugin info and load directly
        plugin_info = discovery._load_plugin_info(
            str(plugin_config_path), str(plugin_dir)
        )
        if not plugin_info:
            raise DiscoveryError(
                f"Failed to create plugin info from {plugin_config_path}"
            )

        plugin_class = await load_plugin(plugin_info)
        if not plugin_class:
            raise DiscoveryError(
                f"Failed to load plugin class for {domain}/{plugin_name}"
            )

        return plugin_class
    except Exception as e:
        raise DiscoveryError(f"Failed to load plugin {domain}/{plugin_name}: {e}")
