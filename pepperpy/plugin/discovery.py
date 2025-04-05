"""
Plugin discovery module.

This module provides functionality for discovering plugins in the filesystem,
installed packages, and registry entries.
"""

import importlib
import importlib.util
import inspect
import os
import sys
from typing import Any

from pepperpy.core.errors import PepperpyError
from pepperpy.core.logging import get_logger
from pepperpy.plugin.base import (
    PluginDiscoveryProtocol,
    PluginInfo,
    PluginSource,
)

logger = get_logger(__name__)


class DiscoveryError(PepperpyError):
    """Error raised during plugin discovery."""

    pass


class FileSystemDiscovery:
    """Discovers plugins in the filesystem."""

    def __init__(self, plugin_directories: list[str] | None = None):
        """Initialize the filesystem discovery.

        Args:
            plugin_directories: List of directories to scan for plugins
        """
        self.plugin_directories = plugin_directories or []

        # Add default plugin directories
        self._add_default_directories()

    def _add_default_directories(self) -> None:
        """Add default plugin directories."""
        # Add the current directory's plugins folder
        cwd_plugins = os.path.join(os.getcwd(), "plugins")
        if os.path.isdir(cwd_plugins) and cwd_plugins not in self.plugin_directories:
            self.plugin_directories.append(cwd_plugins)

        # Add user plugins directory
        user_plugins = os.path.expanduser("~/.pepperpy/plugins")
        if os.path.isdir(user_plugins) and user_plugins not in self.plugin_directories:
            self.plugin_directories.append(user_plugins)

        # Add system plugins directory if available
        sys_plugins = "/etc/pepperpy/plugins"
        if os.path.isdir(sys_plugins) and sys_plugins not in self.plugin_directories:
            self.plugin_directories.append(sys_plugins)

    async def discover_plugins(self) -> list[PluginInfo]:
        """Discover plugins in registered directories.

        Returns:
            List of discovered plugin information
        """
        results = []

        for directory in self.plugin_directories:
            if not os.path.exists(directory):
                logger.warning(f"Plugin directory does not exist: {directory}")
                continue

            logger.debug(f"Scanning directory for plugins: {directory}")
            directory_results = await self._scan_directory(directory)
            results.extend(directory_results)

        return results

    async def _scan_directory(self, directory: str) -> list[PluginInfo]:
        """Scan a directory for plugins.

        Args:
            directory: Directory to scan

        Returns:
            List of discovered plugin information
        """
        results = []

        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)

            if not os.path.isdir(item_path):
                continue

            # Check for plugin.yaml file
            plugin_yaml = os.path.join(item_path, "plugin.yaml")
            if os.path.exists(plugin_yaml):
                plugin_info = await self._load_plugin_info(item_path, plugin_yaml)
                if plugin_info:
                    results.append(plugin_info)

            # Recursively scan subdirectories
            subdir_results = await self._scan_directory(item_path)
            results.extend(subdir_results)

        return results

    async def _load_plugin_info(
        self, plugin_dir: str, plugin_yaml: str
    ) -> PluginInfo | None:
        """Load plugin information from a plugin.yaml file.

        Args:
            plugin_dir: Plugin directory
            plugin_yaml: Path to plugin.yaml file

        Returns:
            Plugin information or None if not valid
        """
        try:
            import yaml

            with open(plugin_yaml) as f:
                data = yaml.safe_load(f)

            # Basic validation
            required_fields = [
                "name",
                "version",
                "description",
                "plugin_type",
                "provider_name",
            ]
            missing_fields = [field for field in required_fields if field not in data]

            if missing_fields:
                logger.warning(
                    f"Invalid plugin.yaml in {plugin_dir}: missing fields: {missing_fields}"
                )
                return None

            # Create plugin info
            plugin_info = PluginInfo(
                name=data["name"],
                version=data["version"],
                description=data["description"],
                plugin_type=data["plugin_type"],
                provider_type=data["provider_name"],
                author=data.get("author", ""),
                email=data.get("email", ""),
                license=data.get("license", ""),
                source=PluginSource.FILE,
                path=plugin_dir,
                module=data.get("entry_point", "provider").split(".")[0],
                class_name=data.get("entry_point", "provider").split(".")[-1],
            )

            return plugin_info

        except Exception as e:
            logger.error(f"Error loading plugin.yaml from {plugin_dir}: {e}")
            return None

    async def _find_plugin_class(
        self, plugin_dir: str, plugin_info: PluginInfo
    ) -> type:
        """Find the plugin class automatically.

        This method searches for a class that inherits from the expected base class
        according to the plugin type.

        Args:
            plugin_dir: Plugin directory
            plugin_info: Plugin information

        Returns:
            The plugin class

        Raises:
            DiscoveryError: If plugin class cannot be found
        """
        # Add plugin directory to path temporarily
        if plugin_dir not in sys.path:
            sys.path.insert(0, plugin_dir)

        try:
            # First try common module names
            possible_modules = [
                "provider",
                "workflow",
                plugin_info.provider_type.lower(),
            ]

            # If entry_point is specified, use that module first
            entry_point = plugin_info.module
            if entry_point and entry_point not in possible_modules:
                possible_modules.insert(0, entry_point)

            # Attempt to import each possible module
            for module_name in possible_modules:
                try:
                    module = importlib.import_module(module_name)

                    # Look for classes with __pepperpy_plugin__ attribute first
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)

                        # Check if it's a class with plugin metadata
                        if not inspect.isclass(attr):
                            continue

                        # Check if class has plugin metadata
                        if hasattr(attr, "__pepperpy_plugin__"):
                            plugin_meta = attr.__pepperpy_plugin__
                            # Check if plugin type matches
                            if plugin_meta.get("type") == plugin_info.plugin_type:
                                return attr

                    # If no decorated class found, look for matching class names
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)

                        # Check if it's a class and matches the provider type
                        if not inspect.isclass(attr):
                            continue

                        # Match by class name pattern
                        if (
                            plugin_info.provider_type in attr_name
                            or plugin_info.plugin_type.capitalize() in attr_name
                            or "Provider" in attr_name
                        ):
                            # Additional validation could be done here
                            # For example, check if it inherits from proper base class

                            return attr

                except ImportError:
                    # This module doesn't exist, try the next one
                    continue
                except Exception as e:
                    logger.warning(f"Error examining module {module_name}: {e}")
                    continue

            # If we reach here, we couldn't find a suitable class
            # Try scanning all Python files
            for root, _, files in os.walk(plugin_dir):
                for file in files:
                    if not file.endswith(".py"):
                        continue

                    try:
                        file_path = os.path.join(root, file)
                        module_name = os.path.splitext(os.path.basename(file))[0]

                        # Skip __init__.py
                        if module_name == "__init__":
                            continue

                        # Try to import via spec
                        spec = importlib.util.spec_from_file_location(
                            module_name, file_path
                        )
                        if spec and spec.loader:
                            module = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(module)

                            # Look for classes with __pepperpy_plugin__ attribute first
                            for attr_name in dir(module):
                                attr = getattr(module, attr_name)

                                if not inspect.isclass(attr):
                                    continue

                                # Check if class has plugin metadata
                                if hasattr(attr, "__pepperpy_plugin__"):
                                    plugin_meta = attr.__pepperpy_plugin__
                                    # Check if plugin type matches
                                    if (
                                        plugin_meta.get("type")
                                        == plugin_info.plugin_type
                                    ):
                                        return attr

                            # If no decorated class found, look for matching class names
                            for attr_name in dir(module):
                                attr = getattr(module, attr_name)

                                if not inspect.isclass(attr):
                                    continue

                                # Match by class name pattern
                                if (
                                    plugin_info.provider_type in attr_name
                                    or plugin_info.plugin_type.capitalize() in attr_name
                                    or "Provider" in attr_name
                                    or "Workflow" in attr_name
                                ):
                                    return attr
                    except Exception as e:
                        logger.warning(f"Error examining file {file_path}: {e}")
                        continue

            # If no class found, fallback to default name based on provider_type
            provider_class_name = f"{plugin_info.provider_type.capitalize()}Provider"
            if plugin_info.plugin_type == "workflow":
                provider_class_name = (
                    f"{plugin_info.provider_type.capitalize()}Workflow"
                )

            # Try various modules with this class name
            for module_name in possible_modules:
                try:
                    module = importlib.import_module(module_name)
                    if hasattr(module, provider_class_name):
                        return getattr(module, provider_class_name)
                except (ImportError, AttributeError):
                    pass

            raise DiscoveryError(
                f"Cannot find provider class for plugin {plugin_info.name}"
            )

        finally:
            # Remove plugin directory from path
            if plugin_dir in sys.path:
                sys.path.remove(plugin_dir)

    async def load_plugin(self, plugin_info: PluginInfo) -> Any:
        """Load a plugin from its information.

        Args:
            plugin_info: Plugin information

        Returns:
            Loaded plugin class

        Raises:
            DiscoveryError: If the plugin cannot be loaded
        """
        if plugin_info.source != PluginSource.FILE:
            raise DiscoveryError(
                f"Cannot load plugin with source {plugin_info.source} using FileSystemDiscovery"
            )

        try:
            # Add plugin path to Python path temporarily
            if plugin_info.path and plugin_info.path not in sys.path:
                sys.path.insert(0, plugin_info.path)

            try:
                # First check if class is already loaded
                if plugin_info.is_loaded():
                    return plugin_info.get_class()

                # Import the module
                module_name = plugin_info.module or "provider"
                class_name = plugin_info.class_name or "Provider"

                try:
                    # Try normal import first
                    module = importlib.import_module(module_name)

                    # Try to get the class
                    if hasattr(module, class_name):
                        plugin_class = getattr(module, class_name)
                    # If class not found in module, try auto-discovery
                    elif plugin_info.path:
                        plugin_class = await self._find_plugin_class(
                            plugin_info.path, plugin_info
                        )
                    else:
                        raise DiscoveryError(
                            f"No path specified for plugin {plugin_info.name}"
                        )

                except ImportError:
                    try:
                        # Try with parent directory as the package
                        parent_dir = os.path.basename(
                            os.path.dirname(plugin_info.path or "")
                        )
                        module = importlib.import_module(f"{parent_dir}.{module_name}")

                        # Try to get the class
                        if hasattr(module, class_name):
                            plugin_class = getattr(module, class_name)
                        # If class not found in module, try auto-discovery
                        elif plugin_info.path:
                            plugin_class = await self._find_plugin_class(
                                plugin_info.path, plugin_info
                            )
                        else:
                            raise DiscoveryError(
                                f"No path specified for plugin {plugin_info.name}"
                            )
                    except ImportError:
                        # If still failing, try auto-discovery
                        if plugin_info.path:
                            plugin_class = await self._find_plugin_class(
                                plugin_info.path, plugin_info
                            )
                        else:
                            raise DiscoveryError(
                                f"No path specified for plugin {plugin_info.name}"
                            )

                # Set the class in plugin info
                plugin_info._plugin_class = plugin_class
                plugin_info._loaded = True

                return plugin_class

            finally:
                # Remove from path
                if plugin_info.path and plugin_info.path in sys.path:
                    sys.path.remove(plugin_info.path)

        except (ImportError, AttributeError) as e:
            raise DiscoveryError(f"Failed to load plugin {plugin_info.name}: {e}")


