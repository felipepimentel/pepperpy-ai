"""Configuration source implementations."""

import json
import os
from abc import ABC, abstractmethod
from argparse import ArgumentParser
from pathlib import Path
from typing import Any

import yaml

from .base import ConfigurationError


class ConfigSource(ABC):
    """Base class for configuration sources."""

    @abstractmethod
    async def load(self) -> dict[str, Any]:
        """Load configuration data.

        Returns:
            Configuration data dictionary

        Raises:
            ConfigurationError: If loading fails

        """
        pass


class EnvSource(ConfigSource):
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


class FileSource(ConfigSource):
    """Base class for file-based configuration sources."""

    def __init__(self, path: str | Path) -> None:
        """Initialize the source.

        Args:
            path: Path to configuration file

        """
        self.path = Path(path)

    @abstractmethod
    async def _parse_file(self, content: str) -> dict[str, Any]:
        """Parse file content into configuration dictionary.

        Args:
            content: File content

        Returns:
            Configuration data dictionary

        Raises:
            ConfigurationError: If parsing fails

        """
        pass

    async def load(self) -> dict[str, Any]:
        """Load configuration from file.

        Returns:
            Configuration data dictionary

        Raises:
            ConfigurationError: If file cannot be read or parsed

        """
        try:
            content = await self._read_file()
            return await self._parse_file(content)
        except Exception as e:
            raise ConfigurationError(
                f"Failed to load configuration from {self.path}: {e}"
            )

    async def _read_file(self) -> str:
        """Read file content.

        Returns:
            File content

        Raises:
            ConfigurationError: If file cannot be read

        """
        try:
            return self.path.read_text()
        except Exception as e:
            raise ConfigurationError(f"Failed to read {self.path}: {e}")


class YAMLSource(FileSource):
    """YAML file configuration source."""

    async def _parse_file(self, content: str) -> dict[str, Any]:
        """Parse YAML content.

        Args:
            content: YAML content

        Returns:
            Configuration data dictionary

        Raises:
            ConfigurationError: If YAML parsing fails

        """
        try:
            return yaml.safe_load(content) or {}
        except Exception as e:
            raise ConfigurationError(f"Failed to parse YAML: {e}")


class JSONSource(FileSource):
    """JSON file configuration source."""

    async def _parse_file(self, content: str) -> dict[str, Any]:
        """Parse JSON content.

        Args:
            content: JSON content

        Returns:
            Configuration data dictionary

        Raises:
            ConfigurationError: If JSON parsing fails

        """
        try:
            return json.loads(content)
        except Exception as e:
            raise ConfigurationError(f"Failed to parse JSON: {e}")


class CLISource(ConfigSource):
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
