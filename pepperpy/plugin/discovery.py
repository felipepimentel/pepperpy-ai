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
from pepperpy.plugin.utils import get_plugin_id, parse_plugin_id

logger = get_logger(__name__)

# Known discovery providers
_discovery_providers: dict[str, Any] = {}

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
        max_recursion_depth = 3  # Increased to handle plugins/<type>/<category>/<name>

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

            # Skip __pycache__ directories
            if item == "__pycache__":
                continue

            # Check if the item is a directory
            if os.path.isdir(item_path):
                # Skip directories with a .disabled file
                if os.path.exists(os.path.join(item_path, ".disabled")):
                    logger.info(f"Skipping disabled plugin in directory: {item_path}")
                    continue

                # Check if provider.py exists in the directory
                provider_file = os.path.join(item_path, "provider.py")
                if os.path.exists(provider_file):
                    logger.info(f"Found provider.py in {item_path}")
                    
                    # Get plugin type from directory structure
                    parts = item_path.split(os.sep)
                    plugins_index = parts.index("plugins")
                    if plugins_index + 1 < len(parts):
                        plugin_type = parts[plugins_index + 1]
                        plugin_name = parts[-1]
                        
                        logger.info(f"Found plugin: type={plugin_type}, name={plugin_name}")
                        
                        # Create plugin info
                        plugin_info = PluginInfo(
                            name=plugin_name,
                            version="0.1.0",  # Default version
                            description=f"{plugin_type} plugin for {plugin_name}",
                            provider_name=plugin_name,
                            plugin_type=plugin_type,
                            module_path=provider_file,
                            module_name=f"pepperpy_plugin_{plugin_type}_{plugin_name}_{hash(item_path) & 0xFFFFFFFF}",
                            class_name=None,  # Will be discovered during loading
                            config={},
                        )

                        # Register plugin info
                        logger.info(f"Registering plugin {plugin_name} in domain {plugin_type}")
                        register_plugin_info(plugin_type, plugin_name, plugin_info)
                        logger.info(f"Registered plugin info: {plugin_type}/{plugin_name}")

                        # Add to the local plugins dict for compatibility
                        if plugin_type not in self._plugins:
                            self._plugins[plugin_type] = {}
                        self._plugins[plugin_type][plugin_name] = plugin_info
                        logger.info(f"Added plugin to local dict: {plugin_type}/{plugin_name}")

                # Recurse into subdirectories up to max_recursion_depth
                elif recursion_depth < max_recursion_depth:
                    self._scan_directory(item_path, recursion_depth + 1)

    def _load_plugin_info(self, plugin_dir: str, provider_file: str) -> PluginInfo | None:
        """Load plugin information from a plugin directory.

        Args:
            plugin_dir: Plugin directory path
            provider_file: Path to provider.py file

        Returns:
            Plugin information or None
        """
        try:
            # Extract plugin type and name from directory structure
            # plugins/<plugin_type>/<provider_name>
            parts = plugin_dir.split(os.sep)
            if len(parts) < 2:
                logger.warning(f"Invalid plugin directory structure: {plugin_dir}")
                return None

            plugin_type = parts[-2]  # Second to last part is plugin_type
            provider_name = parts[-1]  # Last part is provider_name

            # Create a unique module name based on plugin directory path
            module_name = f"pepperpy_plugin_{plugin_type}_{provider_name}_{hash(plugin_dir) & 0xFFFFFFFF}"

            return PluginInfo(
                name=provider_name,
                version="0.1.0",  # Default version
                description=f"{plugin_type} plugin for {provider_name}",
                provider_name=provider_name,
                plugin_type=plugin_type,
                module_path=provider_file,
                module_name=module_name,
                class_name=None,  # Will be discovered during loading
                config={},
            )

        except Exception as e:
            logger.exception(f"Error loading plugin info from {plugin_dir}: {e}")
            return None


