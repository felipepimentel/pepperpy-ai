"""
Lazy plugin discovery for PepperPy.

This module provides an optimized plugin discovery mechanism using lazy loading
to improve startup time and reduce memory usage.
"""

import importlib.metadata
import importlib.util
import inspect
import os
import sys
from collections import defaultdict
from functools import lru_cache
from typing import Any

import yaml

from pepperpy.core.decorators import with_timing
from pepperpy.core.logging import get_logger
from pepperpy.plugin.base import PepperpyPlugin, PluginDiscoveryProtocol, PluginInfo
from pepperpy.plugin.registry import register_plugin_info

logger = get_logger(__name__)


class LazyDiscoveryError(Exception):
    """Error during lazy plugin discovery."""


@lru_cache(maxsize=128)
def get_default_plugin_directories() -> list[str]:
    """Get default plugin directories.

    Returns:
        List of default plugin directories
    """
    directories = []

    # Current working directory plugins
    cwd_plugins = os.path.join(os.getcwd(), "plugins")
    if os.path.exists(cwd_plugins) and os.path.isdir(cwd_plugins):
        directories.append(cwd_plugins)

    # User plugins directory
    user_plugins = os.path.expanduser("~/.pepperpy/plugins")
    if os.path.exists(user_plugins) and os.path.isdir(user_plugins):
        directories.append(user_plugins)

    # System plugins directory
    if sys.platform == "win32":
        system_plugins = os.path.join(
            os.environ.get("ProgramFiles", "C:\\Program Files"), "PepperPy", "plugins"
        )
    else:
        system_plugins = "/usr/local/share/pepperpy/plugins"

    if os.path.exists(system_plugins) and os.path.isdir(system_plugins):
        directories.append(system_plugins)

    return directories


class LazyPluginInfo(PluginInfo):
    """Extended plugin information with lazy loading capabilities."""

    def __init__(
        self,
        name: str,
        version: str,
        description: str,
        plugin_type: str,
        provider_name: str,
        class_name: str | None = None,
        module_name: str | None = None,
        module_path: str | None = None,
        config: dict[str, Any] | None = None,
        entry_point: str | None = None,
        dependencies: list[dict[str, Any]] | None = None,
    ) -> None:
        """Initialize lazy plugin information.

        Args:
            name: Plugin name
            version: Plugin version
            description: Plugin description
            plugin_type: Plugin type (llm, tts, etc.)
            provider_name: Provider name
            class_name: Class name (optional)
            module_name: Module name (optional)
            module_path: Module path (optional)
            config: Plugin configuration (optional)
            entry_point: Entry point (optional)
            dependencies: Plugin dependencies (optional)
        """
        super().__init__(
            name=name,
            version=version,
            description=description,
            plugin_type=plugin_type,
            provider_name=provider_name,
            class_name=class_name,
            module_name=module_name,
            module_path=module_path,
            config=config or {},
        )
        self.entry_point = entry_point
        self.dependencies = dependencies or []
        self._loaded_class: type | None = None

    @property
    def loaded(self) -> bool:
        """Check if plugin class is loaded.

        Returns:
            True if loaded, False otherwise
        """
        return self._loaded_class is not None

    @property
    def plugin_class(self) -> type | None:
        """Get loaded plugin class.

        Returns:
            Plugin class or None if not loaded
        """
        return self._loaded_class

    @plugin_class.setter
    def plugin_class(self, value: type) -> None:
        """Set loaded plugin class.

        Args:
            value: Plugin class
        """
        self._loaded_class = value