class PackageDiscovery:
    """Discovers plugins from installed Python packages."""

    async def discover_plugins(self) -> list[PluginInfo]:
        """Discover plugins from installed packages.

        Returns:
            List of discovered plugin information
        """
        results = []

        # Look for entry points in group 'pepperpy.plugins'
        try:
            import importlib.metadata

            entry_points = importlib.metadata.entry_points()

            # Handle different versions of importlib.metadata
            if hasattr(entry_points, "select"):
                # Python 3.10+
                plugin_entries = entry_points.select(group="pepperpy.plugins")
            elif hasattr(entry_points, "get"):
                # Python < 3.10
                plugin_entries = entry_points.get("pepperpy.plugins", [])
            else:
                logger.warning(
                    "Cannot discover plugins from entry points: unsupported importlib.metadata"
                )
                return []

            for entry_point in plugin_entries:
                try:
                    # Load the entry point
                    plugin_info = await self._load_entry_point(entry_point)
                    if plugin_info:
                        results.append(plugin_info)
                except Exception as e:
                    logger.error(f"Error loading entry point {entry_point.name}: {e}")

        except (ImportError, AttributeError) as e:
            logger.warning(f"Cannot discover plugins from entry points: {e}")

        return results

    async def _load_entry_point(self, entry_point: Any) -> PluginInfo | None:
        """Load plugin information from an entry point.

        Args:
            entry_point: Entry point

        Returns:
            Plugin information or None if not valid
        """
        try:
            # Load the entry point
            plugin_class = entry_point.load()

            # Extract plugin info from the class
            if not hasattr(plugin_class, "plugin_info"):
                logger.warning(
                    f"Entry point {entry_point.name} does not define plugin_info"
                )
                return None

            info = plugin_class.plugin_info

            # Create plugin info
            plugin_info = PluginInfo(
                name=info.get("name", entry_point.name),
                version=info.get("version", "0.1.0"),
                description=info.get("description", ""),
                plugin_type=info.get("plugin_type", "unknown"),
                provider_type=info.get("provider_type", entry_point.name),
                author=info.get("author", ""),
                email=info.get("email", ""),
                license=info.get("license", ""),
                source=PluginSource.ENTRY_POINT,
                entry_point=entry_point.name,
                module=entry_point.value.split(":")[0],
                class_name=entry_point.value.split(":")[-1],
            )

            # Set the class
            plugin_info._plugin_class = plugin_class
            plugin_info._loaded = True

            return plugin_info

        except Exception as e:
            logger.error(f"Error loading entry point {entry_point.name}: {e}")
            return None

    async def load_plugin(self, plugin_info: PluginInfo) -> Any:
        """Load a plugin from its information.

        Args:
            plugin_info: Plugin information

        Returns:
            Loaded plugin class

        Raises:
            DiscoveryError: If the plugin cannot be loaded
        """
        if plugin_info.source != PluginSource.ENTRY_POINT:
            raise DiscoveryError(
                f"Cannot load plugin with source {plugin_info.source} using PackageDiscovery"
            )

        if plugin_info.is_loaded():
            return plugin_info.get_class()

        try:
            import importlib.metadata

            # Get entry points
            entry_points = importlib.metadata.entry_points()

            # Handle different versions
            if hasattr(entry_points, "select"):
                # Python 3.10+
                plugin_entries = entry_points.select(group="pepperpy.plugins")
            elif hasattr(entry_points, "get"):
                # Python < 3.10
                plugin_entries = entry_points.get("pepperpy.plugins", [])
            else:
                raise DiscoveryError("Unsupported importlib.metadata")

            # Find the entry point
            entry_point = None
            for ep in plugin_entries:
                if ep.name == plugin_info.entry_point:
                    entry_point = ep
                    break

            if not entry_point:
                raise DiscoveryError(
                    f"Entry point not found: {plugin_info.entry_point}"
                )

            # Load the entry point
            plugin_class = entry_point.load()

            # Set the class
            plugin_info._plugin_class = plugin_class
            plugin_info._loaded = True

            return plugin_class

        except Exception as e:
            raise DiscoveryError(f"Failed to load plugin {plugin_info.name}: {e}")


