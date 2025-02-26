"""
Core configuration module defining configuration management functionality.

This module provides the base classes and interfaces for managing configuration
throughout the PepperPy framework.
"""

import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, TypeVar

import yaml

from ..base import PepperComponent, Registry

T = TypeVar("T")


class ConfigSource(ABC):
    """Base class for configuration sources."""

    @abstractmethod
    def load(self) -> Dict[str, Any]:
        """Load configuration from the source."""
        pass

    @abstractmethod
    def save(self, config: Dict[str, Any]) -> None:
        """Save configuration to the source."""
        pass


class EnvVarConfigSource(ConfigSource):
    """Configuration source that loads from environment variables."""

    def __init__(self, prefix: str = "PEPPERPY_"):
        self.prefix = prefix

    def load(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        config = {}
        for key, value in os.environ.items():
            if key.startswith(self.prefix):
                config_key = key[len(self.prefix) :].lower()
                config[config_key] = value
        return config

    def save(self, config: Dict[str, Any]) -> None:
        """Save configuration to environment variables."""
        for key, value in config.items():
            env_key = f"{self.prefix}{key.upper()}"
            os.environ[env_key] = str(value)


class YamlConfigSource(ConfigSource):
    """Configuration source that loads from YAML files."""

    def __init__(self, path: Path):
        self.path = Path(path)

    def load(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.path.exists():
            return {}

        with open(self.path, "r") as f:
            return yaml.safe_load(f) or {}

    def save(self, config: Dict[str, Any]) -> None:
        """Save configuration to YAML file."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w") as f:
            yaml.safe_dump(config, f)


class ConfigManager(PepperComponent):
    """Manager for configuration sources and values."""

    def __init__(self, name: str = "config_manager"):
        super().__init__(name)
        self._sources: Dict[str, ConfigSource] = {}
        self._config: Dict[str, Any] = {}

    def initialize(self) -> None:
        """Initialize the configuration manager."""
        self._load_all_sources()
        super().initialize()

    def cleanup(self) -> None:
        """Cleanup configuration resources."""
        self._save_all_sources()
        super().cleanup()

    def add_source(self, name: str, source: ConfigSource) -> None:
        """Add a configuration source."""
        if name in self._sources:
            raise ValueError(f"Configuration source {name} already exists")
        self._sources[name] = source
        self._config.update(source.load())

    def remove_source(self, name: str) -> None:
        """Remove a configuration source."""
        if name in self._sources:
            source = self._sources[name]
            source.save(self._config)
            del self._sources[name]

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        self._config[key] = value

    def update(self, config: Dict[str, Any]) -> None:
        """Update multiple configuration values."""
        self._config.update(config)

    def _load_all_sources(self) -> None:
        """Load configuration from all sources."""
        for source in self._sources.values():
            self._config.update(source.load())

    def _save_all_sources(self) -> None:
        """Save configuration to all sources."""
        for source in self._sources.values():
            source.save(self._config)


class ConfigRegistry(Registry[ConfigSource]):
    """Registry for configuration sources."""

    pass


def create_default_config_manager() -> ConfigManager:
    """Create a default configuration manager with standard sources."""
    manager = ConfigManager()

    # Add environment variables source
    manager.add_source("env", EnvVarConfigSource())

    # Add default YAML config file source
    config_path = Path.home() / ".pepperpy" / "config.yaml"
    manager.add_source("yaml", YamlConfigSource(config_path))

    return manager