def _find_plugin_class(
    module: Any, plugin_type: str, provider_name: str, plugin_info: PluginInfo
) -> Any:
    """Find the plugin class in the given module.

    Args:
        module: Module to search
        plugin_type: Plugin type
        provider_name: Provider name
        plugin_info: Plugin information

    Returns:
        Plugin class or None

    Raises:
        DiscoveryError: If plugin class cannot be found
    """
    # Store all potential matches to prioritize them later
    potential_matches = []

    # First pass - collect all potential classes
    for name, obj in inspect.getmembers(module):
        if not inspect.isclass(obj):
            continue

        # Skip abstract classes
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

        # Check for name that ends with Provider
        if name.endswith("Provider"):
            potential_matches.append((obj, 80))
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
            try:
                # Python 3.10+
                entry_points = importlib.metadata.entry_points(group="pepperpy.plugins")
                entry_points_list = list(entry_points)
            except TypeError:
                # Python < 3.10
                entry_points = importlib.metadata.entry_points()
                entry_points_list = [
                    ep for ep in entry_points if ep.group == "pepperpy.plugins"
                ]

            for entry_point in entry_points_list:
                plugin_info = self._load_entry_point(entry_point)
                if plugin_info:
                    domain = plugin_info.plugin_type
                    name = plugin_info.name

                    register_plugin_info(domain, name, plugin_info)
                    logger.debug(
                        f"Registered plugin info from entry point: {domain}/{name}"
                    )

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
            plugin_class = entry_point.load()

            if not _is_plugin(plugin_class):
                logger.warning(
                    f"Entry point {entry_point.name} does not provide a Plugin"
                )
                return None

            name = getattr(plugin_class, "name", entry_point.name)
            version = getattr(plugin_class, "version", "0.1.0")
            description = getattr(plugin_class, "description", "")
            plugin_type = getattr(plugin_class, "plugin_type", None)
            provider_name = getattr(plugin_class, "provider_name", None)

            if not plugin_type or not provider_name:
                logger.warning(
                    f"Entry point {entry_point.name} missing plugin_type or provider_name"
                )
                return None

            return PluginInfo(
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

    logger.debug(f"Looking for plugin in directory: {plugin_dir}")

    if not plugin_dir.exists():
        raise DiscoveryError(f"Plugin directory not found: {plugin_dir}")

    # Check if plugin is disabled
    if (plugin_dir / ".disabled").exists():
        raise DiscoveryError(f"Plugin is disabled: {domain}/{plugin_name}")

    # Check for provider.py
    provider_file = plugin_dir / "provider.py"
    if not provider_file.exists():
        raise DiscoveryError(
            f"Provider file not found: {provider_file}"
        )

    try:
        logger.debug(f"Creating FileSystemDiscovery for directory: {plugin_dir.parent}")
        # Create a FileSystemDiscovery instance just for this plugin
        discovery = FileSystemDiscovery([str(plugin_dir.parent)])

        # Discover plugins (this will register them for lazy loading)
        logger.debug("Running plugin discovery")
        await discovery.discover_plugins()

        # Now try to get the plugin from the registry again
        logger.debug("Attempting to get plugin from registry after discovery")
        plugin_class = await get_plugin(domain, plugin_name)
        if plugin_class:
            logger.debug(f"Successfully loaded plugin class: {plugin_class.__name__}")
            return plugin_class

        # If still not found, try direct loading
        logger.debug("Plugin not found in registry, attempting direct load")
        
        # Create plugin info and load directly
        plugin_info = discovery._load_plugin_info(str(plugin_dir), str(provider_file))
        if not plugin_info:
            raise DiscoveryError(
                f"Failed to create plugin info from {plugin_dir}"
            )

        plugin_class = await load_plugin(plugin_info)
        if not plugin_class:
            raise DiscoveryError(
                f"Failed to load plugin class for {domain}/{plugin_name}"
            )

        logger.debug(f"Successfully loaded plugin class directly: {plugin_class.__name__}")
        return plugin_class
    except Exception as e:
        logger.exception(f"Failed to load plugin {domain}/{plugin_name}")
        raise DiscoveryError(f"Failed to load plugin {domain}/{plugin_name}: {e}")
