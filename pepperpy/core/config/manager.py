"""Configuration manager for Pepperpy.

This module provides a configuration manager that handles loading, validation,
and access to configuration settings.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from pepperpy.core.base import ComponentBase, ComponentConfig
from pepperpy.core.models import BaseModel
from pepperpy.core.types import ComponentState
from pepperpy.utils.imports import lazy_import

if TYPE_CHECKING:
    from pepperpy.core.errors import ConfigError as ConfigurationError
    from pepperpy.core.errors import ValidationError
    from pepperpy.monitoring.metrics import Counter, Histogram, MetricsManager
else:
    ConfigurationError = lazy_import("pepperpy.core.errors", "ConfigError")
    ValidationError = lazy_import("pepperpy.core.errors", "ValidationError")
    Counter = lazy_import("pepperpy.monitoring.metrics", "Counter")
    Histogram = lazy_import("pepperpy.monitoring.metrics", "Histogram")
    MetricsManager = lazy_import("pepperpy.monitoring.metrics", "MetricsManager")

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class ConfigurationManager(ComponentBase, Generic[T]):
    """Manager for configuration."""

    def __init__(self, config_class: type[T]) -> None:
        """Initialize configuration manager.

        Args:
            config_class: Pydantic model class for configuration
        """
        config = ComponentConfig(name=self.__class__.__name__)
        super().__init__(config=config)
        self._config_class = config_class
        self._config: T | None = None
        self._metrics = MetricsManager.get_instance()
        self._file_reads: Counter | None = None
        self._file_read_errors: Counter | None = None
        self._validation_errors: Counter | None = None
        self._load_duration: Histogram | None = None
        self._save_duration: Histogram | None = None
        self._lock = asyncio.Lock()
        self._config_path: Path | None = None
        self._unexpected_errors: Counter | None = None
        self._successful_loads: Counter | None = None
        self._successful_saves: Counter | None = None
        self._save_errors: Counter | None = None
        self._successful_updates: Counter | None = None
        self._update_errors: Counter | None = None
        self._successful_validations: Counter | None = None

        logger.debug(
            "Initialized configuration manager with class %s",
            self._config_class.__name__ if self._config_class else "None",
        )

    @property
    def config(self) -> T:
        """Get the current configuration.

        Returns:
            Current configuration

        Raises:
            ConfigurationError: If configuration is not loaded
        """
        if self._config is None:
            raise ConfigurationError("Configuration not loaded")
        return self._config

    @property
    def config_path(self) -> Path | None:
        """Get the current configuration file path.

        Returns:
            Current configuration file path or None if not set
        """
        return self._config_path

    async def _increment_metric(self, metric: Counter | None) -> None:
        """Increment a metric counter if it exists.

        Args:
            metric: The metric to increment
        """
        if metric is not None:
            await metric.inc(1)

    async def _load_from_file(self, config_path: Path) -> dict[str, Any]:
        """Load configuration data from file.

        Args:
            config_path: Path to configuration file

        Returns:
            Configuration data as dictionary

        Raises:
            ConfigurationError: If loading fails
        """
        try:
            if self.state != ComponentState.READY:
                raise ConfigurationError("Configuration manager not ready")

            async with self._lock:
                config_data = await asyncio.to_thread(config_path.read_text)
                await self._increment_metric(self._file_reads)
                data = json.loads(config_data)
                config = self._config_class.model_validate(data)
                return config.__dict__
        except OSError as e:
            await self._increment_metric(self._file_read_errors)
            raise ConfigurationError(
                f"Failed to read configuration file: {e}",
                details={"path": str(config_path)},
            ) from e
        except ValidationError as e:
            await self._increment_metric(self._validation_errors)
            raise ConfigurationError(
                f"Invalid configuration data: {e}",
                details={"path": str(config_path), "errors": str(e)},
            ) from e
        except Exception as e:
            await self._increment_metric(self._unexpected_errors)
            raise ConfigurationError(
                f"Unexpected error loading configuration: {e}"
            ) from e

    async def load(self, config_path: Path) -> T:
        """Load configuration from file.

        Args:
            config_path: Path to configuration file

        Returns:
            Loaded configuration

        Raises:
            ConfigurationError: If loading fails
        """
        try:
            if self.state != ComponentState.READY:
                raise ConfigurationError("Configuration manager not ready")

            async with self._lock:
                config_data = await asyncio.to_thread(config_path.read_text)
                await self._increment_metric(self._file_reads)
                data = json.loads(config_data)
                self._config = self._config_class.model_validate(data)
                self._config_path = config_path

                await self._increment_metric(self._successful_loads)

                if self._config is None:
                    raise ConfigurationError("Failed to load configuration")
                return self._config

        except OSError as e:
            await self._increment_metric(self._file_read_errors)
            raise ConfigurationError(
                f"Failed to read configuration file: {e}",
                details={"path": str(config_path)},
            ) from e
        except ValidationError as e:
            await self._increment_metric(self._validation_errors)
            raise ConfigurationError(
                f"Invalid configuration data: {e}",
                details={"path": str(config_path), "errors": str(e)},
            ) from e
        except Exception as e:
            await self._increment_metric(self._unexpected_errors)
            raise ConfigurationError(
                f"Unexpected error loading configuration: {e}"
            ) from e

    async def _initialize(self) -> None:
        """Initialize configuration manager.

        This method initializes the metrics used to track configuration operations.

        Raises:
            ConfigurationError: If initialization fails
        """
        try:
            await self.set_state(ComponentState.INITIALIZING)
            # Initialize metrics
            self._file_reads = await self._metrics.create_counter(
                "config_file_reads_total",
                "Total number of configuration file reads",
                labels={
                    "component_id": str(self._context.component_id),
                    "state": "ready",
                },
            )
            self._file_read_errors = await self._metrics.create_counter(
                "config_file_read_errors_total",
                "Total number of configuration file read errors",
                labels={
                    "component_id": str(self._context.component_id),
                    "state": "error",
                },
            )
            self._validation_errors = await self._metrics.create_counter(
                "config_validation_errors_total",
                "Total number of configuration validation errors",
                labels={
                    "component_id": str(self._context.component_id),
                    "state": "error",
                },
            )
            self._load_duration = await self._metrics.create_histogram(
                "config_load_duration_seconds",
                "Time taken to load configuration files",
                labels={
                    "component_id": str(self._context.component_id),
                    "state": "ready",
                },
            )
            self._save_duration = await self._metrics.create_histogram(
                "config_save_duration_seconds",
                "Time taken to save configuration files",
                labels={
                    "component_id": str(self._context.component_id),
                    "state": "ready",
                },
            )
            self._unexpected_errors = await self._metrics.create_counter(
                name="config_unexpected_errors_total",
                description="Total number of unexpected configuration errors",
            )
            self._successful_loads = await self._metrics.create_counter(
                name="config_successful_loads_total",
                description="Total number of successful configuration loads",
            )
            self._successful_saves = await self._metrics.create_counter(
                name="config_successful_saves_total",
                description="Total number of successful configuration saves",
            )
            self._save_errors = await self._metrics.create_counter(
                name="config_save_errors_total",
                description="Total number of configuration save errors",
            )
            self._successful_updates = await self._metrics.create_counter(
                name="config_successful_updates_total",
                description="Total number of successful configuration updates",
            )
            self._update_errors = await self._metrics.create_counter(
                name="config_update_errors_total",
                description="Total number of configuration update errors",
            )
            self._successful_validations = await self._metrics.create_counter(
                name="config_successful_validations_total",
                description="Total number of successful configuration validations",
            )
            await self.set_state(ComponentState.READY)
        except Exception as e:
            await self.set_state(ComponentState.ERROR)
            logger.error("Failed to initialize configuration manager: %s", str(e))
            raise ConfigurationError(f"Failed to initialize configuration manager: {e}")

    async def _execute(self, **kwargs: Any) -> Any:
        """Execute configuration manager functionality.

        This method is not used directly but is required by ComponentBase.
        """
        pass

    async def _cleanup(self) -> None:
        """Clean up configuration manager resources."""
        self._config = None
        self._file_reads = None
        self._file_read_errors = None
        self._validation_errors = None
        self._load_duration = None
        self._save_duration = None

    async def save(self, path: Path | None = None) -> None:
        """Save current configuration to file.

        Args:
            path: Optional path to save configuration to

        Raises:
            ConfigurationError: If saving fails
        """
        if self._config is None:
            raise ConfigurationError("No configuration to save")

        try:
            save_path = path or self._config_path
            if save_path is None:
                raise ConfigurationError("No path specified for saving configuration")

            config_data = json.dumps(self._config.__dict__, indent=2)
            save_path.write_text(config_data)

            if self._successful_saves is not None:
                await self._successful_saves.inc(1)

        except Exception as e:
            if self._save_errors is not None:
                await self._save_errors.inc(1)
            raise ConfigurationError(f"Failed to save configuration: {e}") from e

    async def update(self, updates: dict[str, Any]) -> T:
        """Update current configuration.

        Args:
            updates: Dictionary of configuration updates

        Returns:
            Updated configuration

        Raises:
            ConfigurationError: If update fails
        """
        if self._config is None:
            raise ConfigurationError("No configuration to update")

        try:
            config_data = self._config.__dict__.copy()
            config_data.update(updates)
            config = self._config_class.model_validate(config_data)
            self._config = config

            if self._successful_updates is not None:
                await self._successful_updates.inc(1)

            return config

        except Exception as e:
            if self._update_errors is not None:
                await self._update_errors.inc(1)
            raise ConfigurationError(f"Failed to update configuration: {e}") from e

    async def validate(self) -> None:
        """Validate current configuration.

        Raises:
            ConfigurationError: If validation fails
        """
        if self._config is None:
            if self._validation_errors is not None:
                await self._validation_errors.inc(1)
            raise ConfigurationError("Configuration not initialized")

        try:
            # Pydantic model validation is automatic
            # Add any additional validation here
            if self._successful_validations is not None:
                await self._successful_validations.inc(1)
            pass
        except Exception as e:
            if self._validation_errors is not None:
                await self._validation_errors.inc(1)
            raise ConfigurationError(f"Configuration validation failed: {e}") from e
