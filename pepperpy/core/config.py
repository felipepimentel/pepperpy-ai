"""Centralized configuration management with validation for PepperPy.

This module provides a comprehensive configuration system that supports
multiple sources (files, environment, code), validation, and hierarchical
structure with consistent access patterns.
"""

import json
import os
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import (
    Annotated,
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Type,
    TypeVar,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

import yaml
from jsonschema import ValidationError as JsonValidationError
from jsonschema import validate

from pepperpy.core.errors import ConfigurationError, ValidationError

T = TypeVar("T")
ConfigValidator = Callable[[Any], Any]


class ConfigSource(Enum):
    """Configuration source types."""

    DEFAULT = "default"  # Default values
    FILE = "file"  # Configuration file
    ENV = "env"  # Environment variables
    DIRECT = "direct"  # Directly set via code
    SCHEMA = "schema"  # Schema default values


class ConfigSchema:
    """Configuration schema with validation.

    This class provides schema-based validation for configuration values,
    including type checking, constraints, and custom validators.
    """

    def __init__(self, schema: Dict[str, Any]):
        """Initialize configuration schema.

        Args:
            schema: JSON Schema for configuration
        """
        self.schema = schema

    def validate(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate configuration against schema.

        Args:
            config: Configuration to validate

        Returns:
            Validated configuration

        Raises:
            ValidationError: If validation fails
        """
        try:
            validate(instance=config, schema=self.schema)
            return config
        except JsonValidationError as e:
            raise ValidationError(
                f"Configuration validation failed: {e.message}",
                field=".".join(str(p) for p in e.path),
                value=e.instance,
                constraint=e.schema.get("description", ""),
            ) from e

    @classmethod
    def from_class(cls, config_cls: Type[Any]) -> "ConfigSchema":
        """Create schema from a configuration class.

        Args:
            config_cls: Configuration class with type annotations

        Returns:
            Configuration schema
        """
        schema = {"type": "object", "properties": {}, "additionalProperties": False}

        # Get type hints
        type_hints = get_type_hints(config_cls, include_extras=True)

        # Create JSON Schema properties from type hints
        for name, type_hint in type_hints.items():
            # Skip private attributes
            if name.startswith("_"):
                continue

            # Get field schema
            field_schema = cls._get_field_schema(name, type_hint, config_cls)

            # Add to properties
            if field_schema:
                schema["properties"][name] = field_schema

                # Check if required
                if cls._is_required(name, type_hint, config_cls):
                    if "required" not in schema:
                        schema["required"] = []
                    schema["required"].append(name)

        return cls(schema)

    @classmethod
    def _get_field_schema(
        cls, name: str, type_hint: Any, config_cls: Type[Any]
    ) -> Dict[str, Any]:
        """Get JSON Schema for a field.

        Args:
            name: Field name
            type_hint: Field type hint
            config_cls: Configuration class

        Returns:
            JSON Schema for the field
        """
        # Check for Annotated type
        if get_origin(type_hint) is Annotated:
            # Get the base type and annotations
            args = get_args(type_hint)
            base_type = args[0]
            annotations = args[1:]

            # Create base schema
            schema = cls._get_field_schema(name, base_type, config_cls)

            # Apply annotations
            for annotation in annotations:
                if isinstance(annotation, dict):
                    # Annotation is a dict with schema properties
                    schema.update(annotation)

            return schema

        # Get default value if available
        if hasattr(config_cls, name):
            default_value = getattr(config_cls, name)

            # Add default to schema
            schema = cls._type_to_schema(type_hint)
            schema["default"] = default_value

            return schema

        # Just use the type
        return cls._type_to_schema(type_hint)

    @classmethod
    def _type_to_schema(cls, type_hint: Any) -> Dict[str, Any]:
        """Convert type hint to JSON Schema.

        Args:
            type_hint: Type hint

        Returns:
            JSON Schema for the type
        """
        # Handle Optional
        if get_origin(type_hint) is Union:
            args = get_args(type_hint)
            if type(None) in args:
                # It's an Optional[Type]
                non_none_args = [arg for arg in args if arg is not type(None)]
                if len(non_none_args) == 1:
                    # Single non-None type
                    return cls._type_to_schema(non_none_args[0])
                else:
                    # Multiple non-None types (oneOf)
                    return {
                        "oneOf": [cls._type_to_schema(arg) for arg in non_none_args]
                    }

        # Handle List
        if get_origin(type_hint) is list:
            args = get_args(type_hint)
            if args:
                item_type = args[0]
                return {"type": "array", "items": cls._type_to_schema(item_type)}
            else:
                return {"type": "array"}

        # Handle Dict
        if get_origin(type_hint) is dict:
            args = get_args(type_hint)
            if len(args) >= 2:
                key_type, value_type = args[:2]

                # Only string keys are supported in JSON Schema
                if key_type is str:
                    return {
                        "type": "object",
                        "additionalProperties": cls._type_to_schema(value_type),
                    }

            return {"type": "object"}

        # Handle simple types
        if type_hint is str:
            return {"type": "string"}
        elif type_hint is int:
            return {"type": "integer"}
        elif type_hint is float:
            return {"type": "number"}
        elif type_hint is bool:
            return {"type": "boolean"}
        elif type_hint is list:
            return {"type": "array"}
        elif type_hint is dict:
            return {"type": "object"}

        # Default to any type
        return {}

    @classmethod
    def _is_required(cls, name: str, type_hint: Any, config_cls: Type[Any]) -> bool:
        """Check if a field is required.

        Args:
            name: Field name
            type_hint: Field type hint
            config_cls: Configuration class

        Returns:
            True if field is required, False otherwise
        """
        # Check if it has a default value
        if hasattr(config_cls, name):
            return False

        # Check if it's Optional
        if get_origin(type_hint) is Union:
            args = get_args(type_hint)
            if type(None) in args:
                return False

        # Otherwise it's required
        return True


class ConfigValue:
    """Configuration value with source information."""

    def __init__(
        self, value: Any, source: ConfigSource, schema: Optional[Dict[str, Any]] = None
    ):
        """Initialize configuration value.

        Args:
            value: Configuration value
            source: Source of the value
            schema: Optional schema for validation
        """
        self.value = value
        self.source = source
        self.schema = schema

    def validate(self) -> None:
        """Validate the value against schema.

        Raises:
            ValidationError: If validation fails
        """
        if self.schema:
            try:
                validate(instance=self.value, schema=self.schema)
            except JsonValidationError as e:
                raise ValidationError(
                    f"Configuration validation failed: {e.message}",
                    field=".".join(str(p) for p in e.path) if e.path else None,
                    value=e.instance,
                    constraint=e.schema.get("description", ""),
                ) from e


class Config:
    """Configuration management class.

    This class handles loading, validating, and accessing configuration values
    from various sources including files, environment variables, and defaults.

    Args:
        config_path: Optional path to config file
        env_prefix: Optional prefix for environment variables
        defaults: Optional default configuration values
        schema: Optional JSON Schema for validation
        **kwargs: Additional configuration values

    Example:
        >>> config = Config(
        ...     config_path="config.yaml",
        ...     env_prefix="APP_",
        ...     defaults={"debug": False},
        ...     api_key="abc123"
        ... )
        >>> print(config.get("api_key"))
    """

    def __init__(
        self,
        config_path: Optional[Union[str, Path, Dict[str, Any], "Config"]] = None,
        env_prefix: str = "PEPPERPY_",
        defaults: Optional[Dict[str, Any]] = None,
        schema: Optional[Dict[str, Any]] = None,
        case_sensitive: bool = False,
        **kwargs: Any,
    ):
        """Initialize configuration.

        Args:
            config_path: Path to config file, dict with config values, or Config object
            env_prefix: Optional prefix for environment variables
            defaults: Optional default configuration values
            schema: Optional JSON Schema for validation
            case_sensitive: Whether keys are case-sensitive
            **kwargs: Additional configuration values

        Raises:
            ValidationError: If config file is invalid or schema validation fails
        """
        self._values: Dict[str, ConfigValue] = {}
        self._env_prefix = env_prefix
        self._schema = schema
        self._case_sensitive = case_sensitive

        # Create config schema
        if schema:
            self._config_schema = ConfigSchema(schema)
        else:
            self._config_schema = None

        # Load defaults
        if defaults:
            self._load_from_dict(defaults, ConfigSource.DEFAULT)

        # Load from file or dictionary
        if config_path is not None:
            if isinstance(config_path, Config):
                # Copy values from another Config object
                for key, value in config_path._values.items():
                    self._values[self._normalize_key(key)] = value
            elif isinstance(config_path, dict):
                # Load from dictionary
                self._load_from_dict(config_path, ConfigSource.DIRECT)
            elif isinstance(config_path, (str, Path)):
                # Load from file
                self._load_from_file(config_path)
            else:
                raise ValidationError(
                    f"Invalid config_path type: {type(config_path)}", value=config_path
                )

        # Load from environment
        self._load_from_env()

        # Load from kwargs
        if kwargs:
            self._load_from_dict(kwargs, ConfigSource.DIRECT)

        # Validate against schema
        if self._config_schema:
            try:
                self._config_schema.validate(self.to_dict())
            except ValidationError as e:
                raise ConfigurationError(
                    f"Configuration schema validation failed: {e}",
                    config_key=e.field,
                    config_value=e.value,
                ) from e

    def _normalize_key(self, key: str) -> str:
        """Normalize configuration key.

        Args:
            key: Configuration key

        Returns:
            Normalized key
        """
        if self._case_sensitive:
            return key
        return key.lower()

    def _load_from_file(self, path: Union[str, Path]) -> None:
        """Load configuration from file.

        Args:
            path: Path to configuration file

        Raises:
            ValidationError: If file is invalid or cannot be read
        """
        try:
            path = Path(path)
            if not path.exists():
                raise ValidationError(
                    f"Config file not found: {path}",
                    field="config_path",
                    value=str(path),
                )

            # Determine file type from extension
            if path.suffix.lower() in (".yaml", ".yml"):
                with open(path) as f:
                    config = yaml.safe_load(f)
            elif path.suffix.lower() == ".json":
                with open(path) as f:
                    config = json.load(f)
            else:
                raise ValidationError(
                    f"Unsupported config file type: {path.suffix}",
                    field="config_path",
                    value=str(path),
                )

            if not isinstance(config, dict):
                raise ValidationError(
                    "Config file must contain a dictionary",
                    field="config_path",
                    value=str(path),
                )

            # Load values
            self._load_from_dict(config, ConfigSource.FILE)

        except (yaml.YAMLError, json.JSONDecodeError) as e:
            raise ValidationError(
                f"Failed to parse config file: {e}",
                field="config_path",
                value=str(path),
            ) from e
        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            raise ValidationError(
                f"Failed to load config file: {e}", field="config_path", value=str(path)
            ) from e

    def _load_from_env(self) -> None:
        """Load configuration from environment variables.

        Environment variables are converted from uppercase with underscores
        to lowercase with dots. For example:
            APP_DATABASE_URL -> database.url
        """
        if not self._env_prefix:
            return

        prefix = self._env_prefix.rstrip("_").upper() + "_"
        prefix_len = len(prefix)

        env_config = {}

        for key, value in os.environ.items():
            if key.startswith(prefix):
                # Convert APP_DATABASE_URL to database.url
                config_key = key[prefix_len:].lower().replace("_", ".")

                # Try to parse value as JSON if it looks like it might be
                if (
                    value.startswith(("{", "[", "true", "false", "null"))
                    or value.isdigit()
                ):
                    try:
                        env_config[config_key] = json.loads(value)
                        continue
                    except json.JSONDecodeError:
                        pass

                # Plain string value
                env_config[config_key] = value

        # Load the flattened environment variables
        for key, value in env_config.items():
            self.set(key, value, source=ConfigSource.ENV)

    def _load_from_dict(self, config: Dict[str, Any], source: ConfigSource) -> None:
        """Load configuration from dictionary.

        Args:
            config: Configuration dictionary
            source: Source of the configuration
        """

        def process_value(key: str, value: Any) -> None:
            """Process a configuration value."""
            # For nested dictionaries, flatten with dot notation
            if isinstance(value, dict):
                for subkey, subvalue in value.items():
                    process_value(f"{key}.{subkey}", subvalue)
            else:
                # Set value with source information
                self.set(key, value, source=source)

        # Process each top-level key
        for key, value in config.items():
            process_value(key, value)

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value.

        Args:
            key: Configuration key (supports dot notation)
            default: Default value if key not found

        Returns:
            Configuration value

        Example:
            >>> config.get("database.url", "sqlite:///db.sqlite3")
        """
        # Normalize key
        norm_key = self._normalize_key(key)

        # Check if key exists directly
        if norm_key in self._values:
            return self._values[norm_key].value

        # Handle dot notation
        parts = norm_key.split(".")
        if len(parts) > 1:
            # Try each part of the path
            current = self.to_dict()
            try:
                for part in parts:
                    current = current[part]
                return current
            except (KeyError, TypeError):
                pass

        return default

    def get_source(self, key: str) -> Optional[ConfigSource]:
        """Get the source of a configuration value.

        Args:
            key: Configuration key (supports dot notation)

        Returns:
            Source of the configuration value or None if not found

        Example:
            >>> config.get_source("database.url")
            ConfigSource.ENV
        """
        # Normalize key
        norm_key = self._normalize_key(key)

        # Check if key exists directly
        if norm_key in self._values:
            return self._values[norm_key].source

        # Handle dot notation
        if "." in norm_key:
            # For now, we don't track sources for nested values
            # If a value exists, assume it came from a direct source
            if self.get(key) is not None:
                return ConfigSource.DIRECT

        return None

    def set(
        self, key: str, value: Any, source: ConfigSource = ConfigSource.DIRECT
    ) -> None:
        """Set configuration value.

        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
            source: Source of the value

        Example:
            >>> config.set("database.url", "postgres://localhost/db")
        """
        # Normalize key
        norm_key = self._normalize_key(key)

        # Find schema for this key if available
        schema = None
        if self._schema and "properties" in self._schema:
            # Check if key exists directly in schema
            if norm_key in self._schema["properties"]:
                schema = self._schema["properties"][norm_key]

            # Check if it's a nested key
            elif "." in norm_key:
                parts = norm_key.split(".")
                current_schema = self._schema

                # Navigate through the schema
                for i, part in enumerate(parts):
                    # Current level properties
                    props = current_schema.get("properties", {})

                    if part in props:
                        # Found the property
                        if i == len(parts) - 1:
                            # Last part, this is our schema
                            schema = props[part]
                        else:
                            # Navigate deeper
                            current_schema = props[part]
                    else:
                        # Not found
                        break

        # Create config value
        config_value = ConfigValue(value, source, schema)

        # Validate value against schema
        if schema:
            config_value.validate()

        # Store value
        self._values[norm_key] = config_value

        # If dot notation, we also need to handle the nested structure
        if "." in norm_key:
            parts = norm_key.split(".")
            self._update_nested(parts, value)

    def _update_nested(self, parts: List[str], value: Any) -> None:
        """Update nested configuration structure.

        Args:
            parts: Key parts
            value: Value to set
        """
        # Convert flat keys to nested dict
        result = {}
        current = result

        # Build nested dict
        for i, part in enumerate(parts):
            if i == len(parts) - 1:
                # Last part, set value
                current[part] = value
            else:
                # Intermediate part, create dict
                current[part] = {}
                current = current[part]

    def update(
        self, config: Dict[str, Any], source: ConfigSource = ConfigSource.DIRECT
    ) -> None:
        """Update configuration with dictionary.

        Args:
            config: Configuration dictionary to merge
            source: Source of the values

        Example:
            >>> config.update({"debug": True, "api": {"timeout": 30}})
        """
        self._load_from_dict(config, source)

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary.

        Returns:
            Configuration dictionary

        Example:
            >>> config_dict = config.to_dict()
            >>> print(config_dict["database"]["url"])
        """
        result = {}

        # Process all values
        for key, config_value in self._values.items():
            # Handle dot notation
            if "." in key:
                parts = key.split(".")

                # Navigate to the right place in the result
                current = result
                for i, part in enumerate(parts[:-1]):
                    if part not in current:
                        current[part] = {}
                    current = current[part]

                # Set the leaf value
                current[parts[-1]] = config_value.value
            else:
                # Simple key
                result[key] = config_value.value

        return result

    def __getitem__(self, key: str) -> Any:
        """Get configuration value using dictionary syntax.

        Args:
            key: Configuration key

        Returns:
            Configuration value

        Raises:
            KeyError: If key not found

        Example:
            >>> api_key = config["api_key"]
        """
        value = self.get(key)
        if value is None:
            raise KeyError(key)
        return value

    def __setitem__(self, key: str, value: Any) -> None:
        """Set configuration value using dictionary syntax.

        Args:
            key: Configuration key
            value: Value to set

        Example:
            >>> config["api_key"] = "new_key"
        """
        self.set(key, value)

    def __contains__(self, key: str) -> bool:
        """Check if key exists in configuration.

        Args:
            key: Configuration key

        Returns:
            True if key exists, False otherwise

        Example:
            >>> if "api_key" in config:
            ...     print("API key is configured")
        """
        return self.get(key) is not None

    def __iter__(self):
        """Iterate over configuration keys.

        Returns:
            Iterator over configuration keys

        Example:
            >>> for key in config:
            ...     print(key)
        """
        return iter(self.to_dict())

    def items(self):
        """Get configuration items.

        Returns:
            Iterator over (key, value) pairs

        Example:
            >>> for key, value in config.items():
            ...     print(f"{key}: {value}")
        """
        return self.to_dict().items()

    def keys(self):
        """Get configuration keys.

        Returns:
            Iterator over configuration keys

        Example:
            >>> for key in config.keys():
            ...     print(key)
        """
        return self.to_dict().keys()

    def values(self):
        """Get configuration values.

        Returns:
            Iterator over configuration values

        Example:
            >>> for value in config.values():
            ...     print(value)
        """
        return self.to_dict().values()


class ConfigRegistry:
    """Registry for configuration providers.

    This class manages a registry of configuration providers for different
    domains (like llm, embeddings, etc.), allowing domain-specific configuration
    to be accessed in a consistent way.
    """

    def __init__(self):
        """Initialize configuration registry."""
        self._registry: Dict[str, Config] = {}

    def register(self, domain: str, config: Config) -> None:
        """Register a configuration provider.

        Args:
            domain: Domain name (e.g., "llm", "embeddings")
            config: Configuration provider
        """
        self._registry[domain] = config

    def get(self, domain: str) -> Optional[Config]:
        """Get a configuration provider by domain.

        Args:
            domain: Domain name (e.g., "llm", "embeddings")

        Returns:
            Configuration provider or None if not found
        """
        return self._registry.get(domain)

    def get_or_create(self, domain: str, **kwargs: Any) -> Config:
        """Get a configuration provider by domain or create a new one.

        Args:
            domain: Domain name (e.g., "llm", "embeddings")
            **kwargs: Configuration options for new provider

        Returns:
            Configuration provider
        """
        if domain in self._registry:
            return self._registry[domain]

        # Create new config
        env_prefix = kwargs.pop("env_prefix", f"PEPPERPY_{domain.upper()}_")
        config = Config(env_prefix=env_prefix, **kwargs)

        # Register it
        self.register(domain, config)

        return config

    def list_domains(self) -> List[str]:
        """List all registered domains.

        Returns:
            List of domain names
        """
        return list(self._registry.keys())

    def load_from_file(
        self, file_path: Union[str, Path], domain: Optional[str] = None
    ) -> None:
        """Load configuration from file.

        Args:
            file_path: Path to configuration file
            domain: Optional domain to load into (if None, load into all domains)
        """
        # Load configuration from file
        root_config = Config(config_path=file_path)

        if domain:
            # Load into specific domain
            if domain not in self._registry:
                # Create new config
                self._registry[domain] = Config()

            # Update with values from file
            self._registry[domain].update(root_config.to_dict(), ConfigSource.FILE)
        else:
            # Check if the file has domain-specific sections
            config_dict = root_config.to_dict()

            for key, value in config_dict.items():
                if isinstance(value, dict):
                    # Treat top-level keys as domains
                    if key not in self._registry:
                        # Create new config
                        env_prefix = f"PEPPERPY_{key.upper()}_"
                        self._registry[key] = Config(env_prefix=env_prefix)

                    # Update with values from file
                    self._registry[key].update(value, ConfigSource.FILE)


# Global configuration registry
_registry = None


def get_config_registry() -> ConfigRegistry:
    """Get the global configuration registry.

    Returns:
        Global configuration registry
    """
    global _registry
    if _registry is None:
        _registry = ConfigRegistry()
    return _registry


@lru_cache(maxsize=128)
def get_domain_config(domain: str, **kwargs: Any) -> Config:
    """Get configuration for a specific domain.

    Args:
        domain: Domain name (e.g., "llm", "embeddings")
        **kwargs: Configuration options for new provider

    Returns:
        Domain-specific configuration
    """
    registry = get_config_registry()
    return registry.get_or_create(domain, **kwargs)


def load_config_from_file(
    file_path: Union[str, Path], domain: Optional[str] = None
) -> None:
    """Load configuration from file.

    Args:
        file_path: Path to configuration file
        domain: Optional domain to load into (if None, load into all domains)
    """
    registry = get_config_registry()
    registry.load_from_file(file_path, domain)


# Helper for creating typed configuration
def create_typed_config(config_cls: Type[T], **kwargs: Any) -> T:
    """Create a typed configuration instance.

    This function creates a configuration instance with the structure
    and defaults defined by a configuration class, validating the
    provided values against the class's type annotations.

    Args:
        config_cls: Configuration class with type annotations
        **kwargs: Configuration values

    Returns:
        Typed configuration instance

    Raises:
        ValidationError: If validation fails

    Example:
        >>> class DatabaseConfig:
        ...     host: str = "localhost"
        ...     port: int = 5432
        ...     user: str
        ...     password: str
        ...
        >>> db_config = create_typed_config(
        ...     DatabaseConfig,
        ...     user="admin",
        ...     password="secret"
        ... )
        >>> db_config.host  # "localhost" (default)
        >>> db_config.user  # "admin" (from kwargs)
    """
    # Create schema from class
    schema = ConfigSchema.from_class(config_cls)

    # Create configuration with schema validation
    config = Config(schema=schema.schema, **kwargs)

    # Create instance of config class
    instance = config_cls()

    # Set attributes from configuration
    for key, value in config.items():
        if hasattr(instance, key):
            setattr(instance, key, value)

    return instance


# Decorator for validated configuration
class validated_config:
    """Decorator for configuration validation.

    This decorator validates the configuration passed to a function or method,
    ensuring it conforms to the specified schema or class.

    Args:
        schema: JSON Schema or configuration class
        param_name: Name of the parameter to validate (default: "config")

    Example:
        >>> @validated_config(schema={"type": "object", "required": ["api_key"]})
        ... def process_api(config):
        ...     return config["api_key"]
        ...
        >>> process_api({"api_key": "123"})  # OK
        >>> process_api({})  # Raises ValidationError
    """

    def __init__(
        self, schema: Union[Dict[str, Any], Type[Any]], param_name: str = "config"
    ):
        """Initialize the decorator.

        Args:
            schema: JSON Schema or configuration class
            param_name: Name of the parameter to validate
        """
        self.param_name = param_name

        # Convert class to schema if needed
        if isinstance(schema, type):
            self.schema = ConfigSchema.from_class(schema).schema
        else:
            self.schema = schema

    def __call__(self, func):
        """Apply validation to the decorated function.

        Args:
            func: Function to decorate

        Returns:
            Decorated function
        """

        def wrapper(*args, **kwargs):
            """Wrapper function."""
            # Find configuration parameter
            config = None

            if self.param_name in kwargs:
                # Named parameter
                config = kwargs[self.param_name]
            elif len(args) > 0:
                # Get from signature
                import inspect

                sig = inspect.signature(func)
                param_names = list(sig.parameters.keys())

                if self.param_name in param_names:
                    idx = param_names.index(self.param_name)
                    if idx < len(args):
                        config = args[idx]

            # Validate configuration
            if config is not None:
                schema = ConfigSchema(self.schema)

                # Convert to dict if not already
                if not isinstance(config, dict):
                    try:
                        config_dict = vars(config)
                    except (TypeError, AttributeError):
                        config_dict = config
                else:
                    config_dict = config

                # Validate
                schema.validate(config_dict)

            return func(*args, **kwargs)

        # Copy metadata
        import functools

        return functools.wraps(func)(wrapper)