# Create discovery providers
file_system_discovery = FileSystemDiscovery()
package_discovery = PackageDiscovery()


async def discover_plugins() -> list[PluginInfo]:
    """Discover available plugins.

    Returns:
        List of discovered plugin information
    """
    from pepperpy.plugin.registry import register_plugin

    # Discover plugins from filesystem
    fs_plugins = await file_system_discovery.discover_plugins()

    # Discover plugins from packages
    pkg_plugins = await package_discovery.discover_plugins()

    # Combine results
    plugins = fs_plugins + pkg_plugins

    # Register discovered plugins
    for plugin_info in plugins:
        try:
            # Load the plugin class
            if plugin_info.source == PluginSource.FILE:
                plugin_class = await file_system_discovery.load_plugin(plugin_info)
            elif plugin_info.source == PluginSource.ENTRY_POINT:
                plugin_class = await package_discovery.load_plugin(plugin_info)
            else:
                logger.warning(f"Unsupported plugin source: {plugin_info.source}")
                continue

            # Register the plugin
            register_plugin(
                plugin_info.plugin_type,
                plugin_info.provider_type,
                plugin_class,
                plugin_info.metadata,
            )

            logger.info(
                f"Registered plugin: {plugin_info.plugin_type}.{plugin_info.provider_type}"
            )

        except Exception as e:
            logger.error(f"Error registering plugin {plugin_info.name}: {e}")

    return plugins


