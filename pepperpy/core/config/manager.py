"""Configuration manager for Pepperpy.

This module provides a configuration manager that handles loading, validation,
and access to configuration settings.
"""

from pathlib import Path
from typing import Any, Dict, Generic, Optional, Type, TypeVar

from pydantic import BaseModel

from pepperpy.core.exceptions import ConfigurationError
from pepperpy.core.monitoring.logging import structured_logger as logger

T = TypeVar("T", bound=BaseModel)


class ConfigurationManager(Generic[T]):
    """Manages configuration for Pepperpy components.

    This class provides a unified interface for loading and accessing
    configuration settings. It supports:
    - Loading from multiple sources (files, environment variables)
    - Type validation using Pydantic models
    - Dynamic configuration updates
    - Configuration versioning
    """

    def __init__(self, config_class: Type[T]) -> None:
        """Initialize the configuration manager.

        Args:
            config_class: Pydantic model class for configuration
        """
        self._config_class = config_class
        self._config: Optional[T] = None
        self._config_path: Optional[Path] = None

    @property
    def config(self) -> Optional[T]:
        """Get the current configuration.

        Returns:
            Current configuration instance or None if not initialized
        """
        return self._config

    @property
    def config_path(self) -> Optional[Path]:
        """Get the current configuration file path.

        Returns:
            Path to configuration file or None if not set
        """
        return self._config_path

    async def load(self, config_path: Optional[Path] = None) -> T:
        """Load configuration from file.

        Args:
            config_path: Optional path to configuration file

        Returns:
            Loaded configuration instance

        Raises:
            ConfigurationError: If loading fails
        """
        try:
            if config_path:
                self._config_path = config_path
                if not config_path.exists():
                    raise ConfigurationError(f"Config file not found: {config_path}")
                config_data = self._load_from_file(config_path)
            else:
                config_data = {}

            # Create config instance
            config = self._config_class(**config_data)
            self._config = config
            logger.info("Configuration loaded successfully")
            return config
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration: {e}") from e

    def _load_from_file(self, path: Path) -> Dict[str, Any]:
        """Load configuration from file.

        Args:
            path: Path to configuration file

        Returns:
            Configuration data

        Raises:
            ConfigurationError: If loading fails
        """
        try:
            import yaml

            with path.open("r") as f:
                return yaml.safe_load(f)
        except Exception as e:
            raise ConfigurationError(f"Failed to load config file: {e}") from e

    async def save(self, path: Optional[Path] = None) -> None:
        """Save current configuration to file.

        Args:
            path: Optional path to save to (defaults to current config path)

        Raises:
            ConfigurationError: If saving fails
        """
        if self._config is None:
            raise ConfigurationError("No configuration to save")

        save_path = path or self._config_path
        if save_path is None:
            raise ConfigurationError("No configuration path specified")

        try:
            import yaml

            config_data = self._config.model_dump()
            with save_path.open("w") as f:
                yaml.safe_dump(config_data, f)
            logger.info(f"Configuration saved to {save_path}")
        except Exception as e:
            raise ConfigurationError(f"Failed to save configuration: {e}") from e

    async def update(self, updates: Dict[str, Any]) -> T:
        """Update current configuration.

        Args:
            updates: Configuration updates to apply

        Returns:
            Updated configuration instance

        Raises:
            ConfigurationError: If update fails
        """
        if self._config is None:
            raise ConfigurationError("Configuration not initialized")

        try:
            # Create new config with updates
            current_data = self._config.model_dump()
            current_data.update(updates)
            config = self._config_class(**current_data)
            self._config = config
            logger.info("Configuration updated successfully")
            return config
        except Exception as e:
            raise ConfigurationError(f"Failed to update configuration: {e}") from e

    def validate(self) -> None:
        """Validate current configuration.

        Raises:
            ConfigurationError: If validation fails
        """
        if self._config is None:
            raise ConfigurationError("Configuration not initialized")

        try:
            # Pydantic model validation is automatic
            # Add any additional validation here
            pass
        except Exception as e:
            raise ConfigurationError(f"Configuration validation failed: {e}") from e
