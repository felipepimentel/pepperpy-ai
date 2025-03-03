"""Base interface for configuration providers."""

from abc import ABC, abstractmethod
from typing import Dict, Optional

from pepperpy.core.common.config.types import ConfigValue


class ConfigProvider(ABC):
    """Base class for configuration providers."""

    @abstractmethod
    def get(self, key: str) -> Optional[ConfigValue]:
        """Retrieve a configuration value by key."""

    @abstractmethod
    def set(self, key: str, value: ConfigValue) -> None:
        """Set a configuration value."""

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete a configuration value."""

    @abstractmethod
    def clear(self) -> None:
        """Clear all configuration values."""

    @abstractmethod
    def load(self) -> Dict[str, ConfigValue]:
        """Load all configuration values."""

    @abstractmethod
    def save(self) -> None:
        """Save all configuration values."""

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if a configuration key exists."""

    @abstractmethod
    def get_namespace(self, namespace: str) -> Dict[str, ConfigValue]:
        """Get all configuration values under a namespace."""
