"""
Configuration management interface.

This module provides the public interface for the configuration management system.
"""

from pathlib import Path
from typing import Any, Dict, Optional, Union

from pepperpy.core.protocols.base import Lifecycle


class ConfigManager(Lifecycle):
    """Configuration management system.

    This class provides a unified interface for accessing and managing
    configuration settings from various sources.
    """

    async def initialize(self) -> None:
        """Initialize the configuration manager.

        This method loads configurations from default sources and
        prepares the manager for use.

        Raises:
            ConfigurationError: If initialization fails
        """
        pass

    async def cleanup(self) -> None:
        """Clean up configuration resources.

        This method releases any resources used by the configuration manager.
        """
        pass

    async def load_from_file(self, file_path: Union[str, Path]) -> None:
        """Load configuration from a file.

        Args:
            file_path: Path to the configuration file

        Raises:
            FileNotFoundError: If the file doesn't exist
            ConfigurationError: If the file format is invalid
        """
        pass

    async def load_from_env(self, prefix: Optional[str] = None) -> None:
        """Load configuration from environment variables.

        Args:
            prefix: Optional prefix for environment variables
        """
        pass

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.

        Args:
            key: Configuration key
            default: Default value if key doesn't exist

        Returns:
            Configuration value or default
        """
        pass

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value.

        Args:
            key: Configuration key
            value: Configuration value
        """
        pass

    def get_section(self, section: str) -> Dict[str, Any]:
        """Get a configuration section.

        Args:
            section: Section name

        Returns:
            Dictionary containing section configuration
        """
        pass
