"""Unified configuration system for Pepperpy.

This module provides a centralized configuration system with support for:
- Multiple configuration sources (env vars, files, CLI)
- Type-safe configuration with validation
- Dynamic configuration updates
- Configuration versioning
- Lifecycle hooks
- Metrics and monitoring
"""

import asyncio
from collections.abc import Callable
from enum import Enum
from pathlib import Path
from typing import Any, Generic, TypeVar, cast

from pepperpy.core.base import Lifecycle
from pepperpy.core.errors import ConfigError as ConfigurationError
from pepperpy.core.logging import get_logger
from pepperpy.core.models import BaseModel
from pepperpy.monitoring.metrics import Counter, Histogram, MetricsManager

from .sources import ConfigSource, EnvSource, FileSource

# Configure logging
logger = get_logger(__name__)

# Type variable for configuration models
ConfigT = TypeVar("ConfigT", bound=BaseModel)

# Default configuration paths
DEFAULT_CONFIG_PATHS = [
    Path.home() / ".pepper_hub/config.yml",
    Path.cwd() / ".pepper_hub/config.yml",
    Path.cwd() / "pepperpy.yml",
]


class ConfigState(Enum):
    """Configuration states."""

    UNINITIALIZED = "uninitialized"
    LOADING = "loading"
    READY = "ready"
    ERROR = "error"


class ConfigHook(Generic[ConfigT]):
    """Configuration hook for lifecycle events."""

    def __init__(
        self,
        callback: Callable[[ConfigT], None],
        source: str | None = None,
    ) -> None:
        """Initialize the hook.

        Args:
            callback: Hook callback function
            source: Optional source identifier
        """
        self.callback = callback
        self.source = source