async def load_plugin(plugin_info: PluginInfo) -> Any:
    """Load a plugin from its information.

    Args:
        plugin_info: Plugin information

    Returns:
        Loaded plugin class

    Raises:
        DiscoveryError: If the plugin cannot be loaded
    """
    if plugin_info.is_loaded():
        return plugin_info.get_class()

    if plugin_info.source == PluginSource.FILE:
        return await file_system_discovery.load_plugin(plugin_info)
    elif plugin_info.source == PluginSource.ENTRY_POINT:
        return await package_discovery.load_plugin(plugin_info)
    else:
        raise DiscoveryError(f"Unsupported plugin source: {plugin_info.source}")


class PluginDiscoveryProvider(PluginDiscoveryProtocol):
    """Default implementation of the PluginDiscoveryProtocol."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize the discovery provider.

        Args:
            config: Provider configuration
        """
        self.config = config or {}

    async def discover_plugins(self) -> list[PluginInfo]:
        """Discover available plugins.

        Returns:
            List of discovered plugin information
        """
        return await discover_plugins()

    async def load_plugin(self, plugin_info: PluginInfo) -> Any:
        """Load a plugin from its information.

        Args:
            plugin_info: Plugin information

        Returns:
            Loaded plugin class
        """
        return await load_plugin(plugin_info)

    async def cleanup(self) -> None:
        """Clean up any resources."""
        # Currently no resources to clean up
        pass
