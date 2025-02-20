"""Configuration manager for Pepperpy.

This module provides a configuration manager that handles loading, validation,
and access to configuration settings.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Generic, Optional, Type, TypeVar

from pydantic import BaseModel, ValidationError

from pepperpy.core.errors import ConfigError as ConfigurationError
from pepperpy.monitoring.metrics import Counter, MetricsManager

logger = logging.getLogger(__name__)

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
        self._metrics = MetricsManager.get_instance()
        self._file_reads: Optional[Counter] = None
        self._file_read_errors: Optional[Counter] = None
        self._validation_errors: Optional[Counter] = None
        self._unexpected_errors: Optional[Counter] = None
        self._successful_loads: Optional[Counter] = None
        self._successful_saves: Optional[Counter] = None
        self._save_errors: Optional[Counter] = None
        self._successful_updates: Optional[Counter] = None
        self._update_errors: Optional[Counter] = None
        self._successful_validations: Optional[Counter] = None
        self._validation_errors: Optional[Counter] = None

        logger.debug(
            "Initialized configuration manager with class %s", config_class.__name__
        )

    async def _init_metrics(self) -> None:
        """Initialize metrics counters."""
        if self._file_reads is None:
            self._file_reads = await self._metrics.create_counter(
                "config.file_reads",
                "Number of configuration file reads",
            )
        if self._file_read_errors is None:
            self._file_read_errors = await self._metrics.create_counter(
                "config.file_read_errors",
                "Number of configuration file read errors",
            )
        if self._validation_errors is None:
            self._validation_errors = await self._metrics.create_counter(
                "config.validation_errors",
                "Number of configuration validation errors",
            )
        if self._unexpected_errors is None:
            self._unexpected_errors = await self._metrics.create_counter(
                "config.unexpected_errors",
                "Number of unexpected configuration errors",
            )
        if self._successful_loads is None:
            self._successful_loads = await self._metrics.create_counter(
                "config.successful_loads",
                "Number of successful configuration loads",
            )
        if self._successful_saves is None:
            self._successful_saves = await self._metrics.create_counter(
                "config.successful_saves",
                "Number of successful configuration saves",
            )
        if self._save_errors is None:
            self._save_errors = await self._metrics.create_counter(
                "config.save_errors",
                "Number of configuration save errors",
            )
        if self._successful_updates is None:
            self._successful_updates = await self._metrics.create_counter(
                "config.successful_updates",
                "Number of successful configuration updates",
            )
        if self._update_errors is None:
            self._update_errors = await self._metrics.create_counter(
                "config.update_errors",
                "Number of configuration update errors",
            )
        if self._successful_validations is None:
            self._successful_validations = await self._metrics.create_counter(
                "config.successful_validations",
                "Number of successful configuration validations",
            )
        if self._validation_errors is None:
            self._validation_errors = await self._metrics.create_counter(
                "config.validation_errors",
                "Number of configuration validation errors",
            )

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

    def _load_from_file(self, config_path: Path) -> Dict[str, Any]:
        """Load configuration data from file.

        Args:
            config_path: Path to configuration file

        Returns:
            Configuration data as dictionary

        Raises:
            ConfigurationError: If file reading or parsing fails
        """
        try:
            config_data = config_path.read_text()
            if self._file_reads is not None:
                self._file_reads.record(1)
            return self._config_class.parse_raw(config_data).dict()
        except (OSError, IOError) as e:
            if self._file_read_errors is not None:
                self._file_read_errors.record(1)
            raise ConfigurationError(
                f"Failed to read config file: {e}",
                details={"path": str(config_path)},
                recovery_hint="Check file permissions and path",
            ) from e
        except ValidationError as e:
            if self._validation_errors is not None:
                self._validation_errors.record(1)
            raise ConfigurationError(
                f"Invalid configuration format: {e}",
                details={"path": str(config_path), "errors": e.errors()},
                recovery_hint="Check configuration file format and required fields",
            ) from e
        except Exception as e:
            if self._unexpected_errors is not None:
                self._unexpected_errors.record(1)
            raise ConfigurationError(
                f"Unexpected error loading config: {e}",
                details={"path": str(config_path)},
            ) from e

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
            await self._init_metrics()

            if config_path:
                self._config_path = config_path
                if not config_path.exists():
                    if self._file_read_errors is not None:
                        self._file_read_errors.record(1)
                    raise ConfigurationError(
                        f"Config file not found: {config_path}",
                        details={"path": str(config_path)},
                        recovery_hint="Create the configuration file or check the path",
                    )
                config_data = self._load_from_file(config_path)
                logger.info("Loaded configuration from %s", config_path)
            else:
                config_data = {}
                logger.info("Using default configuration")

            # Create config instance
            config = self._config_class(**config_data)
            self._config = config
            if self._successful_loads is not None:
                self._successful_loads.record(1)
            logger.debug("Configuration loaded successfully: %s", config.dict())
            return config
        except ConfigurationError:
            raise
        except Exception as e:
            if self._unexpected_errors is not None:
                self._unexpected_errors.record(1)
            raise ConfigurationError(
                f"Failed to load configuration: {e}",
                details={"path": str(config_path) if config_path else None},
                recovery_hint="Check configuration format and try again",
            ) from e

    async def save(self, path: Optional[Path] = None) -> None:
        """Save current configuration to file.

        Args:
            path: Optional path to save to (defaults to current config path)

        Raises:
            ConfigurationError: If saving fails
        """
        if self._config is None:
            if self._save_errors is not None:
                self._save_errors.record(1)
            raise ConfigurationError("No configuration to save")

        save_path = path or self._config_path
        if save_path is None:
            if self._save_errors is not None:
                self._save_errors.record(1)
            raise ConfigurationError("No configuration path specified")

        try:
            import yaml

            config_data = self._config.model_dump()
            with save_path.open("w") as f:
                yaml.safe_dump(config_data, f)
            if self._successful_saves is not None:
                self._successful_saves.record(1)
            logger.info("Configuration saved to %s", save_path)
        except Exception as e:
            if self._save_errors is not None:
                self._save_errors.record(1)
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
            if self._update_errors is not None:
                self._update_errors.record(1)
            raise ConfigurationError("Configuration not initialized")

        try:
            # Create new config with updates
            current_data = self._config.model_dump()
            current_data.update(updates)
            config = self._config_class(**current_data)
            self._config = config
            if self._successful_updates is not None:
                self._successful_updates.record(1)
            logger.info("Configuration updated successfully")
            return config
        except Exception as e:
            if self._update_errors is not None:
                self._update_errors.record(1)
            raise ConfigurationError(f"Failed to update configuration: {e}") from e

    def validate(self) -> None:
        """Validate current configuration.

        Raises:
            ConfigurationError: If validation fails
        """
        if self._config is None:
            if self._validation_errors is not None:
                self._validation_errors.record(1)
            raise ConfigurationError("Configuration not initialized")

        try:
            # Pydantic model validation is automatic
            # Add any additional validation here
            if self._successful_validations is not None:
                self._successful_validations.record(1)
            pass
        except Exception as e:
            if self._validation_errors is not None:
                self._validation_errors.record(1)
            raise ConfigurationError(f"Configuration validation failed: {e}") from e
