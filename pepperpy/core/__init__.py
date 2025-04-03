"""Core components for PepperPy framework."""

from pepperpy.core.base import (
    BaseComponent,
    PepperpyError,
)
from pepperpy.core.config import Config, ConfigurationError
from pepperpy.core.errors import PluginError, ValidationError
from pepperpy.core.logging import get_logger
from pepperpy.plugins.registry import PluginInfo

__all__ = [
    # Base classes
    "BaseComponent",
    "PepperpyError",
    # Configuration
    "Config",
    "ConfigurationError",
    # Plugin system
    "PluginError",
    "PluginInfo",
    # Validation
    "ValidationError",
    # Logging
    "get_logger",
]
