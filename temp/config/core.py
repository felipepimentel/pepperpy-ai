"""Core functionality for configuration in PepperPy.

This module provides the core functionality for configuration in PepperPy,
including configuration loading, validation, and access.
"""

import json
import os
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, TypeVar, Union, get_type_hints

from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)

# Type variable for configuration types
T = TypeVar("T")


class ConfigSource(str, Enum):
    """Sources of configuration values."""

    DEFAULT = "default"
    ENV = "environment"
    FILE = "file"
    OVERRIDE = "override"


@dataclass
class ConfigValue:
    """A configuration value with metadata.

    A config value represents a single configuration value, along with metadata
    about where it came from and when it was set.
    """

    value: Any
    source: ConfigSource = ConfigSource.DEFAULT
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConfigError(Exception):
    """Base class for configuration errors."""

    pass


class ConfigValidationError(ConfigError):
    """Error raised when configuration validation fails."""

    def __init__(self, message: str, errors: Optional[Dict[str, str]] = None):
        """Initialize a configuration validation error.

        Args:
            message: The error message
            errors: A dictionary of field-specific error messages
        """
        super().__init__(message)
        self.errors = errors or {}


class ConfigNotFoundError(ConfigError):
    """Error raised when a configuration file is not found."""

    pass


class ConfigSection:
    """Base class for configuration sections.

    A configuration section is a group of related configuration values.
    """

    def __init__(self, **kwargs: Any):
        """Initialize a configuration section.

        Args:
            **kwargs: Configuration values to set
        """
        # Set default values
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the configuration section to a dictionary.

        Returns:
            The configuration section as a dictionary
        """
        if is_dataclass(self):
            return asdict(self)

        result = {}
        for key, value in self.__dict__.items():
            if not key.startswith("_"):
                if isinstance(value, ConfigSection):
                    result[key] = value.to_dict()
                else:
                    result[key] = value

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConfigSection":
        """Create a configuration section from a dictionary.

        Args:
            data: The dictionary to create the configuration section from

        Returns:
            The created configuration section
        """
        # Create a new instance
        instance = cls()

        # Set values from the dictionary
        for key, value in data.items():
            if hasattr(instance, key):
                # Get the type of the attribute
                attr_type = get_type_hints(cls).get(key)

                # If the attribute is a ConfigSection, recursively create it
                if attr_type and issubclass(attr_type, ConfigSection):
                    setattr(instance, key, attr_type.from_dict(value))
                else:
                    setattr(instance, key, value)

        return instance


class ConfigLoader(ABC):
    """Base class for configuration loaders.

    A configuration loader is responsible for loading configuration values from
    a specific source.
    """

    @abstractmethod
    def load(self, config_class: Type[T]) -> T:
        """Load configuration values.

        Args:
            config_class: The configuration class to load values for

        Returns:
            The loaded configuration
        """
        pass


class EnvConfigLoader(ConfigLoader):
    """Configuration loader that loads values from environment variables.

    This loader loads configuration values from environment variables, using
    a prefix to identify which variables belong to the application.
    """

    def __init__(self, prefix: str = "PEPPERPY_"):
        """Initialize an environment configuration loader.

        Args:
            prefix: The prefix for environment variables
        """
        self.prefix = prefix

    def load(self, config_class: Type[T]) -> T:
        """Load configuration values from environment variables.

        Args:
            config_class: The configuration class to load values for

        Returns:
            The loaded configuration
        """
        # Create a new instance of the configuration class
        config = config_class()

        # Get all environment variables with the prefix
        env_vars = {
            key[len(self.prefix) :]: value
            for key, value in os.environ.items()
            if key.startswith(self.prefix)
        }

        # Set values from environment variables
        for key, value in env_vars.items():
            # Convert key to lowercase
            key_lower = key.lower()

            # Try to set the value on the configuration object
            self._set_value(config, key_lower, value)

        return config

    def _set_value(self, config: Any, key: str, value: str) -> None:
        """Set a value on a configuration object.

        Args:
            config: The configuration object to set the value on
            key: The key to set
            value: The value to set
        """
        # Split the key by underscores
        parts = key.split("_")

        # Navigate to the correct configuration section
        current = config
        for i, part in enumerate(parts[:-1]):
            if hasattr(current, part):
                current = getattr(current, part)
            else:
                # If the attribute doesn't exist, we can't set the value
                return

        # Set the value on the final configuration section
        final_key = parts[-1]
        if hasattr(current, final_key):
            # Get the current value to determine its type
            current_value = getattr(current, final_key)

            # Convert the value to the correct type
            if isinstance(current_value, bool):
                # Convert string to boolean
                converted_value = value.lower() in ("true", "1", "yes", "y", "on")
            elif isinstance(current_value, int):
                # Convert string to integer
                converted_value = int(value)
            elif isinstance(current_value, float):
                # Convert string to float
                converted_value = float(value)
            elif isinstance(current_value, list):
                # Convert string to list
                converted_value = value.split(",")
            elif isinstance(current_value, dict):
                # Convert string to dictionary
                try:
                    converted_value = json.loads(value)
                except json.JSONDecodeError:
                    # If the value is not valid JSON, use it as is
                    converted_value = value
            else:
                # Use the value as is
                converted_value = value

            # Set the value
            setattr(current, final_key, converted_value)


class FileConfigLoader(ConfigLoader):
    """Configuration loader that loads values from a file.

    This loader loads configuration values from a file, supporting various
    file formats such as JSON, YAML, and TOML.
    """

    def __init__(self, file_path: Union[str, Path]):
        """Initialize a file configuration loader.

        Args:
            file_path: The path to the configuration file
        """
        self.file_path = Path(file_path)

    def load(self, config_class: Type[T]) -> T:
        """Load configuration values from a file.

        Args:
            config_class: The configuration class to load values for

        Returns:
            The loaded configuration

        Raises:
            FileNotFoundError: If the configuration file does not exist
            ValueError: If the configuration file has an unsupported format
        """
        # Check if the file exists
        if not self.file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.file_path}")

        # Load the file based on its extension
        extension = self.file_path.suffix.lower()

        if extension == ".json":
            # Load JSON file
            with open(self.file_path, "r") as f:
                data = json.load(f)
        elif extension in (".yaml", ".yml"):
            # Load YAML file
            try:
                import yaml

                with open(self.file_path, "r") as f:
                    data = yaml.safe_load(f)
            except ImportError:
                raise ImportError(
                    "The 'pyyaml' package is required to load YAML configuration files. "
                    "Install it with 'pip install pyyaml'."
                )
        elif extension == ".toml":
            # Load TOML file
            try:
                import tomli

                with open(self.file_path, "rb") as f:
                    data = tomli.load(f)
            except ImportError:
                raise ImportError(
                    "The 'tomli' package is required to load TOML configuration files. "
                    "Install it with 'pip install tomli'."
                )
        else:
            raise ValueError(f"Unsupported configuration file format: {extension}")

        # Create a new instance of the configuration class
        if hasattr(config_class, "from_dict") and callable(
            getattr(config_class, "from_dict")
        ):
            # If the class has a from_dict method, use it
            config = config_class.from_dict(data)
        else:
            # Otherwise, create a new instance and set values manually
            config = config_class()
            self._set_values(config, data)

        return config

    def _set_values(self, config: Any, data: Dict[str, Any]) -> None:
        """Set values on a configuration object from a dictionary.

        Args:
            config: The configuration object to set values on
            data: The dictionary of values to set
        """
        for key, value in data.items():
            if hasattr(config, key):
                # Get the current value to determine its type
                current_value = getattr(config, key)

                # If the current value is a ConfigSection and the new value is a dictionary,
                # recursively set values on the ConfigSection
                if isinstance(current_value, ConfigSection) and isinstance(value, dict):
                    self._set_values(current_value, value)
                else:
                    # Otherwise, set the value directly
                    setattr(config, key, value)


class Config:
    """Configuration manager.

    The configuration manager provides a high-level interface for working with
    configuration values, including loading, validation, and access.
    """

    def __init__(
        self, config_class: Type[T], loaders: Optional[List[ConfigLoader]] = None
    ):
        """Initialize the configuration manager.

        Args:
            config_class: The configuration class to manage
            loaders: The configuration loaders to use
        """
        self.config_class = config_class
        self.loaders = loaders or []
        self._config: Optional[T] = None

    def add_loader(self, loader: ConfigLoader) -> "Config":
        """Add a configuration loader.

        Args:
            loader: The loader to add

        Returns:
            The configuration manager
        """
        self.loaders.append(loader)
        return self

    def load(self) -> T:
        """Load configuration values.

        Returns:
            The loaded configuration
        """
        # Create a new instance of the configuration class
        config = self.config_class()

        # Load values from each loader
        for loader in self.loaders:
            try:
                # Load values from the loader
                loaded_config = loader.load(self.config_class)

                # Merge the loaded values into the configuration
                self._merge_config(config, loaded_config)
            except Exception as e:
                logger.warning(
                    f"Error loading configuration from {loader.__class__.__name__}: {str(e)}"
                )

        # Store the loaded configuration
        self._config = config

        return config

    def get(self) -> T:
        """Get the loaded configuration.

        Returns:
            The loaded configuration

        Raises:
            ValueError: If the configuration has not been loaded
        """
        if self._config is None:
            raise ValueError("Configuration has not been loaded")

        return self._config

    def _merge_config(self, target: Any, source: Any) -> None:
        """Merge configuration values from source into target.

        Args:
            target: The target configuration object
            source: The source configuration object
        """
        # Get all attributes of the source
        for key in dir(source):
            # Skip private attributes
            if key.startswith("_"):
                continue

            # Skip methods and properties
            if callable(getattr(source, key)) or isinstance(
                getattr(type(source), key, None), property
            ):
                continue

            # Get the value from the source
            source_value = getattr(source, key)

            # If the target has the attribute, set it
            if hasattr(target, key):
                target_value = getattr(target, key)

                # If both values are ConfigSection instances, recursively merge them
                if isinstance(source_value, ConfigSection) and isinstance(
                    target_value, ConfigSection
                ):
                    self._merge_config(target_value, source_value)
                else:
                    # Otherwise, set the value directly
                    setattr(target, key, source_value)


# Default configuration class
@dataclass
class AppConfig(ConfigSection):
    """Application configuration.

    This class provides default configuration values for the application.
    """

    # Debug mode
    debug: bool = False

    # Logging configuration
    log_level: str = "info"
    log_file: Optional[str] = None

    # API configuration
    api_key: Optional[str] = None
    api_url: Optional[str] = None

    # LLM configuration
    llm_provider: str = "openai"
    llm_model: str = "gpt-3.5-turbo"


# Factory function to create a configuration manager
def create_config(
    config_class: Type[T] = AppConfig,
    env_prefix: str = "PEPPERPY_",
    config_file: Optional[Union[str, Path]] = None,
) -> Config:
    """Create a configuration manager.

    Args:
        config_class: The configuration class to manage
        env_prefix: The prefix for environment variables
        config_file: The path to the configuration file

    Returns:
        The created configuration manager
    """
    # Create the configuration manager
    config_manager = Config(config_class)

    # Add environment loader
    config_manager.add_loader(EnvConfigLoader(prefix=env_prefix))

    # Add file loader if a configuration file is specified
    if config_file:
        config_manager.add_loader(FileConfigLoader(file_path=config_file))

    return config_manager
