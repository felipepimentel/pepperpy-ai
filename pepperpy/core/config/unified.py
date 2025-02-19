"""Unified configuration system for Pepperpy.

This module provides a centralized configuration system with support for:
- Multiple configuration sources (env vars, files, CLI)
- Type-safe configuration with validation
- Dynamic configuration updates
- Configuration versioning
- Lifecycle hooks
"""

import os
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, Generic, List, Optional, Set, TypeVar

from pydantic import BaseModel

from pepperpy.core.base import Lifecycle
from pepperpy.core.errors import ConfigurationError
from pepperpy.core.logging import get_logger

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


class ConfigSource(Enum):
    """Available configuration sources."""

    ENV = "environment"
    FILE = "file"
    CLI = "cli"
    DEFAULT = "default"


class ConfigState(Enum):
    """Configuration states."""

    UNINITIALIZED = "uninitialized"
    LOADING = "loading"
    READY = "ready"
    ERROR = "error"
    UPDATING = "updating"


class ConfigHook(Generic[ConfigT]):
    """Configuration lifecycle hook."""

    def __init__(
        self,
        callback: Callable[[ConfigT], None],
        source: Optional[ConfigSource] = None,
    ) -> None:
        """Initialize the hook.

        Args:
            callback: Function to call when hook is triggered
            source: Optional source to restrict hook to

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
        self._config: Optional[ConfigT] = None
        self._state = ConfigState.UNINITIALIZED
        self._sources: Set[ConfigSource] = set()
        self._hooks: Dict[str, List[ConfigHook[ConfigT]]] = {
            "on_load": [],
            "on_update": [],
            "on_error": [],
        }

    @property
    def config(self) -> Optional[ConfigT]:
        """Get the current configuration."""
        return self._config

    @property
    def state(self) -> ConfigState:
        """Get the current configuration state."""
        return self._state

    @property
    def sources(self) -> Set[ConfigSource]:
        """Get the active configuration sources."""
        return self._sources.copy()

    async def initialize(self) -> None:
        """Initialize the configuration manager.

        This loads the initial configuration from all available sources.

        Raises:
            ConfigurationError: If initialization fails

        """
        try:
            self._state = ConfigState.LOADING

            # Load from default paths first
            config_dict = {}
            for path in DEFAULT_CONFIG_PATHS:
                if path.exists():
                    config_dict.update(self._load_from_file(path))
                    self._sources.add(ConfigSource.FILE)
                    break

            # Override with environment variables
            env_config = self._load_from_env()
            if env_config:
                config_dict.update(env_config)
                self._sources.add(ConfigSource.ENV)

            # Create and validate configuration
            self._config = self.config_class(**config_dict)

            # Run load hooks
            await self._run_hooks("on_load")

            self._state = ConfigState.READY
            logger.info(
                "Configuration initialized",
                extra={
                    "sources": [s.value for s in self._sources],
                    "config_type": self.config_class.__name__,
                },
            )

        except Exception as e:
            self._state = ConfigState.ERROR
            raise ConfigurationError(f"Failed to initialize configuration: {e}") from e

    async def update(self, updates: Dict[str, Any]) -> None:
        """Update the current configuration.

        Args:
            updates: Configuration updates to apply

        Raises:
            ConfigurationError: If update fails or validation fails

        """
        if not self._config:
            raise ConfigurationError("Configuration not initialized")

        try:
            self._state = ConfigState.UPDATING

            # Create new config with updates
            config_dict = self._config.model_dump()
            config_dict.update(updates)
            new_config = self.config_class(**config_dict)

            # Run update hooks
            self._config = new_config
            await self._run_hooks("on_update")

            self._state = ConfigState.READY
            logger.info(
                "Configuration updated",
                extra={"updates": list(updates.keys())},
            )

        except Exception as e:
            self._state = ConfigState.ERROR
            raise ConfigurationError(f"Failed to update configuration: {e}") from e

    def add_hook(
        self,
        event: str,
        callback: Callable[[ConfigT], None],
        source: Optional[ConfigSource] = None,
    ) -> None:
        """Add a configuration lifecycle hook.

        Args:
            event: Event to hook into ("on_load", "on_update", "on_error")
            callback: Function to call when event occurs
            source: Optional source to restrict hook to

        Raises:
            ValueError: If event is invalid

        """
        if event not in self._hooks:
            raise ValueError(f"Invalid hook event: {event}")

        hook = ConfigHook(callback, source)
        self._hooks[event].append(hook)

    def remove_hook(
        self,
        event: str,
        callback: Callable[[ConfigT], None],
    ) -> None:
        """Remove a configuration lifecycle hook.

        Args:
            event: Event to remove hook from
            callback: Callback to remove

        Raises:
            ValueError: If event is invalid

        """
        if event not in self._hooks:
            raise ValueError(f"Invalid hook event: {event}")

        self._hooks[event] = [h for h in self._hooks[event] if h.callback != callback]

    async def cleanup(self) -> None:
        """Clean up the configuration manager."""
        self._config = None
        self._state = ConfigState.UNINITIALIZED
        self._sources.clear()
        self._hooks.clear()

    def _load_from_file(self, path: Path) -> Dict[str, Any]:
        """Load configuration from a file.

        Args:
            path: Path to configuration file

        Returns:
            Configuration dictionary

        Raises:
            ConfigurationError: If file cannot be loaded

        """
        try:
            import yaml

            with path.open() as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            raise ConfigurationError(f"Failed to load config from {path}: {e}") from e

    def _load_from_env(self) -> Dict[str, Any]:
        """Load configuration from environment variables.

        Returns:
            Configuration dictionary

        """
        config: Dict[str, Any] = {}
        prefix_len = len(self.env_prefix)

        for key, value in os.environ.items():
            if not key.startswith(self.env_prefix):
                continue

            config_key = key[prefix_len:].lower()
            parts = config_key.split("__")

            # Handle nested configuration
            current = config
            for part in parts[:-1]:
                current = current.setdefault(part, {})

            # Convert value types
            if value.lower() in ("true", "false"):
                value = value.lower() == "true"
            elif value.isdigit():
                value = int(value)
            elif parts[-1] in ("timeout", "retry_delay"):
                value = float(value)

            current[parts[-1]] = value

        return config

    async def _run_hooks(self, event: str) -> None:
        """Run hooks for an event.

        Args:
            event: Event to run hooks for

        """
        if not self._config:
            return

        for hook in self._hooks[event]:
            if not hook.source or hook.source in self._sources:
                try:
                    hook.callback(self._config)
                except Exception as e:
                    logger.error(
                        f"Hook failed: {e}",
                        extra={
                            "event": event,
                            "source": hook.source.value if hook.source else None,
                        },
                    )
                    if event != "on_error":
                        await self._run_hooks("on_error")