class LazyFileSystemDiscovery(PluginDiscoveryProtocol):
    """Discovery provider for plugins in the filesystem with lazy loading."""

    def __init__(
        self, plugin_directories: list[str] | None = None, scan_depth: int = 3
    ) -> None:
        """Initialize lazy file system discovery.

        Args:
            plugin_directories: List of directories to scan for plugins
            scan_depth: Maximum directory recursion depth
        """
        self._dirs: set[str] = set()
        self._scan_depth = scan_depth
        self._plugins: dict[str, dict[str, LazyPluginInfo]] = defaultdict(dict)
        self._scanned = False

        if plugin_directories:
            for directory in plugin_directories:
                self.add_directory(directory)
        else:
            # Add default directories
            for directory in get_default_plugin_directories():
                self.add_directory(directory)

    def add_directory(self, directory: str) -> None:
        """Add a directory to scan for plugins.

        Args:
            directory: Directory path
        """
        self._dirs.add(str(directory))
        # Reset scan flag when adding new directories
        self._scanned = False

    @with_timing(log_level="info")
    async def discover_plugins(self) -> dict[str, dict[str, LazyPluginInfo]]:
        """Discover plugins but only scan for metadata without loading classes.

        Returns:
            Dict of plugins by domain
        """
        # Only scan if we haven't scanned before
        if not self._scanned:
            for directory in self._dirs:
                self._scan_directory(directory)
            self._scanned = True

        # Register plugin info with registry for lazy loading
        for domain, plugins in self._plugins.items():
            for name, plugin_info in plugins.items():
                register_plugin_info(domain, name, plugin_info)

        return self._plugins

    async def load_plugin(self, plugin_info: LazyPluginInfo) -> Any:
        """Load a plugin class from its information.

        Args:
            plugin_info: Plugin information

        Returns:
            Loaded plugin class

        Raises:
            LazyDiscoveryError: If plugin cannot be loaded
        """
        # If already loaded, return the class
        if plugin_info.loaded:
            return plugin_info.plugin_class

        # If not loaded, load it now
        try:
            logger.debug(f"Lazy loading plugin {plugin_info.name}")

            # Handle different loading mechanisms
            if plugin_info.module_path and plugin_info.module_name:
                # Load from file
                plugin_class = self._load_from_file(plugin_info)
            elif plugin_info.entry_point:
                # Load from entry point
                plugin_class = self._load_from_entry_point(plugin_info)
            else:
                raise LazyDiscoveryError(
                    f"No loading mechanism for plugin {plugin_info.name}"
                )

            # Store loaded class in plugin info
            plugin_info.plugin_class = plugin_class

            return plugin_class

        except Exception as e:
            logger.exception(f"Error loading plugin {plugin_info.name}: {e}")
            raise LazyDiscoveryError(
                f"Error loading plugin {plugin_info.name}: {e}"
            ) from e

    def _load_from_file(self, plugin_info: LazyPluginInfo) -> type:
        """Load a plugin class from a file.

        Args:
            plugin_info: Plugin information

        Returns:
            Loaded plugin class

        Raises:
            LazyDiscoveryError: If plugin cannot be loaded
        """
        try:
            # Import the module
            if not plugin_info.module_name or not plugin_info.module_path:
                raise LazyDiscoveryError(
                    f"Missing module name or path for plugin {plugin_info.name}"
                )

            spec = importlib.util.spec_from_file_location(
                plugin_info.module_name, plugin_info.module_path
            )

            if not spec or not spec.loader:
                raise LazyDiscoveryError(
                    f"Cannot load module spec for {plugin_info.module_path}"
                )

            module = importlib.util.module_from_spec(spec)
            sys.modules[plugin_info.module_name] = module
            spec.loader.exec_module(module)

            # If class name is specified, use it
            if plugin_info.class_name:
                if not hasattr(module, plugin_info.class_name):
                    raise LazyDiscoveryError(
                        f"Module {plugin_info.module_name} has no class {plugin_info.class_name}"
                    )

                plugin_class = getattr(module, plugin_info.class_name)
                return plugin_class

            # Otherwise, find plugin class from expected interfaces
            plugin_class = self._find_plugin_class(
                module, plugin_info.plugin_type, plugin_info.provider_name, plugin_info
            )

            if not plugin_class:
                raise LazyDiscoveryError(
                    f"Could not find plugin class in {plugin_info.module_path}"
                )

            return plugin_class

        except Exception as e:
            logger.exception(f"Error loading plugin from file: {e}")
            raise LazyDiscoveryError(f"Error loading plugin from file: {e}") from e

    def _load_from_entry_point(self, plugin_info: LazyPluginInfo) -> type:
        """Load a plugin class from an entry point.

        Args:
            plugin_info: Plugin information

        Returns:
            Loaded plugin class

        Raises:
            LazyDiscoveryError: If plugin cannot be loaded
        """
        try:
            if not plugin_info.entry_point:
                raise LazyDiscoveryError("No entry point specified")

            # Parse entry point
            if ":" in plugin_info.entry_point:
                module_path, class_name = plugin_info.entry_point.split(":", 1)
            else:
                module_path = plugin_info.entry_point
                class_name = None

            # Import module
            module = importlib.import_module(module_path)

            # If class name is specified, use it
            if class_name:
                if not hasattr(module, class_name):
                    raise LazyDiscoveryError(
                        f"Module {module_path} has no class {class_name}"
                    )

                plugin_class = getattr(module, class_name)
                return plugin_class

            # Otherwise, find plugin class from expected interfaces
            plugin_class = self._find_plugin_class(
                module, plugin_info.plugin_type, plugin_info.provider_name, plugin_info
            )

            if not plugin_class:
                raise LazyDiscoveryError(
                    f"Could not find plugin class in {module_path}"
                )

            return plugin_class

        except Exception as e:
            logger.exception(f"Error loading plugin from entry point: {e}")
            raise LazyDiscoveryError(
                f"Error loading plugin from entry point: {e}"
            ) from e

    def _scan_directory(
        self, directory: str, current_depth: int = 0, max_depth: int | None = None
    ) -> None:
        """Scan a directory for plugins.

        Args:
            directory: Directory path
            current_depth: Current recursion depth
            max_depth: Maximum recursion depth
        """
        if max_depth is None:
            max_depth = self._scan_depth

        if current_depth > max_depth:
            return

        if not os.path.exists(directory) or not os.path.isdir(directory):
            logger.warning(
                f"Directory does not exist or is not a directory: {directory}"
            )
            return

        try:
            # Check for plugin.yaml files directly
            plugin_yaml = os.path.join(directory, "plugin.yaml")
            if os.path.exists(plugin_yaml):
                plugin_info = self._load_plugin_info(plugin_yaml, directory)
                if plugin_info:
                    domain = plugin_info.plugin_type
                    plugin_key = (
                        f"{plugin_info.plugin_type}/{plugin_info.provider_name}"
                    )
                    self._plugins[domain][plugin_key] = plugin_info
                    logger.debug(f"Found plugin: {plugin_key}")

                    # For workflow plugins, also register with just the name
                    if domain == "workflow":
                        self._plugins[domain][plugin_info.provider_name] = plugin_info

                # Don't recurse into plugin directories
                return

            # Skip disabled directories
            if os.path.exists(os.path.join(directory, ".disabled")):
                logger.debug(f"Skipping disabled directory: {directory}")
                return

            # Recurse into subdirectories
            for item in os.listdir(directory):
                item_path = os.path.join(directory, item)
                if os.path.isdir(item_path):
                    self._scan_directory(item_path, current_depth + 1, max_depth)

        except Exception as e:
            logger.warning(f"Error scanning directory {directory}: {e}")

    def _load_plugin_info(
        self, yaml_file: str, plugin_dir: str
    ) -> LazyPluginInfo | None:
        """Load plugin information from YAML file.

        Args:
            yaml_file: Path to YAML file
            plugin_dir: Plugin directory

        Returns:
            Plugin information or None if invalid
        """
        try:
            # Load YAML
            with open(yaml_file) as f:
                plugin_data = yaml.safe_load(f)

            # Basic validation
            if not plugin_data:
                logger.warning(f"Empty plugin.yaml: {yaml_file}")
                return None

            # Check required fields
            required_fields = [
                "name",
                "version",
                "description",
                "plugin_type",
                "provider_name",
            ]
            for field in required_fields:
                if field not in plugin_data:
                    logger.warning(f"Missing required field '{field}' in {yaml_file}")
                    return None

            # Get plugin info
            name = plugin_data["name"]
            version = plugin_data["version"]
            description = plugin_data["description"]
            plugin_type = plugin_data["plugin_type"]
            provider_name = plugin_data["provider_name"]

            # Get entry point if specified
            entry_point = plugin_data.get("entry_point")

            # Get module path and name
            module_path = None
            module_name = None

            if entry_point and "." in entry_point:
                # Extract from entry point
                if ":" in entry_point:
                    module_name = entry_point.split(":", 1)[0]
                else:
                    module_name = entry_point

                # Find actual module path
                if "/" in module_name:
                    # Likely a file path like 'provider.py'
                    module_path = os.path.join(plugin_dir, module_name)
                else:
                    # Try to resolve module based on python module
                    try:
                        module_spec = importlib.util.find_spec(module_name)
                        if module_spec and module_spec.origin:
                            module_path = module_spec.origin
                    except (ImportError, AttributeError):
                        # Fall back to looking in the plugin directory
                        if "." in module_name:
                            # Convert dotted path to filename
                            module_file = module_name.replace(".", "/") + ".py"
                            module_path = os.path.join(plugin_dir, module_file)
                        else:
                            # Look for match in plugin dir
                            for ext in [".py", "/__init__.py"]:
                                test_path = os.path.join(plugin_dir, module_name + ext)
                                if os.path.exists(test_path):
                                    module_path = test_path
                                    break

            # If no module path yet, guess from default patterns
            if not module_path:
                # Try to find provider.py or similar
                for potential_file in [
                    "provider.py",
                    "__init__.py",
                    f"{provider_name.lower()}.py",
                ]:
                    potential_path = os.path.join(plugin_dir, potential_file)
                    if os.path.exists(potential_path):
                        module_path = potential_path
                        # Guess module name from directory name
                        parts = os.path.normpath(plugin_dir).split(os.path.sep)
                        # Use plugin_type and provider_name if possible
                        module_name = f"{plugin_type}.{provider_name}"
                        break

            # Extract class name from entry point
            class_name = None
            if entry_point and ":" in entry_point:
                class_name = entry_point.split(":", 1)[1]

            # Get default configuration
            config = plugin_data.get("default_config", {})

            # Get dependencies
            dependencies = plugin_data.get("dependencies", [])

            # Create plugin info
            plugin_info = LazyPluginInfo(
                name=name,
                version=version,
                description=description,
                plugin_type=plugin_type,
                provider_name=provider_name,
                class_name=class_name,
                module_name=module_name,
                module_path=module_path,
                config=config,
                entry_point=entry_point,
                dependencies=dependencies,
            )

            return plugin_info

        except Exception as e:
            logger.warning(f"Error loading plugin info from {yaml_file}: {e}")
            return None

    def _find_plugin_class(
        self,
        module: Any,
        plugin_type: str,
        provider_name: str,
        plugin_info: LazyPluginInfo,
    ) -> type | None:
        """Find plugin class in module.

        Args:
            module: Module to search
            plugin_type: Plugin type
            provider_name: Provider name
            plugin_info: Plugin information

        Returns:
            Plugin class or None if not found
        """
        # Expected provider base class name patterns
        expected_base_names = [
            f"{provider_name.title()}Provider",
            f"{plugin_type.title()}{provider_name.title()}Provider",
            f"{plugin_type.title()}Provider",
            "Provider",
        ]

        # Look through classes in module
        for name, obj in inspect.getmembers(module, inspect.isclass):
            # Skip abstract classes
            if inspect.isabstract(obj):
                continue

            # Skip imported classes not defined in this module
            if obj.__module__ != module.__name__:
                continue

            # Check if class matches expected name patterns
            if name in expected_base_names:
                logger.debug(f"Found provider class {name} in {module.__name__}")
                return obj

            # Check if class is a PepperpyPlugin
            try:
                if isinstance(obj, type) and issubclass(obj, PepperpyPlugin):
                    # Check plugin metadata
                    # Note: We can only check these attributes at instance level,
                    # not at class level, so we check for class attributes or properties
                    plugin_type_attr = getattr(obj, "plugin_type", None)
                    provider_name_attr = getattr(obj, "provider_name", None)

                    if (
                        plugin_type_attr == plugin_type
                        and provider_name_attr == provider_name
                    ):
                        logger.debug(f"Found provider class {name} matching metadata")
                        return obj
            except TypeError:
                # Not a class or other type error
                pass

        logger.warning(
            f"Could not find provider class for {plugin_type}/{provider_name} in {module.__name__}"
        )
        return None


