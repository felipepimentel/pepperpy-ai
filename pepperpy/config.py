"""Configuration system for the PepperPy framework.

This module provides a unified configuration system for the PepperPy framework.
It supports loading configuration from various sources, including environment
variables, configuration files, and programmatic configuration.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from pepperpy.core.errors import ConfigError
from pepperpy.core.logging import get_logger
from pepperpy.core.types import PathType

# Logger for this module
logger = get_logger(__name__)


class ConfigSource:
    """Base class for configuration sources.

    Configuration sources provide configuration data from different locations,
    such as environment variables, files, or dictionaries.
    """

    def load(self) -> Dict[str, Any]:
        """Load configuration from this source.

        Returns:
            Dictionary containing configuration data

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Subclasses must implement load()")


class EnvironmentConfigSource(ConfigSource):
    """Configuration source that loads from environment variables.

    This source loads configuration from environment variables with a specified
    prefix. The environment variable names are converted to configuration keys
    by removing the prefix and converting to lowercase with dots as separators.

    For example, the environment variable `PEPPERPY_DATABASE_URL` would be
    converted to the configuration key `database.url`.
    """

    def __init__(self, prefix: str = "PEPPERPY_"):
        """Initialize the environment configuration source.

        Args:
            prefix: Prefix for environment variables to load
        """
        self.prefix = prefix

    def load(self) -> Dict[str, Any]:
        """Load configuration from environment variables.

        Returns:
            Dictionary containing configuration data from environment variables
        """
        config: Dict[str, Any] = {}

        for key, value in os.environ.items():
            if key.startswith(self.prefix):
                # Remove prefix and convert to lowercase
                config_key = key[len(self.prefix) :].lower()

                # Convert underscores to dots for nested keys
                config_key = config_key.replace("_", ".")

                # Parse value
                if value.lower() in ("true", "yes", "1"):
                    parsed_value = True
                elif value.lower() in ("false", "no", "0"):
                    parsed_value = False
                elif value.isdigit():
                    parsed_value = int(value)
                elif value.replace(".", "", 1).isdigit() and value.count(".") == 1:
                    parsed_value = float(value)
                else:
                    parsed_value = value

                # Set value in config
                self._set_nested_key(config, config_key, parsed_value)

        return config

    def _set_nested_key(self, config: Dict[str, Any], key: str, value: Any) -> None:
        """Set a nested key in a dictionary.

        Args:
            config: Dictionary to set key in
            key: Dot-separated key
            value: Value to set
        """
        parts = key.split(".")
        current = config

        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]

        current[parts[-1]] = value


class FileConfigSource(ConfigSource):
    """Configuration source that loads from a file.

    This source loads configuration from a JSON or YAML file.
    """

    def __init__(self, file_path: PathType):
        """Initialize the file configuration source.

        Args:
            file_path: Path to the configuration file
        """
        self.file_path = Path(file_path)

    def load(self) -> Dict[str, Any]:
        """Load configuration from a file.

        Returns:
            Dictionary containing configuration data from the file

        Raises:
            ConfigError: If the file cannot be loaded
        """
        try:
            if not self.file_path.exists():
                logger.warning(f"Configuration file not found: {self.file_path}")
                return {}

            with open(self.file_path, "r", encoding="utf-8") as f:
                if self.file_path.suffix.lower() in (".json", ".jsn"):
                    return json.load(f)
                elif self.file_path.suffix.lower() in (".yaml", ".yml"):
                    try:
                        import yaml

                        return yaml.safe_load(f)
                    except ImportError:
                        raise ConfigError("PyYAML is required to load YAML files")
                else:
                    raise ConfigError(
                        f"Unsupported file format: {self.file_path.suffix}"
                    )
        except Exception as e:
            raise ConfigError(f"Failed to load configuration file: {str(e)}") from e


class DictConfigSource(ConfigSource):
    """Configuration source that loads from a dictionary.

    This source loads configuration from a dictionary provided at initialization.
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize the dictionary configuration source.

        Args:
            config: Dictionary containing configuration data
        """
        self.config = config

    def load(self) -> Dict[str, Any]:
        """Load configuration from the dictionary.

        Returns:
            Dictionary containing configuration data
        """
        return self.config


