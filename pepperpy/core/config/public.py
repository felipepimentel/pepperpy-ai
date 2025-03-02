"""Public Interface for Configuration Management

This module provides a stable public interface for the configuration management system.
It exposes the core configuration abstractions and implementations that are
considered part of the public API.

Core Components:
    ConfigManager: Configuration management system
    ConfigProvider: Base class for configuration providers
    ConfigSection: Configuration section
    ConfigValue: Configuration value
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pepperpy.core.protocols.base import Lifecycle


class ConfigProvider:
    """Base class for configuration providers.

    This class defines the interface for configuration providers,
    which are responsible for loading configuration from various sources.
    """

    def __init__(self, name: str):
        """Initialize the configuration provider.

        Args:
            name: Provider name
        """
        self.name = name

    async def load(self) -> Dict[str, Any]:
        """Load configuration from the provider.

        Returns:
            Dictionary containing configuration values

        Raises:
            NotImplementedError: If the subclass does not implement this method
        """
        raise NotImplementedError("Subclasses must implement load method")


class ConfigSection:
    """Configuration section.

    This class represents a section of configuration values,
    providing a namespace for related settings.
    """

    def __init__(self, name: str, values: Optional[Dict[str, Any]] = None):
        """Initialize the configuration section.

        Args:
            name: Section name
            values: Initial values
        """
        self.name = name
        self.values = values or {}

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.

        Args:
            key: Configuration key
            default: Default value if key doesn't exist

        Returns:
            Configuration value or default
        """
        return self.values.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value.

        Args:
            key: Configuration key
            value: Configuration value
        """
        self.values[key] = value

    def as_dict(self) -> Dict[str, Any]:
        """Get the section as a dictionary.

        Returns:
            Dictionary containing section values
        """
        return self.values.copy()


class ConfigManager(Lifecycle):
    """Configuration management system.

    This class provides a unified interface for accessing and managing
    configuration settings from various sources.
    """

    def __init__(self):
        """Initialize the configuration manager."""
        self.providers: List[ConfigProvider] = []
        self.sections: Dict[str, ConfigSection] = {}

    async def initialize(self) -> None:
        """Initialize the configuration manager.

        This method loads configurations from default sources and
        prepares the manager for use.

        Raises:
            ConfigurationError: If initialization fails
        """
        # Load from registered providers
        for provider in self.providers:
            config = await provider.load()
            for section_name, section_values in config.items():
                if section_name not in self.sections:
                    self.sections[section_name] = ConfigSection(section_name)

                for key, value in section_values.items():
                    self.sections[section_name].set(key, value)

    async def cleanup(self) -> None:
        """Clean up configuration resources.

        This method releases any resources used by the configuration manager.
        """
        self.providers.clear()
        self.sections.clear()

    def register_provider(self, provider: ConfigProvider) -> None:
        """Register a configuration provider.

        Args:
            provider: Configuration provider
        """
        self.providers.append(provider)

    async def load_from_file(self, file_path: Union[str, Path]) -> None:
        """Load configuration from a file.

        Args:
            file_path: Path to the configuration file

        Raises:
            FileNotFoundError: If the file doesn't exist
            ConfigurationError: If the file format is invalid
        """
        # Implementation would load from file
        pass

    async def load_from_env(self, prefix: Optional[str] = None) -> None:
        """Load configuration from environment variables.

        Args:
            prefix: Optional prefix for environment variables
        """
        # Implementation would load from environment
        pass

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.

        Args:
            key: Configuration key in format "section.key"
            default: Default value if key doesn't exist

        Returns:
            Configuration value or default
        """
        if "." not in key:
            return default

        section_name, key_name = key.split(".", 1)
        section = self.sections.get(section_name)

        if not section:
            return default

        return section.get(key_name, default)

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value.

        Args:
            key: Configuration key in format "section.key"
            value: Configuration value

        Raises:
            ValueError: If key format is invalid
        """
        if "." not in key:
            raise ValueError("Key must be in format 'section.key'")

        section_name, key_name = key.split(".", 1)

        if section_name not in self.sections:
            self.sections[section_name] = ConfigSection(section_name)

        self.sections[section_name].set(key_name, value)

    def get_section(self, section: str) -> Dict[str, Any]:
        """Get a configuration section.

        Args:
            section: Section name

        Returns:
            Dictionary containing section configuration
        """
        section_obj = self.sections.get(section)

        if not section_obj:
            return {}

        return section_obj.as_dict()


# Export public classes
__all__ = [
    "ConfigManager",
    "ConfigProvider",
    "ConfigSection",
]
