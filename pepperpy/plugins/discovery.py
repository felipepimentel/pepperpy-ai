"""Enhanced plugin discovery system for PepperPy.

This module provides an advanced plugin discovery system that can:
1. Detect plugins in installed Python packages
2. Use entry points for automatic plugin registration
3. Scan for plugins based on naming conventions
4. Handle dependencies between plugins
"""

import importlib
import importlib.metadata
import importlib.util
import inspect
import os
import pkgutil
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Type, TypeVar, cast

from pepperpy.core.logging import get_logger
from pepperpy.plugins.plugin import PepperpyPlugin

logger = get_logger(__name__)

# Type for plugin classes
T = TypeVar("T", bound=PepperpyPlugin)


class PluginSource(Enum):
    """Source of plugin discovery."""

    FILE = "file"  # From filesystem
    PACKAGE = "package"  # From installed package
    ENTRY_POINT = "entry_point"  # From package entry point
    REGISTRY = "registry"  # From plugin registry
    DYNAMIC = "dynamic"  # Dynamically registered


@dataclass
class PluginDependency:
    """Dependency information for a plugin."""

    plugin_type: str
    provider_type: str
    required: bool = True
    version_constraint: Optional[str] = None


@dataclass
class PluginInfo:
    """Enhanced information about a plugin."""

    name: str
    version: str
    description: str
    plugin_type: str
    provider_type: str

    # Plugin metadata
    author: str = ""
    email: str = ""
    license: str = ""

    # Source information
    source: PluginSource = PluginSource.FILE
    path: Optional[str] = None
    module: Optional[str] = None
    class_name: Optional[str] = None
    entry_point: Optional[str] = None

    # Dependencies
    dependencies: List[PluginDependency] = field(default_factory=list)
    python_dependencies: List[str] = field(default_factory=list)
    system_dependencies: List[str] = field(default_factory=list)

    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Lazy loading
    _loaded: bool = False
    _plugin_class: Optional[Type[PepperpyPlugin]] = None

    def is_loaded(self) -> bool:
        """Check if the plugin class is loaded."""
        return self._loaded

    def get_class(self) -> Optional[Type[PepperpyPlugin]]:
        """Get the plugin class (loads it if not already loaded)."""
        if not self._loaded and self._plugin_class is None:
            self._plugin_class = load_plugin_class(self)
            self._loaded = self._plugin_class is not None
        return self._plugin_class


class PluginDiscoveryError(Exception):
    """Error raised during plugin discovery."""

    pass