class LazyPackageDiscovery(PluginDiscoveryProtocol):
    """Discovery provider for plugins in installed packages with lazy loading."""

    def __init__(self, entry_point_group: str = "pepperpy.plugins") -> None:
        """Initialize lazy package discovery.

        Args:
            entry_point_group: Entry point group to search
        """
        self.entry_point_group = entry_point_group
        self._plugins: dict[str, dict[str, LazyPluginInfo]] = defaultdict(dict)
        self._scanned = False

    @with_timing(log_level="info")
    async def discover_plugins(self) -> dict[str, dict[str, LazyPluginInfo]]:
        """Discover plugins but only scan for metadata without loading classes.

        Returns:
            Dict of plugins by domain
        """
        # Only scan if we haven't scanned before
        if not self._scanned:
            self._scan_entry_points()
            self._scanned = True

        # Register plugin info with registry for lazy loading
        for domain, plugins in self._plugins.items():
            for name, plugin_info in plugins.items():
                register_plugin_info(domain, name, plugin_info)

        return self._plugins

    async def load_plugin(self, plugin_info: LazyPluginInfo) -> Any:
        """Load a plugin class from its information.

        Args:
            plugin_info: Plugin information

        Returns:
            Loaded plugin class

        Raises:
            LazyDiscoveryError: If plugin cannot be loaded
        """
        # If already loaded, return the class
        if plugin_info.loaded:
            return plugin_info.plugin_class

        # If not loaded, load it now
        try:
            logger.debug(f"Lazy loading plugin {plugin_info.name}")

            # Try to load entry point
            if plugin_info.entry_point:
                # For entry point format 'module.path:ClassName'
                module_path, class_name = plugin_info.entry_point.split(":", 1)

                # Import module
                module = importlib.import_module(module_path)

                # Get class from module
                if not hasattr(module, class_name):
                    raise LazyDiscoveryError(
                        f"Module {module_path} has no class {class_name}"
                    )

                plugin_class = getattr(module, class_name)

                # Store loaded class in plugin info
                plugin_info.plugin_class = plugin_class

                return plugin_class

            # No entry point, cannot load
            raise LazyDiscoveryError(f"No entry point for plugin {plugin_info.name}")

        except Exception as e:
            logger.exception(f"Error loading plugin {plugin_info.name}: {e}")
            raise LazyDiscoveryError(
                f"Error loading plugin {plugin_info.name}: {e}"
            ) from e

    def _scan_entry_points(self) -> None:
        """Scan entry points for plugins."""
        try:
            # Find all entry points in group
            entry_points = []

            # Handle different importlib.metadata versions
            try:
                # Python 3.10+
                entry_points = list(
                    importlib.metadata.entry_points(group=self.entry_point_group)
                )
            except TypeError:
                # Python 3.8-3.9
                all_entries = importlib.metadata.entry_points()
                if hasattr(all_entries, "select"):
                    # Newer importlib.metadata versions
                    entry_points = list(
                        all_entries.select(group=self.entry_point_group)
                    )
                else:
                    # Older versions
                    entry_points = [
                        ep for ep in all_entries if ep.group == self.entry_point_group
                    ]

            # Load entry points
            for entry_point in entry_points:
                try:
                    # Load entry point as plugin info
                    plugin_info = self._load_entry_point(entry_point)
                    if plugin_info:
                        domain = plugin_info.plugin_type
                        plugin_key = (
                            f"{plugin_info.plugin_type}/{plugin_info.provider_name}"
                        )
                        self._plugins[domain][plugin_key] = plugin_info
                        logger.debug(f"Found plugin from entry point: {plugin_key}")

                        # For workflow plugins, also register with just the name
                        if domain == "workflow":
                            self._plugins[domain][plugin_info.provider_name] = (
                                plugin_info
                            )

                except Exception as e:
                    logger.warning(f"Error loading entry point {entry_point.name}: {e}")

        except Exception as e:
            logger.warning(f"Error scanning entry points: {e}")

    def _load_entry_point(self, entry_point: Any) -> LazyPluginInfo | None:
        """Load plugin information from entry point.

        Args:
            entry_point: Entry point object

        Returns:
            Plugin information or None if invalid
        """
        try:
            # Extract metadata from entry point
            name = entry_point.name

            # Try to get metadata without loading
            attrs = {}

            # Try to get module name from entry point
            module_name = None
            try:
                if hasattr(entry_point, "value"):
                    # Python 3.9+
                    module_name = entry_point.value.split(":")[0]
                else:
                    # Python 3.8
                    module_name = entry_point.module_name
            except AttributeError:
                # Fall back to direct access
                module_name = entry_point.module

            if not module_name:
                logger.warning(f"Could not extract module name from entry point {name}")
                return None

            # Try to import just the module to get metadata
            try:
                module = importlib.import_module(module_name)

                # Look for plugin metadata in module
                if hasattr(module, "__plugin_metadata__"):
                    attrs = module.__plugin_metadata__
            except ImportError as e:
                logger.warning(f"Could not import module {module_name}: {e}")

            # Extract plugin type and provider name
            plugin_type = attrs.get("plugin_type")
            provider_name = attrs.get("provider_name")

            # If not in metadata, try to extract from name format
            if not plugin_type or not provider_name:
                # Try format: llm.openai
                if "." in name:
                    parts = name.split(".", 1)
                    plugin_type = plugin_type or parts[0]
                    provider_name = provider_name or parts[1]
                else:
                    # Assume it's just the provider name
                    provider_name = provider_name or name

                    # Try to guess plugin type from entry point name
                    if not plugin_type:
                        if "llm" in name.lower():
                            plugin_type = "llm"
                        elif "tts" in name.lower():
                            plugin_type = "tts"
                        elif "tool" in name.lower():
                            plugin_type = "tool"
                        elif "workflow" in name.lower():
                            plugin_type = "workflow"
                        else:
                            # Default to generic
                            plugin_type = "plugin"

            # Create entry point value as string
            entry_point_value = ""
            if hasattr(entry_point, "value"):
                # Python 3.9+
                entry_point_value = entry_point.value
            else:
                # Python 3.8
                entry_point_value = f"{entry_point.module_name}:{entry_point.attr}"

            # Create plugin info
            plugin_info = LazyPluginInfo(
                name=name,
                version=attrs.get("version", "0.1.0"),
                description=attrs.get("description", f"Plugin {name}"),
                plugin_type=plugin_type,
                provider_name=provider_name,
                entry_point=entry_point_value,
                config=attrs.get("default_config", {}),
                dependencies=attrs.get("dependencies", []),
            )

            return plugin_info

        except Exception as e:
            logger.warning(f"Error creating plugin info from entry point: {e}")
            return None


