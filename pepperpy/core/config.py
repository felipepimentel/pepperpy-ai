"""Configuration module for PepperPy.

This module provides configuration management functionality.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml

from pepperpy.core.utils import merge_configs, unflatten_dict, validate_type

from .validation import ValidationError

logger = logging.getLogger(__name__)


class Config:
    """Configuration management class.

    This class handles loading, validating, and accessing configuration values
    from various sources including files, environment variables, and defaults.

    Args:
        config_path: Optional path to config file
        env_prefix: Optional prefix for environment variables
        defaults: Optional default configuration values
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
        config_path: Optional[Union[str, Path]] = None,
        env_prefix: str = "",
        defaults: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize configuration.

        Args:
            config_path: Optional path to config file
            env_prefix: Optional prefix for environment variables
            defaults: Optional default configuration values
            **kwargs: Additional configuration values

        Raises:
            ValidationError: If config file is invalid
        """
        self._config: Dict[str, Any] = {}
        self._env_prefix = env_prefix

        # Load defaults
        if defaults:
            validate_type(defaults, dict)
            self._config.update(defaults)

        # Load from file
        if config_path:
            self._load_file(config_path)

        # Load from environment
        self._load_env()

        # Load from kwargs
        self._config.update(kwargs)

    def _load_file(self, path: Union[str, Path]) -> None:
        """Load configuration from file.

        Args:
            path: Path to configuration file

        Raises:
            ValidationError: If file is invalid or cannot be read
        """
        try:
            path = Path(path)
            if not path.exists():
                raise ValidationError(f"Config file not found: {path}")

            with open(path) as f:
                config = yaml.safe_load(f)

            if not isinstance(config, dict):
                raise ValidationError("Config file must contain a dictionary")

            self._config.update(config)

        except Exception as e:
            raise ValidationError(f"Failed to load config file: {e}")

    def _load_env(self) -> None:
        """Load configuration from environment variables.

        Environment variables are converted from uppercase with underscores
        to lowercase with dots. For example:
            APP_DATABASE_URL -> database.url
        """
        if not self._env_prefix:
            return

        prefix = self._env_prefix.rstrip("_").upper() + "_"
        env_config = {}

        for key, value in os.environ.items():
            if key.startswith(prefix):
                # Convert APP_DATABASE_URL to database.url
                config_key = key[len(prefix) :].lower().replace("_", ".")
                env_config[config_key] = value

        # Update config with flattened env vars
        if env_config:
            self._config.update(unflatten_dict(env_config))

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
        try:
            current = self._config
            for part in key.split("."):
                current = current[part]
            return current
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any) -> None:
        """Set configuration value.

        Args:
            key: Configuration key (supports dot notation)
            value: Value to set

        Example:
            >>> config.set("database.url", "postgres://localhost/db")
        """
        config = unflatten_dict({key: value})
        self._config = merge_configs(self._config, config)

    def update(self, config: Dict[str, Any]) -> None:
        """Update configuration with dictionary.

        Args:
            config: Configuration dictionary to merge

        Example:
            >>> config.update({"debug": True, "api": {"timeout": 30}})
        """
        validate_type(config, dict)
        self._config = merge_configs(self._config, config)

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary.

        Returns:
            Configuration dictionary

        Example:
            >>> config_dict = config.to_dict()
            >>> print(config_dict["database"]["url"])
        """
        return dict(self._config)

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
