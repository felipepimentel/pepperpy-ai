"""Configuration Module.

This module provides configuration management with validation and schema support.
It handles loading, validating, and accessing configuration from various sources.

Example:
    >>> from pepperpy.core.internal.config import Config
    >>> config = Config.from_file("config.yaml")
    >>> api_key = config.get("api_key")
"""

from typing import Any, Dict, Optional

import yaml

from .validation import ValidationError, ValidationSchema


class ConfigError(Exception):
    """Error raised for configuration issues.

    This error is raised when configuration operations fail, such as
    loading from file, validation, or accessing missing values.

    Example:
        >>> try:
        ...     config = Config.from_file("missing.yaml")
        ... except ConfigError as e:
        ...     print(f"Config error: {e}")
    """

    pass


class ConfigSchema(ValidationSchema):
    """Schema for configuration validation.

    This class extends ValidationSchema to provide configuration-specific
    validation rules and defaults.

    Example:
        >>> schema = ConfigSchema({
        ...     "api_key": {"type": str, "required": True},
        ...     "timeout": {"type": int, "default": 30}
        ... })
    """

    def __init__(self, schema: Dict[str, Any]):
        """Initialize the config schema.

        Args:
            schema: Schema definition
        """
        super().__init__(schema)


class Config:
    """Configuration management with validation.

    This class provides methods for loading, validating, and accessing
    configuration values from various sources.

    Args:
        data: Configuration data
        schema: Optional validation schema
        **kwargs: Additional configuration options

    Example:
        >>> config = Config({
        ...     "api_key": "secret",
        ...     "timeout": 30
        ... })
        >>> print(config.get("timeout"))  # 30
    """

    def __init__(
        self,
        data: Dict[str, Any],
        schema: Optional[ConfigSchema] = None,
        **kwargs: Any,
    ):
        """Initialize the configuration.

        Args:
            data: Configuration data
            schema: Optional validation schema
            **kwargs: Additional configuration options

        Raises:
            ConfigError: If validation fails
        """
        self._data = data
        self._schema = schema
        self._options = kwargs

        if schema:
            try:
                self._data = schema.validate(data)
            except ValidationError as e:
                raise ConfigError(f"Invalid configuration: {e}")

    @classmethod
    def from_file(
        cls,
        path: str,
        schema: Optional[ConfigSchema] = None,
        **kwargs: Any,
    ) -> "Config":
        """Load configuration from file.

        Args:
            path: Path to configuration file
            schema: Optional validation schema
            **kwargs: Additional configuration options

        Returns:
            Config instance

        Raises:
            ConfigError: If file cannot be loaded or validation fails

        Example:
            >>> config = Config.from_file(
            ...     "config.yaml",
            ...     schema=ConfigSchema({"api_key": str})
            ... )
        """
        try:
            with open(path) as f:
                data = yaml.safe_load(f)
            return cls(data, schema, **kwargs)
        except Exception as e:
            raise ConfigError(f"Failed to load config from {path}: {e}")

    def get(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        """Get configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value

        Example:
            >>> config = Config({"timeout": 30})
            >>> timeout = config.get("timeout", 60)
        """
        return self._data.get(key, default)

    def set(
        self,
        key: str,
        value: Any,
    ) -> None:
        """Set configuration value.

        Args:
            key: Configuration key
            value: Value to set

        Raises:
            ConfigError: If validation fails

        Example:
            >>> config = Config({})
            >>> config.set("timeout", 30)
        """
        if self._schema:
            try:
                data = {**self._data, key: value}
                self._data = self._schema.validate(data)
            except ValidationError as e:
                raise ConfigError(f"Invalid configuration: {e}")
        else:
            self._data[key] = value

    def update(
        self,
        data: Dict[str, Any],
    ) -> None:
        """Update configuration with new data.

        Args:
            data: Configuration data to update

        Raises:
            ConfigError: If validation fails

        Example:
            >>> config = Config({})
            >>> config.update({"timeout": 30, "retries": 3})
        """
        if self._schema:
            try:
                self._data = self._schema.validate({**self._data, **data})
            except ValidationError as e:
                raise ConfigError(f"Invalid configuration: {e}")
        else:
            self._data.update(data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary.

        Returns:
            Configuration data

        Example:
            >>> config = Config({"timeout": 30})
            >>> data = config.to_dict()
        """
        return dict(self._data)

    def __getitem__(self, key: str) -> Any:
        """Get configuration value by key.

        Args:
            key: Configuration key

        Returns:
            Configuration value

        Raises:
            KeyError: If key not found

        Example:
            >>> config = Config({"timeout": 30})
            >>> timeout = config["timeout"]
        """
        return self._data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        """Set configuration value by key.

        Args:
            key: Configuration key
            value: Value to set

        Raises:
            ConfigError: If validation fails

        Example:
            >>> config = Config({})
            >>> config["timeout"] = 30
        """
        self.set(key, value)

    def __contains__(self, key: str) -> bool:
        """Check if key exists in configuration.

        Args:
            key: Configuration key

        Returns:
            True if key exists, False otherwise

        Example:
            >>> config = Config({"timeout": 30})
            >>> "timeout" in config  # True
        """
        return key in self._data

    def __len__(self) -> int:
        """Get number of configuration items.

        Returns:
            Number of items

        Example:
            >>> config = Config({"timeout": 30, "retries": 3})
            >>> len(config)  # 2
        """
        return len(self._data)

    def __str__(self) -> str:
        """Get string representation.

        Returns:
            String representation of configuration

        Example:
            >>> config = Config({"timeout": 30})
            >>> str(config)  # "Config(items=1)"
        """
        return f"Config(items={len(self)})"

    def __repr__(self) -> str:
        """Get detailed string representation.

        Returns:
            Detailed string representation of configuration

        Example:
            >>> config = Config({"timeout": 30})
            >>> repr(config)  # Contains all configuration details
        """
        return (
            f"{self.__class__.__name__}("
            f"data={self._data}, "
            f"schema={self._schema}, "
            f"options={self._options})"
        )