class LazyPluginDiscoveryProvider(PluginDiscoveryProtocol):
    """Main discovery provider that combines multiple discovery methods with lazy loading."""

    def __init__(
        self, discovery_providers: list[PluginDiscoveryProtocol] | None = None
    ) -> None:
        """Initialize lazy plugin discovery provider.

        Args:
            discovery_providers: List of discovery providers
        """
        self._providers = discovery_providers or []
        self._plugins: dict[str, dict[str, Any]] = defaultdict(dict)

        # Initialize default providers if none provided
        if not self._providers:
            self._init_discovery_providers()

    def _init_discovery_providers(self) -> None:
        """Initialize default discovery providers."""
        # File system discovery
        self._providers.append(LazyFileSystemDiscovery())

        # Package discovery
        self._providers.append(LazyPackageDiscovery())

    @with_timing(log_level="info")
    async def discover_plugins(self) -> dict[str, dict[str, Any]]:
        """Discover plugins using all providers.

        Returns:
            Dict of plugins by domain
        """
        # Clear existing plugins
        self._plugins.clear()

        # Discover plugins from all providers
        for provider in self._providers:
            try:
                provider_plugins = await provider.discover_plugins()

                # Merge plugins
                for domain, plugins in provider_plugins.items():
                    for name, plugin_info in plugins.items():
                        self._plugins[domain][name] = plugin_info

            except Exception as e:
                logger.error(f"Error discovering plugins from provider {provider}: {e}")

        return self._plugins

    async def load_plugin(self, plugin_info: LazyPluginInfo) -> Any:
        """Load a plugin class.

        Args:
            plugin_info: Plugin information

        Returns:
            Loaded plugin class

        Raises:
            LazyDiscoveryError: If plugin cannot be loaded
        """
        # If already loaded, return the class
        if plugin_info.loaded:
            return plugin_info.plugin_class

        # Find provider that can load this plugin
        for provider in self._providers:
            try:
                plugin_class = await provider.load_plugin(plugin_info)
                if plugin_class:
                    # Store loaded class in plugin info
                    plugin_info.plugin_class = plugin_class
                    return plugin_class
            except Exception as e:
                logger.debug(f"Provider {provider} could not load plugin: {e}")

        # No provider could load the plugin
        raise LazyDiscoveryError(f"No provider could load plugin {plugin_info.name}")


def get_lazy_discovery_provider() -> LazyPluginDiscoveryProvider:
    """Get the lazy plugin discovery provider.

    Returns:
        Lazy plugin discovery provider
    """
    return LazyPluginDiscoveryProvider()


async def discover_plugins_lazy() -> dict[str, dict[str, Any]]:
    """Discover plugins using lazy loading.

    Returns:
        Dict of plugins by domain
    """
    provider = get_lazy_discovery_provider()
    return await provider.discover_plugins()


async def load_plugin_lazy(plugin_info: LazyPluginInfo) -> Any:
    """Load a plugin class.

    Args:
        plugin_info: Plugin information

    Returns:
        Loaded plugin class

    Raises:
        LazyDiscoveryError: If plugin cannot be loaded
    """
    provider = get_lazy_discovery_provider()
    return await provider.load_plugin(plugin_info)
