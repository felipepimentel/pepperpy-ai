"""Configuration source implementations.

This module provides a unified interface for loading configuration from different sources:
- Environment variables
- Files (YAML, JSON)
- Command line arguments
- Default values

Each source implements the ConfigSource protocol and can be used with the UnifiedConfig manager.
"""

import json
import os
from abc import abstractmethod
from argparse import ArgumentParser
from pathlib import Path
from typing import Any, Protocol, TypeVar, runtime_checkable

import yaml

from pepperpy.core.errors import ConfigError as ConfigurationError
from pepperpy.core.models import BaseModel

# Type variable for configuration models
ConfigT = TypeVar("ConfigT", bound=BaseModel)


@runtime_checkable
class ConfigSource(Protocol[ConfigT]):
    """Protocol for configuration sources."""

    @abstractmethod
    async def load(self) -> dict[str, Any]:
        """Load configuration data.

        Returns:
            Configuration data dictionary

        Raises:
            ConfigurationError: If loading fails
        """
        ...

    @abstractmethod
    async def save(self, config: ConfigT, path: Path | None = None) -> None:
        """Save configuration data.

        Args:
            config: Configuration to save
            path: Optional path to save to

        Raises:
            ConfigurationError: If saving fails
        """
        ...


class EnvSource(ConfigSource[ConfigT]):
    """Environment variable configuration source."""

    def __init__(self, prefix: str = "PEPPERPY_", case_sensitive: bool = True) -> None:
        """Initialize the source.

        Args:
            prefix: Environment variable prefix
            case_sensitive: Whether to preserve case in keys
        """
        self.prefix = prefix
        self.case_sensitive = case_sensitive

    async def load(self) -> dict[str, Any]:
        """Load configuration from environment variables.

        Returns:
            Configuration data dictionary
        """
        config = {}
        prefix_len = len(self.prefix)

        for key, value in os.environ.items():
            if key.startswith(self.prefix):
                config_key = key[prefix_len:]
                if not self.case_sensitive:
                    config_key = config_key.lower()
                config[config_key] = value

        return config

    async def save(self, config: ConfigT, path: Path | None = None) -> None:
        """Save configuration to environment variables.

        Args:
            config: Configuration to save
            path: Ignored for environment variables

        Raises:
            ConfigurationError: If saving fails
        """
        try:
            data = config.model_dump()
            for key, value in data.items():
                if isinstance(value, (str, int, float, bool)):
                    os.environ[f"{self.prefix}{key}"] = str(value)
        except Exception as e:
            raise ConfigurationError(f"Failed to save to environment: {e}")


class FileSource(ConfigSource[ConfigT]):
    """File-based configuration source."""

    def __init__(self, path: Path | None = None) -> None:
        """Initialize the source.

        Args:
            path: Optional default path for loading/saving
        """
        self.path = path

    async def load(self) -> dict[str, Any]:
        """Load configuration from file.

        Returns:
            Configuration data dictionary

        Raises:
            ConfigurationError: If loading fails
        """
        if not self.path:
            return {}

        try:
            if not self.path.exists():
                return {}

            content = self.path.read_text()
            if self.path.suffix in {".yml", ".yaml"}:
                return yaml.safe_load(content) or {}
            else:
                return json.loads(content)
        except Exception as e:
            raise ConfigurationError(f"Failed to load from {self.path}: {e}")

    async def save(self, config: ConfigT, path: Path | None = None) -> None:
        """Save configuration to file.

        Args:
            config: Configuration to save
            path: Optional path to save to (overrides default)

        Raises:
            ConfigurationError: If saving fails
        """
        save_path = path or self.path
        if not save_path:
            raise ConfigurationError("No path specified for saving")

        try:
            data = config.model_dump()
            if save_path.suffix in {".yml", ".yaml"}:
                save_path.write_text(yaml.dump(data))
            else:
                save_path.write_text(json.dumps(data, indent=2))
        except Exception as e:
            raise ConfigurationError(f"Failed to save to {save_path}: {e}")


class CLISource(ConfigSource[ConfigT]):
    """Command line argument configuration source."""

    def __init__(
        self,
        parser: ArgumentParser | None = None,
        prefix: str = "config_",
    ) -> None:
        """Initialize the source.

        Args:
            parser: Optional argument parser to use
            prefix: Prefix for configuration arguments
        """
        self.parser = parser or ArgumentParser()
        self.prefix = prefix
        self._args = None

    def add_argument(self, name: str, **kwargs: Any) -> None:
        """Add a configuration argument.

        Args:
            name: Argument name
            **kwargs: Argument parser parameters
        """
        self.parser.add_argument(f"--{self.prefix}{name}", **kwargs)

    async def load(self) -> dict[str, Any]:
        """Load configuration from command line arguments.

        Returns:
            Configuration data dictionary
        """
        if self._args is None:
            self._args = vars(self.parser.parse_args())

        config = {}
        prefix_len = len(self.prefix)

        for key, value in self._args.items():
            if key.startswith(self.prefix):
                config_key = key[prefix_len:]
                if value is not None:  # Only include set values
                    config[config_key] = value

        return config

    async def save(self, config: ConfigT, path: Path | None = None) -> None:
        """Save configuration to command line arguments.

        Args:
            config: Configuration to save
            path: Ignored for CLI arguments

        Raises:
            ConfigurationError: Always raises as CLI args are read-only
        """
        raise ConfigurationError("Cannot save to command line arguments")


__all__ = [
    "CLISource",
    "ConfigSource",
    "EnvSource",
    "FileSource",
]
