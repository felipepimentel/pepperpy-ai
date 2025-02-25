"""Configuration system for the Pepperpy framework.

This package provides a unified configuration system with support for:
- Multiple configuration providers (filesystem, environment variables)
- Configuration validation and type conversion
- Environment variable mapping
- Configuration file management
"""

from pepperpy.core.config.base import (
    ConfigManager,
    ConfigModel,
    ConfigProvider,
    config_manager,
)
from pepperpy.core.config.providers.env import EnvironmentProvider
from pepperpy.core.config.providers.filesystem import FilesystemProvider

# Register default providers
config_manager.add_provider(EnvironmentProvider())
config_manager.add_provider(FilesystemProvider(".config"))


__all__ = [
    "ConfigManager",
    "ConfigModel",
    "ConfigProvider",
    "EnvironmentProvider",
    "FilesystemProvider",
    "config_manager",
]