class ConfigManager:
    """Manages configuration for the PepperPy framework.

    The config manager loads configuration from multiple sources and provides
    a unified interface for accessing configuration values.
    """

    def __init__(self):
        """Initialize the configuration manager."""
        self._sources: List[ConfigSource] = []
        self._config: Dict[str, Any] = {}
        self._loaded = False

    def add_source(self, source: ConfigSource) -> None:
        """Add a configuration source.

        Args:
            source: Configuration source to add
        """
        self._sources.append(source)
        self._loaded = False

    def load(self) -> None:
        """Load configuration from all sources.

        This method loads configuration from all registered sources in the order
        they were added. Later sources override values from earlier sources.
        """
        self._config = {}

        for source in self._sources:
            try:
                source_config = source.load()
                self._deep_update(self._config, source_config)
            except Exception as e:
                logger.error(f"Failed to load configuration from {source}: {str(e)}")

        self._loaded = True
        logger.info(f"Loaded configuration from {len(self._sources)} sources")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.

        Args:
            key: Configuration key (dot-separated for nested keys)
            default: Default value to return if key is not found

        Returns:
            Configuration value, or default if not found
        """
        if not self._loaded:
            self.load()

        parts = key.split(".")
        current = self._config

        for part in parts:
            if not isinstance(current, dict) or part not in current:
                return default
            current = current[part]

        return current

    def require(self, key: str) -> Any:
        """Get a required configuration value.

        Args:
            key: Configuration key (dot-separated for nested keys)

        Returns:
            Configuration value

        Raises:
            ConfigError: If the key is not found
        """
        value = self.get(key)
        if value is None:
            raise ConfigError(f"Required configuration key not found: {key}")
        return value

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value.

        Args:
            key: Configuration key (dot-separated for nested keys)
            value: Value to set
        """
        if not self._loaded:
            self.load()

        parts = key.split(".")
        current = self._config

        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            elif not isinstance(current[part], dict):
                current[part] = {}
            current = current[part]

        current[parts[-1]] = value

    def as_dict(self) -> Dict[str, Any]:
        """Get the entire configuration as a dictionary.

        Returns:
            Dictionary containing all configuration values
        """
        if not self._loaded:
            self.load()

        return self._config.copy()

    def _deep_update(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """Deep update a dictionary.

        This method recursively updates a dictionary with values from another
        dictionary, preserving nested structures.

        Args:
            target: Dictionary to update
            source: Dictionary to update from
        """
        for key, value in source.items():
            if (
                key in target
                and isinstance(target[key], dict)
                and isinstance(value, dict)
            ):
                self._deep_update(target[key], value)
            else:
                target[key] = value


# Global configuration manager instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get the global configuration manager instance.

    Returns:
        The global configuration manager instance
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def set_config_manager(manager: ConfigManager) -> None:
    """Set the global configuration manager instance.

    Args:
        manager: The configuration manager instance to set
    """
    global _config_manager
    _config_manager = manager


def get_config(key: str, default: Any = None) -> Any:
    """Get a configuration value from the global configuration manager.

    Args:
        key: Configuration key (dot-separated for nested keys)
        default: Default value to return if key is not found

    Returns:
        Configuration value, or default if not found
    """
    return get_config_manager().get(key, default)


def require_config(key: str) -> Any:
    """Get a required configuration value from the global configuration manager.

    Args:
        key: Configuration key (dot-separated for nested keys)

    Returns:
        Configuration value

    Raises:
        ConfigError: If the key is not found
    """
    return get_config_manager().require(key)


def set_config(key: str, value: Any) -> None:
    """Set a configuration value in the global configuration manager.

    Args:
        key: Configuration key (dot-separated for nested keys)
        value: Value to set
    """
    get_config_manager().set(key, value)


def load_config() -> None:
    """Load configuration from all sources in the global configuration manager."""
    get_config_manager().load()


def add_config_source(source: ConfigSource) -> None:
    """Add a configuration source to the global configuration manager.

    Args:
        source: Configuration source to add
    """
    get_config_manager().add_source(source)


def load_default_config() -> None:
    """Load default configuration for the PepperPy framework.

    This function adds default configuration sources to the global configuration
    manager and loads configuration from them.
    """
    manager = get_config_manager()

    # Add environment variables
    manager.add_source(EnvironmentConfigSource())

    # Add configuration file
    config_file = os.environ.get("PEPPERPY_CONFIG_FILE", "config.json")
    manager.add_source(FileConfigSource(config_file))

    # Load configuration
    manager.load()

    logger.info("Loaded default configuration")


__all__ = [
    # Classes
    "ConfigSource",
    "EnvironmentConfigSource",
    "FileConfigSource",
    "DictConfigSource",
    "ConfigManager",
    # Functions
    "get_config_manager",
    "set_config_manager",
    "get_config",
    "require_config",
    "set_config",
    "load_config",
    "add_config_source",
    "load_default_config",
]