class UnifiedConfig(Lifecycle, Generic[ConfigT]):
    """Unified configuration manager.

    This class provides a centralized way to manage configuration from multiple
    sources, with support for validation, updates, and lifecycle hooks.

    Type Args:
        ConfigT: Configuration model type (must be a Pydantic BaseModel)

    Attributes:
        config: Current configuration instance
        state: Current configuration state
        sources: Active configuration sources
    """

    def __init__(
        self,
        config_class: type[ConfigT],
        env_prefix: str = "PEPPERPY_",
    ) -> None:
        """Initialize the configuration manager.

        Args:
            config_class: Configuration model class to use
            env_prefix: Prefix for environment variables
        """
        super().__init__()
        self.config_class = config_class
        self.env_prefix = env_prefix
        self._config: ConfigT | None = None
        self._state = ConfigState.UNINITIALIZED
        self._sources: list[ConfigSource[ConfigT]] = []
        self._hooks: dict[str, list[ConfigHook[ConfigT]]] = {
            "on_load": [],
            "on_update": [],
            "on_error": [],
            "on_validate": [],
        }
        self._validation_rules: list[Callable[[ConfigT], list[str]]] = []
        self._lock = asyncio.Lock()

        # Metrics
        self._metrics = MetricsManager.get_instance()
        self._file_reads: Counter | None = None
        self._file_read_errors: Counter | None = None
        self._validation_errors: Counter | None = None
        self._load_duration: Histogram | None = None
        self._save_duration: Histogram | None = None
        self._successful_loads: Counter | None = None
        self._successful_saves: Counter | None = None
        self._successful_updates: Counter | None = None
        self._update_errors: Counter | None = None

    async def _initialize_metrics(self) -> None:
        """Initialize metrics collectors."""
        self._file_reads = await self._metrics.create_counter(
            name="config_file_reads_total",
            description="Total number of configuration file reads",
            labels={"component": "config"},
        )
        self._file_read_errors = await self._metrics.create_counter(
            name="config_file_read_errors_total",
            description="Total number of configuration file read errors",
            labels={"component": "config"},
        )
        self._validation_errors = await self._metrics.create_counter(
            name="config_validation_errors_total",
            description="Total number of configuration validation errors",
            labels={"component": "config"},
        )
        self._load_duration = await self._metrics.create_histogram(
            name="config_load_duration_seconds",
            description="Time taken to load configuration",
            labels={"component": "config"},
        )
        self._save_duration = await self._metrics.create_histogram(
            name="config_save_duration_seconds",
            description="Time taken to save configuration",
            labels={"component": "config"},
        )
        self._successful_loads = await self._metrics.create_counter(
            name="config_successful_loads_total",
            description="Total number of successful configuration loads",
            labels={"component": "config"},
        )
        self._successful_saves = await self._metrics.create_counter(
            name="config_successful_saves_total",
            description="Total number of successful configuration saves",
            labels={"component": "config"},
        )
        self._successful_updates = await self._metrics.create_counter(
            name="config_successful_updates_total",
            description="Total number of successful configuration updates",
            labels={"component": "config"},
        )
        self._update_errors = await self._metrics.create_counter(
            name="config_update_errors_total",
            description="Total number of configuration update errors",
            labels={"component": "config"},
        )

    @property
    def config(self) -> ConfigT | None:
        """Get current configuration."""
        return self._config

    @property
    def state(self) -> ConfigState:
        """Get current configuration state."""
        return self._state

    @property
    def sources(self) -> list[ConfigSource[ConfigT]]:
        """Get active configuration sources."""
        return self._sources.copy()

    async def initialize(self) -> None:
        """Initialize the configuration system.

        This method initializes metrics and loads initial configuration.

        Raises:
            ConfigurationError: If initialization fails
        """
        try:
            self._state = ConfigState.LOADING
            await self._initialize_metrics()

            # Add default sources
            self.add_source(EnvSource(prefix=self.env_prefix))

            # Load configuration from default paths
            for path in DEFAULT_CONFIG_PATHS:
                if path.exists():
                    self.add_source(FileSource(path))
                    break

            # Load initial configuration
            await self.reload()
            self._state = ConfigState.READY

        except Exception as e:
            self._state = ConfigState.ERROR
            raise ConfigurationError(f"Failed to initialize configuration: {e}")

    async def cleanup(self) -> None:
        """Clean up resources."""
        self._sources.clear()
        self._hooks.clear()
        self._config = None
        self._state = ConfigState.UNINITIALIZED

    async def reload(self) -> None:
        """Reload configuration from all sources.

        This method merges configuration from all sources in order
        and notifies watchers of changes.

        Raises:
            ConfigurationError: If reload fails
        """
        try:
            async with self._lock:
                # Collect configuration from all sources
                config_data: dict[str, Any] = {}
                for source in self._sources:
                    data = await source.load()
                    config_data.update(data)

                # Create new configuration
                old_config = self._config
                self._config = self.config_class.model_validate(config_data)

                # Run validation hooks
                await self._run_hooks("on_validate")

                # Run validation rules
                errors = []
                for rule in self._validation_rules:
                    try:
                        rule_errors = rule(self._config)
                        errors.extend(rule_errors)
                    except Exception as e:
                        errors.append(str(e))

                if errors:
                    if self._validation_errors:
                        await self._validation_errors.inc()
                    raise ConfigurationError(
                        "Configuration validation failed",
                        details={"errors": errors},
                    )

                # Notify hooks if configuration changed
                if old_config is not None and old_config != self._config:
                    await self._run_hooks("on_update")

                if self._successful_loads:
                    await self._successful_loads.inc()

        except Exception as e:
            if self._update_errors:
                await self._update_errors.inc()
            raise ConfigurationError(f"Failed to reload configuration: {e}")

    def add_source(self, source: ConfigSource[ConfigT]) -> None:
        """Add a configuration source.

        Sources are processed in order of addition.

        Args:
            source: Configuration source to add
        """
        self._sources.append(source)

    def remove_source(self, source: ConfigSource[ConfigT]) -> None:
        """Remove a configuration source.

        Args:
            source: Configuration source to remove
        """
        self._sources.remove(source)

    async def save(self, path: Path | None = None) -> None:
        """Save configuration to file.

        Args:
            path: Optional path to save to

        Raises:
            ConfigurationError: If saving fails
        """
        if not self._config:
            raise ConfigurationError("No configuration to save")

        try:
            # Find existing file source or create new one
            file_source: FileSource[ConfigT] | None = None
            for source in self._sources:
                if isinstance(source, FileSource):
                    file_source = cast(FileSource[ConfigT], source)
                    break

            if not file_source:
                if not path:
                    raise ConfigurationError(
                        "No file source available and no path provided"
                    )
                file_source = FileSource[ConfigT](path)
                self.add_source(file_source)

            # Save configuration (we know self._config is not None here)
            config = self._config
            await file_source.save(config, path)

            # Record metrics
            if self._successful_saves:
                await self._successful_saves.inc()

        except Exception as e:
            raise ConfigurationError(f"Failed to save configuration: {e}")

    async def update(self, updates: dict[str, Any]) -> None:
        """Update current configuration.

        Args:
            updates: Dictionary of configuration updates

        Raises:
            ConfigurationError: If update fails
        """
        if not self._config:
            raise ConfigurationError("No configuration to update")

        try:
            async with self._lock:
                # Create new config with updates
                config_dict = self._config.model_dump()
                config_dict.update(updates)
                new_config = self.config_class.model_validate(config_dict)

                # Update and notify
                self._config = new_config
                if self._successful_updates:
                    await self._successful_updates.inc()
                await self._run_hooks("on_update")

        except Exception as e:
            if self._update_errors:
                await self._update_errors.inc()
            raise ConfigurationError(f"Failed to update configuration: {e}")

    async def validate(self) -> list[str]:
        """Validate the current configuration.

        Returns:
            List of validation error messages

        Raises:
            ConfigurationError: If validation fails
        """
        if not self._config:
            return ["No configuration loaded"]

        errors = []

        try:
            # Run validation hooks
            await self._run_hooks("on_validate")

            # Run validation rules
            for rule in self._validation_rules:
                try:
                    rule_errors = rule(self._config)
                    errors.extend(rule_errors)
                except Exception as e:
                    errors.append(str(e))

            return errors

        except Exception as e:
            if self._validation_errors:
                await self._validation_errors.inc()
            raise ConfigurationError(f"Configuration validation failed: {e}")

    async def _run_hooks(self, event: str) -> None:
        """Run configuration hooks for an event.

        Args:
            event: Event name
        """
        if not self._config:
            return

        for hook in self._hooks.get(event, []):
            try:
                await asyncio.to_thread(hook.callback, self._config)
            except Exception as e:
                logger.error("Hook %s failed: %s", hook.source or "unknown", e)
                await self._run_hooks("on_error")


__all__ = [
    "ConfigHook",
    "ConfigState",
    "UnifiedConfig",
]
