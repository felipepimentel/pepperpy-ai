"""Core configuration management module.

This module provides a unified configuration system with support for:
- Environment variables
- File-based configuration (YAML, JSON)
- Command line arguments
- Dynamic configuration updates
- Type safety and validation
"""

from .base import ConfigurationError, ConfigurationManager
from .sources import (
    CLISource,
    ConfigSource,
    EnvSource,
    FileSource,
    JSONSource,
    YAMLSource,
)
from .types import ConfigWatcher

__all__ = [
    "ConfigurationManager",
    "ConfigurationError",
    "ConfigSource",
    "EnvSource",
    "FileSource",
    "YAMLSource",
    "JSONSource",
    "CLISource",
    "ConfigWatcher",
]