class PluginDiscoveryManager:
    """Manager for plugin discovery and registration."""

    def __init__(self):
        """Initialize the plugin discovery manager."""
        self._plugins: Dict[str, Dict[str, PluginInfo]] = {}
        self._entry_point_group = "pepperpy.plugins"
        self._discovered = False
        self._scan_paths: Set[str] = set()
        self._package_scan_paths: Set[str] = set()
        self._autodiscovery_enabled = True
        self.plugins_by_module: Dict[str, List[str]] = {}
        self.search_modules: List[str] = []
        self.discover_entry_points = True

    def register_plugin(
        self,
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
        if plugin_type not in self._plugins:
            self._plugins[plugin_type] = {}

        # Get plugin metadata from class docstring or annotations
        meta = extract_plugin_metadata(plugin_class)
        if metadata:
            meta.update(metadata)

        # Create plugin info
        info = PluginInfo(
            name=meta.get("name", provider_type),
            version=meta.get("version", "0.1.0"),
            description=meta.get("description", plugin_class.__doc__ or ""),
            plugin_type=plugin_type,
            provider_type=provider_type,
            author=meta.get("author", ""),
            source=PluginSource.DYNAMIC,
            metadata=meta,
            _loaded=True,
            _plugin_class=plugin_class,
        )

        self._plugins[plugin_type][provider_type] = info
        logger.debug(f"Registered plugin: {plugin_type}/{provider_type}")

    def get_plugin(
        self, plugin_type: str, provider_type: str
    ) -> Optional[Type[PepperpyPlugin]]:
        """Get a plugin by type and provider.

        Args:
            plugin_type: Type of plugin
            provider_type: Type of provider

        Returns:
            Plugin class or None if not found
        """
        # Auto-discover if enabled and not yet discovered
        if self._autodiscovery_enabled and not self._discovered:
            self.discover_plugins()

        # Get plugin info
        info = self._plugins.get(plugin_type, {}).get(provider_type)
        if info is None:
            return None

        # Get plugin class (triggers lazy loading if needed)
        return info.get_class()

    def get_plugin_metadata(
        self, plugin_type: str, provider_type: str
    ) -> Optional[Dict[str, Any]]:
        """Get plugin metadata.

        Args:
            plugin_type: Type of plugin
            provider_type: Type of provider

        Returns:
            Plugin metadata or None if not found
        """
        info = self._plugins.get(plugin_type, {}).get(provider_type)
        if info is None:
            return None
        return info.metadata

    def register_scan_path(self, path: str) -> None:
        """Register a filesystem path to scan for plugins.

        Args:
            path: Path to scan for plugins
        """
        if not os.path.isdir(path):
            logger.warning(f"Plugin scan path does not exist: {path}")
            return

        self._scan_paths.add(os.path.abspath(path))
        logger.debug(f"Added plugin scan path: {path}")

        # Invalidate discovery status
        self._discovered = False

    def register_package_path(self, package: str) -> None:
        """Register a Python package to scan for plugins.

        Args:
            package: Package name to scan
        """
        self._package_scan_paths.add(package)
        logger.debug(f"Added plugin package scan path: {package}")

        # Invalidate discovery status
        self._discovered = False

    def set_autodiscovery(self, enabled: bool) -> None:
        """Enable or disable plugin autodiscovery.

        Args:
            enabled: Whether autodiscovery is enabled
        """
        self._autodiscovery_enabled = enabled
        logger.debug(f"Plugin autodiscovery {'enabled' if enabled else 'disabled'}")

    def get_plugins_by_type(self, plugin_type: str) -> Dict[str, Type[PepperpyPlugin]]:
        """Get all plugins of a specific type.

        Args:
            plugin_type: Type of plugin

        Returns:
            Dictionary of provider names to plugin classes
        """
        # Auto-discover if enabled and not yet discovered
        if self._autodiscovery_enabled and not self._discovered:
            self.discover_plugins()

        result: Dict[str, Type[PepperpyPlugin]] = {}
        for provider_type, info in self._plugins.get(plugin_type, {}).items():
            plugin_class = info.get_class()
            if plugin_class is not None:
                result[provider_type] = plugin_class

        return result

    def list_plugins(self) -> Dict[str, Dict[str, PluginInfo]]:
        """List all registered plugins.

        Returns:
            Dictionary of plugin types to dictionaries of provider types to plugin info
        """
        # Auto-discover if enabled and not yet discovered
        if self._autodiscovery_enabled and not self._discovered:
            self.discover_plugins()

        return self._plugins

    def list_plugin_types(self) -> List[str]:
        """List all registered plugin types.

        Returns:
            List of plugin types
        """
        # Auto-discover if enabled and not yet discovered
        if self._autodiscovery_enabled and not self._discovered:
            self.discover_plugins()

        return list(self._plugins.keys())

    def discover_plugins(self) -> Dict[str, Dict[str, PluginInfo]]:
        """Discover plugins from all sources.

        Returns:
            Dictionary of plugin types to dictionaries of provider types to plugin info
        """
        logger.debug("Discovering plugins...")

        # Discover plugins from entry points
        self._discover_from_entry_points()

        # Discover plugins from scan paths
        for path in self._scan_paths:
            self._discover_from_path(path)

        # Discover plugins from package paths
        for package in self._package_scan_paths:
            self._discover_from_package(package)

        self._discovered = True
        logger.debug(
            f"Discovered {sum(len(providers) for providers in self._plugins.values())} plugins"
        )

        return self._plugins

    def _discover_from_entry_points(self) -> None:
        """Discover plugins from package entry points."""
        try:
            # Use importlib.metadata to get entry points
            try:
                from importlib import metadata
            except ImportError:
                # Fallback for Python < 3.8
                import importlib_metadata as metadata

            # Get entry points for pepperpy.plugins group
            try:
                entry_points = metadata.entry_points()
                plugin_points = []

                # Handle different entry_points() return type in Python 3.10+
                if hasattr(entry_points, "select"):
                    # Python 3.10+: use select method
                    plugin_points = list(entry_points.select(group="pepperpy.plugins"))
                elif isinstance(entry_points, dict):
                    # Python 3.8-3.9 (dict-like): access by key
                    plugin_points = list(entry_points.get("pepperpy.plugins", []))
                else:
                    # Fallback: filter entry_points manually
                    plugin_points = [
                        ep for ep in entry_points if ep.group == "pepperpy.plugins"
                    ]

                # Load each entry point
                for entry_point in plugin_points:
                    try:
                        plugin_class = entry_point.load()

                        # Skip if not a PepperpyPlugin subclass
                        if not issubclass(plugin_class, PepperpyPlugin):
                            logger.warning(
                                f"Entry point {entry_point.name} is not a PepperpyPlugin subclass: {plugin_class.__name__}"
                            )
                            continue

                        # Register plugin
                        self.register_plugin(
                            plugin_type=entry_point.name.split(".")[0],
                            provider_type=entry_point.name.split(".")[1],
                            plugin_class=plugin_class,
                        )
                        self._plugins[entry_point.name.split(".")[0]][
                            entry_point.name.split(".")[1]
                        ].source = PluginSource.ENTRY_POINT
                        self._plugins[entry_point.name.split(".")[0]][
                            entry_point.name.split(".")[1]
                        ].entry_point = entry_point.name

                        logger.debug(
                            f"Discovered plugin from entry point: {entry_point.name}"
                        )
                    except Exception as e:
                        logger.error(
                            f"Error loading entry point {entry_point.name}: {e}"
                        )
            except Exception as e:
                logger.error(f"Error accessing entry points: {e}")
        except ImportError:
            logger.warning(
                "importlib.metadata not available, skipping entry point discovery"
            )

    def _discover_from_path(self, path: str) -> None:
        """Discover plugins from a filesystem path.

        Args:
            path: Path to scan for plugins
        """
        # Skip if path doesn't exist
        if not os.path.isdir(path):
            return

        # Look for plugin.yaml files
        for root, _, files in os.walk(path):
            for file in files:
                if file == "plugin.yaml" or file == "plugin.yml":
                    plugin_file = os.path.join(root, file)
                    try:
                        self._load_plugin_yaml(plugin_file)
                    except Exception as e:
                        logger.warning(f"Error loading plugin from {plugin_file}: {e}")

        # Look for Python modules with plugin_type and provider_type attributes
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith(".py") and file != "__init__.py":
                    module_path = os.path.join(root, file)
                    try:
                        self._load_plugin_module(module_path)
                    except Exception:
                        # This is expected for many Python files that aren't plugins
                        pass

    def _discover_from_package(self, package_name: str) -> None:
        """Discover plugins from a Python package.

        Args:
            package_name: Package name to scan
        """
        try:
            # Get package spec
            package_spec = importlib.util.find_spec(package_name)
            if package_spec is None or package_spec.submodule_search_locations is None:
                logger.warning(f"Package not found: {package_name}")
                return

            # Scan all modules in package
            for finder, name, is_pkg in pkgutil.iter_modules(
                package_spec.submodule_search_locations
            ):
                if is_pkg:
                    # Recursively scan subpackages
                    self._discover_from_package(f"{package_name}.{name}")
                else:
                    # Check if module is a plugin
                    try:
                        module_name = f"{package_name}.{name}"
                        self._load_plugin_package_module(module_name)
                    except Exception:
                        # This is expected for many modules that aren't plugins
                        pass

        except Exception as e:
            logger.warning(
                f"Error discovering plugins from package {package_name}: {e}"
            )

    def _load_plugin_yaml(self, yaml_path: str) -> None:
        """Load plugin from YAML file.

        Args:
            yaml_path: Path to plugin.yaml file
        """
        import yaml

        # Read YAML file
        with open(yaml_path) as f:
            plugin_data = yaml.safe_load(f)

        # Get plugin type and provider type
        plugin_type = plugin_data.get("plugin_type")
        provider_type = plugin_data.get("provider_type")

        # Skip if required fields are missing
        if not plugin_type or not provider_type:
            logger.warning(f"Missing plugin_type or provider_type in {yaml_path}")
            return

        # Create plugin info
        info = PluginInfo(
            name=plugin_data.get("name", provider_type),
            version=plugin_data.get("version", "0.1.0"),
            description=plugin_data.get("description", ""),
            plugin_type=plugin_type,
            provider_type=provider_type,
            author=plugin_data.get("author", ""),
            email=plugin_data.get("email", ""),
            license=plugin_data.get("license", ""),
            source=PluginSource.FILE,
            path=os.path.dirname(yaml_path),
            module=plugin_data.get("module"),
            class_name=plugin_data.get("class"),
            metadata=plugin_data,
        )

        # Parse dependencies
        if "dependencies" in plugin_data:
            for dep in plugin_data["dependencies"]:
                info.dependencies.append(
                    PluginDependency(
                        plugin_type=dep["plugin_type"],
                        provider_type=dep["provider_type"],
                        required=dep.get("required", True),
                        version_constraint=dep.get("version"),
                    )
                )

        # Register plugin
        if plugin_type not in self._plugins:
            self._plugins[plugin_type] = {}

        self._plugins[plugin_type][provider_type] = info
        logger.debug(f"Discovered plugin from YAML: {plugin_type}/{provider_type}")

    def _load_plugin_module(self, module_path: str) -> None:
        """Load plugin from Python module file.

        Args:
            module_path: Path to Python module file
        """
        # Generate module name from path
        module_rel_path = os.path.relpath(module_path)
        module_name = os.path.splitext(module_rel_path.replace(os.path.sep, "."))[0]

        # Import module
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if spec is None or spec.loader is None:
            return

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Check for plugin_type and provider_type attributes
        if not hasattr(module, "plugin_type") or not hasattr(module, "provider_type"):
            return

        plugin_type = module.plugin_type
        provider_type = module.provider_type

        # Look for plugin class (subclass of PepperpyPlugin)
        plugin_class = None
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (
                inspect.isclass(attr)
                and issubclass(attr, PepperpyPlugin)
                and attr is not PepperpyPlugin
            ):
                plugin_class = attr
                break

        if plugin_class is None:
            return

        # Extract metadata
        metadata = extract_plugin_metadata(plugin_class)

        # Create plugin info
        info = PluginInfo(
            name=metadata.get("name", provider_type),
            version=metadata.get("version", "0.1.0"),
            description=metadata.get("description", plugin_class.__doc__ or ""),
            plugin_type=plugin_type,
            provider_type=provider_type,
            author=metadata.get("author", ""),
            source=PluginSource.FILE,
            path=os.path.dirname(module_path),
            module=module_name,
            class_name=plugin_class.__name__,
            metadata=metadata,
            _loaded=True,
            _plugin_class=plugin_class,
        )

        # Register plugin
        if plugin_type not in self._plugins:
            self._plugins[plugin_type] = {}

        self._plugins[plugin_type][provider_type] = info
        logger.debug(f"Discovered plugin from module: {plugin_type}/{provider_type}")

    def _load_plugin_package_module(self, module_name: str) -> None:
        """Load plugin from Python package module.

        Args:
            module_name: Name of module to load
        """
        # Import module
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            return

        # Check for plugin_type and provider_type attributes
        if not hasattr(module, "plugin_type") or not hasattr(module, "provider_type"):
            return

        plugin_type = module.plugin_type
        provider_type = module.provider_type

        # Look for plugin class (subclass of PepperpyPlugin)
        plugin_class = None
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (
                inspect.isclass(attr)
                and issubclass(attr, PepperpyPlugin)
                and attr is not PepperpyPlugin
            ):
                plugin_class = attr
                break

        if plugin_class is None:
            return

        # Extract metadata
        metadata = extract_plugin_metadata(plugin_class)

        # Create plugin info
        info = PluginInfo(
            name=metadata.get("name", provider_type),
            version=metadata.get("version", "0.1.0"),
            description=metadata.get("description", plugin_class.__doc__ or ""),
            plugin_type=plugin_type,
            provider_type=provider_type,
            author=metadata.get("author", ""),
            source=PluginSource.PACKAGE,
            module=module_name,
            class_name=plugin_class.__name__,
            metadata=metadata,
            _loaded=True,
            _plugin_class=plugin_class,
        )

        # Register plugin
        if plugin_type not in self._plugins:
            self._plugins[plugin_type] = {}

        self._plugins[plugin_type][provider_type] = info
        logger.debug(f"Discovered plugin from package: {plugin_type}/{provider_type}")


def extract_plugin_metadata(plugin_class: Type[PepperpyPlugin]) -> Dict[str, Any]:
    """Extract metadata from plugin class.

    Extracts metadata from class docstring, __metadata__ attribute, and annotations.

    Args:
        plugin_class: Plugin class

    Returns:
        Plugin metadata
    """
    metadata: Dict[str, Any] = {}

    # Extract from __metadata__ attribute if present
    if hasattr(plugin_class, "__metadata__"):
        metadata.update(plugin_class.__metadata__)

    # Extract from class annotations
    for attr_name, attr_type in plugin_class.__annotations__.items():
        if attr_name.startswith("_"):
            continue
        metadata[attr_name] = attr_type

    # Extract from docstring
    if plugin_class.__doc__:
        metadata["description"] = plugin_class.__doc__.strip()

    return metadata


def load_plugin_class(info: PluginInfo) -> Optional[Type[PepperpyPlugin]]:
    """Load plugin class based on plugin info.

    Args:
        info: Plugin info

    Returns:
        Plugin class or None if it can't be loaded
    """
    # If class is already loaded, return it
    if info._plugin_class is not None:
        return info._plugin_class

    # If module and class name are not provided, can't load
    if not info.module or not info.class_name:
        logger.warning(
            f"Cannot load plugin {info.plugin_type}/{info.provider_type}: missing module or class name"
        )
        return None

    # Load module
    try:
        # If path is provided, load from file
        if info.path:
            spec = importlib.util.spec_from_file_location(
                info.module, os.path.join(info.path, f"{info.module.split('.')[-1]}.py")
            )
            if spec is None or spec.loader is None:
                logger.warning(
                    f"Cannot load plugin module {info.module} from {info.path}"
                )
                return None

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        else:
            # Otherwise, import module
            module = importlib.import_module(info.module)

        # Get class from module
        plugin_class = getattr(module, info.class_name)

        # Check if it's a valid plugin class
        if not inspect.isclass(plugin_class) or not issubclass(
            plugin_class, PepperpyPlugin
        ):
            logger.warning(
                f"Class {info.class_name} in module {info.module} is not a valid PepperpyPlugin subclass"
            )
            return None

        # Store class in plugin info
        info._plugin_class = cast(Type[PepperpyPlugin], plugin_class)
        info._loaded = True

        return info._plugin_class

    except Exception as e:
        logger.warning(
            f"Error loading plugin {info.plugin_type}/{info.provider_type}: {e}"
        )
        return None


# Singleton instance
_plugin_manager = PluginDiscoveryManager()

# Public API
register_plugin = _plugin_manager.register_plugin
register_scan_path = _plugin_manager.register_scan_path
register_package_path = _plugin_manager.register_package_path
set_autodiscovery = _plugin_manager.set_autodiscovery
get_plugin = _plugin_manager.get_plugin
get_plugin_metadata = _plugin_manager.get_plugin_metadata
get_plugins_by_type = _plugin_manager.get_plugins_by_type
list_plugins = _plugin_manager.list_plugins
list_plugin_types = _plugin_manager.list_plugin_types
discover_plugins = _plugin_manager.discover_plugins
