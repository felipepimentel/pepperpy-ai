"""Plugin base classes and utilities.

This module defines the base classes for all PepperPy plugins and provides
utilities for plugin registration, discovery, and management.
"""

import importlib
import importlib.util
import json
import os
import subprocess
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional, Set, Type, TypeVar

import yaml

# Import PepperPy's own logging system instead of third-party loggers
from pepperpy.core import BaseProvider, ConfigError
from pepperpy.core.logging import get_logger

T = TypeVar("T", bound="PepperpyPlugin")


class PepperpyPlugin(ABC):
    """Base class for all PepperPy plugins.

    All plugins must inherit from this class and implement its abstract methods.
    This ensures consistent behavior across all plugins and simplifies
    registration and discovery.
    """

    # Class variables that must be defined by subclasses or in plugin.yaml
    plugin_name: ClassVar[str] = ""
    plugin_version: ClassVar[str] = "0.1.0"
    plugin_description: ClassVar[str] = ""
    plugin_category: ClassVar[str] = ""
    plugin_author: ClassVar[str] = "PepperPy Team"
    required_config_keys: ClassVar[List[str]] = []

    # Auto-assigned logger
    _logger = None

    def __init__(self, **config: Any) -> None:
        """Initialize the plugin with configuration.

        Args:
            **config: Plugin configuration

        Raises:
            ConfigError: If required configuration is missing
        """
        self._config = config
        self._metadata = {}
        self.initialized = False

        # Load metadata from plugin.yaml if available
        self._load_metadata_from_yaml()

        # Auto-inject environment variables based on metadata
        self._inject_env_variables()

    def _load_metadata_from_yaml(self) -> None:
        """Load plugin metadata from plugin.yaml file."""
        try:
            # Get the module path of the concrete plugin class
            module_path = Path(self.__class__.__module__.replace(".", "/"))
            # Try to find plugin.yaml in the parent directory
            plugin_dir = Path(__file__).parent.parent.parent / "plugins"

            # Get plugin name from module path
            parts = module_path.parts
            if "plugins" in parts:
                plugin_idx = parts.index("plugins")
                if len(parts) > plugin_idx + 1:
                    plugin_name = parts[plugin_idx + 1]
                    yaml_path = plugin_dir / plugin_name / "plugin.yaml"

                    if yaml_path.exists():
                        with open(yaml_path) as f:
                            self._metadata = yaml.safe_load(f)
        except Exception:
            # Just log warning and continue - this is not critical
            pass

    @property
    def logger(self):
        """Get the logger for this plugin.

        This is automatically initialized with the plugin's module name.
        """
        if self._logger is None:
            # Get the module name of the concrete class
            self._logger = get_logger(self.__class__.__module__)
        return self._logger

    def _inject_env_variables(self) -> None:
        """Inject environment variables into configuration.

        This automatically loads environment variables for any required_config_keys
        from plugin.yaml that aren't provided in the constructor.
        """
        # Check if we have metadata with required keys
        required_keys = self._metadata.get("required_config_keys", [])
        if not required_keys:
            return

        category = self._metadata.get("category", "").lower()
        provider_type = self._metadata.get("provider_type", "").lower()

        if not category or not provider_type:
            return

        for key in required_keys:
            if key not in self._config or not self._config[key]:
                # Try environment variables in order of specificity
                env_values = [
                    # Most specific: PEPPERPY_{CATEGORY}__{PROVIDER}__{KEY}
                    os.getenv(
                        f"PEPPERPY_{category.upper()}__{provider_type.upper()}__{key.upper()}"
                    ),
                    # Provider specific: {PROVIDER}_{KEY} (e.g., OPENAI_API_KEY)
                    os.getenv(f"{provider_type.upper()}_{key.upper()}"),
                    # General: PEPPERPY_{KEY}
                    os.getenv(f"PEPPERPY_{key.upper()}"),
                ]

                # Use the first non-None value
                for value in env_values:
                    if value is not None:
                        self._config[key] = value
                        break

    def get_metadata(self) -> Dict[str, Any]:
        """Get plugin metadata.

        Returns:
            Dictionary with plugin metadata
        """
        return self._metadata

    @classmethod
    def from_config(cls: Type[T], **config: Any) -> T:
        """Create a plugin instance from configuration.

        Args:
            **config: Plugin configuration

        Returns:
            Plugin instance

        Raises:
            ConfigError: If required configuration is missing
        """
        instance = cls(**config)
        return instance

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value
        """
        return self._config.get(key, default)

    def validate_config(self) -> None:
        """Validate plugin configuration.

        Raises:
            ConfigError: If any required keys are missing
        """
        required_keys = self._metadata.get("required_config_keys", [])
        missing = [key for key in required_keys if key not in self._config]
        if missing:
            raise ConfigError(
                f"Missing required configuration keys: {', '.join(missing)}"
            )

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize plugin resources.

        This method should be called before using the plugin.
        It initializes any resources needed by the plugin.

        Raises:
            ConfigError: If configuration is invalid
            ProviderError: If initialization fails
        """
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up plugin resources.

        This method should be called when the plugin is no longer needed.
        It cleans up any resources allocated by the plugin.

        Raises:
            ProviderError: If cleanup fails
        """
        pass

    async def __aenter__(self) -> "PepperpyPlugin":
        """Enter async context manager.

        Returns:
            Self

        Raises:
            ConfigError: If configuration is invalid
            ProviderError: If initialization fails
        """
        await self.initialize()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context manager.

        Args:
            exc_type: Exception type
            exc_val: Exception value
            exc_tb: Exception traceback

        Raises:
            ProviderError: If cleanup fails
        """
        await self.cleanup()


