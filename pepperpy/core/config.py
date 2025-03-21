"""Configuration management for PepperPy.

This module provides configuration management functionality including:
- Loading configuration from various sources
- Environment variable handling
- Configuration validation
- Default configuration management
"""


import os
from pathlib import Path
from typing import Any, Dict, Optional

from pepperpy.utils.base import (
    flatten_dict,
    get_metadata_value,
    merge_configs,
    safe_import,
    unflatten_dict,
)


class Config:
    """Configuration manager for PepperPy.

    This class handles loading and managing configuration from various sources
    including environment variables, files, and default values.
    """

    def __init__(
        self,
        env_prefix: str = "PEPPERPY_",
        config_file: Optional[str] = None,
        **defaults: Any,
    ) -> None:
        """Initialize the configuration manager.

        Args:
            env_prefix: Prefix for environment variables
            config_file: Path to configuration file
            **defaults: Default configuration values
        """
        self.env_prefix = env_prefix
        self.config_file = Path(config_file) if config_file else None
        self.config: Dict[str, Any] = defaults.copy()
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from all sources."""
        # Load from file if specified
        if self.config_file and self.config_file.exists():
            self._load_from_file()

        # Load from environment variables
        self._load_from_env()

    def _load_from_file(self) -> None:
        """Load configuration from file."""
        if not self.config_file:
            return

        ext = self.config_file.suffix.lower()
        if ext == ".json":
            import json

            with open(self.config_file) as f:
                file_config = json.load(f)
        elif ext in (".yaml", ".yml"):
            yaml = safe_import("yaml")
            if yaml:
                with open(self.config_file) as f:
                    file_config = yaml.safe_load(f)
            else:
                file_config = {}
        else:
            file_config = {}

        self.config = merge_configs(self.config, file_config)

    def _load_from_env(self) -> None:
        """Load configuration from environment variables."""
        env_config = {}
        for key, value in os.environ.items():
            if key.startswith(self.env_prefix):
                config_key = key[len(self.env_prefix) :].lower()
                env_config[config_key] = value

        self.config = merge_configs(self.config, unflatten_dict(env_config))

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.

        Args:
            key: Configuration key (can use dot notation)
            default: Default value if key not found

        Returns:
            Configuration value
        """
        return get_metadata_value(self.config, key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value.

        Args:
            key: Configuration key (can use dot notation)
            value: Value to set
        """
        parts = key.split(".")
        target = self.config
        for part in parts[:-1]:
            target = target.setdefault(part, {})
        target[parts[-1]] = value

    def update(self, config: Dict[str, Any]) -> None:
        """Update configuration with new values.

        Args:
            config: New configuration values
        """
        self.config = merge_configs(self.config, config)

    def to_dict(self) -> Dict[str, Any]:
        """Get configuration as dictionary.

        Returns:
            Configuration dictionary
        """
        return self.config.copy()

    def to_env_dict(self) -> Dict[str, str]:
        """Get configuration as environment variables.

        Returns:
            Dictionary of environment variables
        """
        return {
            f"{self.env_prefix}{k.upper()}": str(v)
            for k, v in flatten_dict(self.config).items()
        }