class ProviderPlugin(BaseProvider):
    """Base class for provider plugins.

    This class serves as a base for all provider plugins, providing common
    functionality such as configuration management, resource initialization,
    and environment variable injection.

    Plugin metadata is loaded automatically from plugin.yaml within the
    plugin directory.
    """

    # Set of automatically created attributes from config
    _auto_attrs: Set[str] = set()

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the plugin with configuration.

        Args:
            **kwargs: Configuration options for the plugin
        """
        super().__init__(**kwargs)

        # Load metadata from plugin.yaml if available
        self._metadata = self._load_metadata()

        # Get logger for this plugin
        plugin_category = self._metadata.get("plugin_category", "unknown")
        provider_type = self._metadata.get("provider_type", "unknown")
        self._logger = get_logger(f"pepperpy.{plugin_category}.{provider_type}")

        # Inject environment variables
        self._inject_env_variables()

        # Auto-bind configuration attributes based on schema
        self._auto_bind_config_attributes()

    def _auto_bind_config_attributes(self) -> None:
        """Automatically bind configuration values from schema to instance attributes.

        This method reads the config_schema from metadata and creates instance attributes
        for each config key, converting values to the appropriate type as specified
        in the schema.
        """
        schema = self._metadata.get("config_schema", {})
        default_config = self._metadata.get("default_config", {})

        # Clear previously auto-bound attributes
        for attr in self._auto_attrs:
            if hasattr(self, attr):
                delattr(self, attr)
        self._auto_attrs.clear()

        # Bind new attributes based on schema
        for key, schema_info in schema.items():
            # Get value with precedence: runtime config > default config > schema default
            value = None
            if key in self._config:
                value = self._config[key]
            elif key in default_config:
                value = default_config[key]
            elif "default" in schema_info:
                value = schema_info["default"]

            # Skip if no value available
            if value is None:
                continue

            # Convert to appropriate type
            attr_type = schema_info.get("type", "string")
            try:
                if attr_type == "float":
                    value = float(value)
                elif attr_type == "integer":
                    value = int(value)
                elif attr_type == "boolean":
                    if isinstance(value, str):
                        value = value.lower() in ("true", "yes", "1", "t", "y")
                    else:
                        value = bool(value)
            except (ValueError, TypeError):
                # If conversion fails, use default or skip
                if "default" in schema_info:
                    value = schema_info["default"]
                else:
                    continue

            # Set attribute and track it
            setattr(self, key, value)
            self._auto_attrs.add(key)

    def _load_metadata(self) -> Dict[str, Any]:
        """Load plugin metadata from plugin.yaml or plugin.json.

        Returns:
            Dictionary containing plugin metadata
        """
        # Find plugin directory by looking at module path
        module_file = sys.modules[self.__class__.__module__].__file__
        if not module_file:
            return {}

        plugin_dir = Path(module_file).parent

        # Try to load metadata from plugin.yaml or plugin.json
        metadata_file = plugin_dir / "plugin.yaml"
        if not metadata_file.exists():
            metadata_file = plugin_dir / "plugin.json"
            if not metadata_file.exists():
                return {}

        # Load metadata from file
        try:
            with open(metadata_file) as f:
                if metadata_file.suffix == ".yaml":
                    return yaml.safe_load(f) or {}
                else:
                    import json

                    return json.load(f) or {}
        except Exception as e:
            # Log error but continue
            print(f"Error loading plugin metadata: {e}")
            return {}

    def _inject_env_variables(self) -> None:
        """Inject environment variables into configuration based on metadata."""
        plugin_category = self._metadata.get("plugin_category", "unknown")
        provider_type = self._metadata.get("provider_type", "unknown")
        required_keys = self._metadata.get("required_config_keys", [])

        # Check for each required key in config, then environment
        for key in required_keys:
            # Skip if already in config
            if key in self._config and self._config[key] is not None:
                continue

            # Check environment variables with different prefix patterns
            env_patterns = [
                f"PEPPERPY_{plugin_category.upper()}__{provider_type.upper()}__{key.upper()}",
                f"PEPPERPY_{plugin_category.upper()}_{provider_type.upper()}_{key.upper()}",
                f"{provider_type.upper()}_{key.upper()}",
            ]

            # Try each pattern
            for pattern in env_patterns:
                value = os.environ.get(pattern)
                if value:
                    self._config[key] = value
                    break

    def get_metadata(self) -> Dict[str, Any]:
        """Get plugin metadata.

        Returns:
            Dictionary with plugin metadata
        """
        return self._metadata

    @classmethod
    def get_metadata_class(cls) -> Dict[str, Any]:
        """Get plugin metadata from class attributes.

        Returns:
            Dictionary with plugin metadata from class attributes
        """
        metadata = {
            "name": getattr(cls, "plugin_name", ""),
            "version": getattr(cls, "plugin_version", "0.1.0"),
            "category": getattr(cls, "plugin_category", ""),
            "provider_type": getattr(cls, "provider_type", ""),
            "description": getattr(cls, "plugin_description", ""),
            "author": getattr(cls, "plugin_author", "PepperPy Team"),
            "required_config_keys": getattr(cls, "required_config_keys", []),
        }
        return metadata

    @classmethod
    def generate_plugin_json(cls, directory: str) -> None:
        """Generate plugin.json file from class metadata.

        Args:
            directory: Directory to write plugin.json to
        """
        # Create full metadata dictionary with additional fields
        metadata = cls.get_metadata_class()
        # Add additional fields needed for plugin.json
        plugin_json = {
            "name": metadata["name"],
            "version": metadata["version"],
            "category": metadata["category"],
            "provider_name": metadata["provider_type"],
            "description": metadata["description"],
            "entry_point": f"provider:{cls.__name__}",
            "author": metadata["author"],
            "pepperpy_compatibility": ">=0.1.0",
        }

        # Write to plugin.json
        plugin_json_path = Path(directory) / "plugin.json"
        with open(plugin_json_path, "w") as f:
            json.dump(plugin_json, f, indent=2)

        logger = get_logger(__name__)
        logger.debug(f"Generated plugin.json at {plugin_json_path}")

    @classmethod
    def apply_metadata_from_file(cls, directory: str) -> None:
        """Apply metadata from plugin.yaml or plugin.json file to class attributes.

        Args:
            directory: Directory to look for metadata files
        """
        logger = get_logger(__name__)

        # Check for plugin.yaml first (preferred format)
        plugin_yaml_path = Path(directory) / "plugin.yaml"
        if plugin_yaml_path.exists():
            try:
                with open(plugin_yaml_path) as f:
                    metadata = yaml.safe_load(f)

                # Apply metadata to class attributes
                if "name" in metadata:
                    cls.plugin_name = metadata["name"]
                if "version" in metadata:
                    cls.plugin_version = metadata["version"]
                if "description" in metadata:
                    cls.plugin_description = metadata["description"]
                if "category" in metadata:
                    cls.plugin_category = metadata["category"]
                if "provider_type" in metadata:
                    cls.provider_type = metadata["provider_type"]
                if "author" in metadata:
                    cls.plugin_author = metadata["author"]
                if "required_config_keys" in metadata:
                    cls.required_config_keys = metadata["required_config_keys"]

                logger.debug(f"Applied metadata from plugin.yaml for {cls.__name__}")
                return
            except Exception as e:
                logger.warning(f"Failed to load plugin.yaml: {e}")

        # Fall back to plugin.json if it exists
        plugin_json_path = Path(directory) / "plugin.json"
        if plugin_json_path.exists():
            try:
                with open(plugin_json_path) as f:
                    metadata = json.load(f)

                # Apply metadata to class attributes
                if "name" in metadata:
                    cls.plugin_name = metadata["name"]
                if "version" in metadata:
                    cls.plugin_version = metadata["version"]
                if "description" in metadata:
                    cls.plugin_description = metadata["description"]
                if "category" in metadata:
                    cls.plugin_category = metadata["category"]
                if "provider_name" in metadata:
                    cls.provider_type = metadata["provider_name"]
                if "author" in metadata:
                    cls.plugin_author = metadata["author"]

                logger.debug(f"Applied metadata from plugin.json for {cls.__name__}")
            except Exception as e:
                logger.warning(f"Failed to load plugin.json: {e}")

    @classmethod
    def load_from_directory(cls, directory: str) -> Dict[str, Any]:
        """Load plugin metadata from a directory.

        If metadata files don't exist, generates plugin.json from class metadata.

        Args:
            directory: Plugin directory path

        Returns:
            Plugin metadata

        Raises:
            ValueError: If metadata cannot be loaded or generated
        """
        logger = get_logger(__name__)
        plugin_json_path = Path(directory) / "plugin.json"
        plugin_yaml_path = Path(directory) / "plugin.yaml"
        plugin_class = None

        # First try to load from plugin.yaml (preferred format)
        if plugin_yaml_path.exists():
            try:
                with open(plugin_yaml_path) as f:
                    metadata = yaml.safe_load(f)
                    return {
                        "name": metadata.get("name", ""),
                        "version": metadata.get("version", "0.1.0"),
                        "category": metadata.get("category", ""),
                        "provider_name": metadata.get("provider_type", ""),
                        "description": metadata.get("description", ""),
                        "author": metadata.get("author", "PepperPy Team"),
                        "pepperpy_compatibility": ">=0.1.0",
                        "required_config_keys": metadata.get(
                            "required_config_keys", []
                        ),
                    }
            except Exception as e:
                logger.warning(f"Failed to load plugin.yaml: {e}")

        # Then try plugin.json
        if plugin_json_path.exists():
            try:
                with open(plugin_json_path) as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load plugin.json: {e}")

        # If no metadata files exist, try to find the provider class and generate metadata
        try:
            # Try to import provider module
            provider_path = Path(directory) / "provider.py"
            if provider_path.exists():
                spec = importlib.util.spec_from_file_location(
                    "provider", str(provider_path)
                )
                if spec and spec.loader:
                    provider_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(provider_module)

                    # Find the ProviderPlugin subclass
                    for attr_name in dir(provider_module):
                        attr = getattr(provider_module, attr_name)
                        if (
                            isinstance(attr, type)
                            and issubclass(attr, ProviderPlugin)
                            and attr != ProviderPlugin
                        ):
                            plugin_class = attr
                            break

                    # Generate plugin.json if class was found
                    if plugin_class:
                        # First apply any metadata from YAML if it exists but is incomplete
                        plugin_class.apply_metadata_from_file(directory)

                        plugin_class.generate_plugin_json(directory)
                        logger.info(
                            f"Generated plugin.json from class metadata for {directory}"
                        )

                        # Now load the generated file
                        with open(plugin_json_path) as f:
                            return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to generate metadata for {directory}: {e}")

        raise ValueError(
            f"Unable to load or generate metadata for plugin in {directory}"
        )

    @classmethod
    def install_dependencies(cls, directory: str) -> bool:
        """Install plugin dependencies using UV.

        Args:
            directory: Plugin directory path

        Returns:
            True if dependencies were installed successfully, False otherwise
        """
        logger = get_logger(__name__)
        requirements_path = Path(directory) / "requirements.txt"
        if not requirements_path.exists():
            # If no requirements.txt, create it with only core dependencies
            try:
                with open(requirements_path, "w") as f:
                    f.write("# PepperPy plugin dependencies\n")
                logger.info(f"Created empty requirements.txt for plugin in {directory}")
            except Exception as e:
                logger.warning(f"Failed to create requirements.txt: {e}")
            return True  # No external dependencies needed

        # Check if requirements.txt has only comments
        try:
            with open(requirements_path) as f:
                content = f.read().strip()
                if not content or all(
                    line.strip().startswith("#") for line in content.split("\n")
                ):
                    logger.info(f"No dependencies needed for plugin in {directory}")
                    return True
        except Exception:
            pass  # If we can't read the file, try to install anyway

        try:
            logger.info(f"Installing dependencies for plugin in {directory}")
            result = subprocess.run(
                ["uv", "pip", "install", "-r", str(requirements_path)],
                check=True,
                capture_output=True,
                text=True,
            )
            logger.info(
                f"Successfully installed dependencies for plugin in {directory}"
            )
            logger.debug(f"UV output: {result.stdout}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install dependencies: {e.stderr}")
            return False
        except FileNotFoundError:
            logger.error("UV is not installed. Please install UV: pip install uv")
            return False

    def update_config(self, **config: Any) -> None:
        """
        Updates provider configuration and automatically rebinds attributes.

        This overrides BaseProvider's update_config method to add automatic
        attribute binding after configuration update.

        Args:
            **config: Configuration key-value pairs to update.
        """
        # Update config dictionary
        self._config.update(config)

        # Rebind attributes after config update
        self._auto_bind_config_attributes()


def discover_plugins(plugins_dir: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    """Discover available plugins.

    Args:
        plugins_dir: Directory to scan for plugins. If None, uses the default
            plugins directory.

    Returns:
        Dictionary mapping plugin names to metadata
    """
    logger = get_logger(__name__)

    if plugins_dir is None:
        # Try to find plugins directory relative to this file
        current_dir = Path(__file__).parent
        plugins_dir = str(current_dir.parent / "plugins")
        if not Path(plugins_dir).exists():
            logger.warning(f"Plugins directory not found: {plugins_dir}")
            return {}

    plugins = {}
    for plugin_dir in Path(plugins_dir).iterdir():
        if not plugin_dir.is_dir():
            continue

        try:
            # Attempt to load metadata from plugin.yaml, plugin.json, or generate it
            try:
                metadata = ProviderPlugin.load_from_directory(str(plugin_dir))
                plugins[metadata.get("name", plugin_dir.name)] = metadata
            except ValueError as e:
                logger.warning(f"Failed to load plugin metadata: {e}")
                continue

            # Check if requirements.txt exists
            requirements_path = plugin_dir / "requirements.txt"
            if not requirements_path.exists():
                # Create empty requirements file if it doesn't exist
                try:
                    with open(requirements_path, "w") as f:
                        f.write("# PepperPy plugin dependencies\n")
                    logger.debug(
                        f"Created empty requirements.txt for plugin {plugin_dir.name}"
                    )
                except Exception as e:
                    logger.warning(f"Failed to create requirements.txt: {e}")
        except Exception as e:
            logger.error(f"Failed to load plugin from {plugin_dir}: {e}")

    return plugins


def install_plugin_dependencies(
    plugin_name: str, plugins_dir: Optional[str] = None
) -> bool:
    """Install dependencies for a specific plugin using UV.

    Args:
        plugin_name: Name of the plugin
        plugins_dir: Directory to scan for plugins. If None, uses the default
            plugins directory.

    Returns:
        True if dependencies were installed successfully, False otherwise
    """
    logger = get_logger(__name__)

    if plugins_dir is None:
        # Try to find plugins directory relative to this file
        current_dir = Path(__file__).parent
        plugins_dir = str(current_dir.parent / "plugins")

    plugin_dir = Path(plugins_dir) / plugin_name
    if not plugin_dir.exists():
        logger.error(f"Plugin directory not found: {plugin_dir}")
        return False

    return ProviderPlugin.install_dependencies(str(plugin_dir))


# Initialize the module logger
logger = get_logger(__name__)


def _load_plugin_specs(self, plugin_name: str):
    """Load plugin specs.

    Args:
        plugin_name: Plugin name

    Returns:
        Plugin specs
    """
    try:
        # Try to load from importlib
        spec = importlib.util.find_spec(plugin_name)
        if spec is not None:
            return spec
    except (ImportError, ValueError):
        pass
