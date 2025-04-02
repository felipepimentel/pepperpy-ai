"""Core components for PepperPy framework."""

from pepperpy.core.base import (
    BaseComponent,
    PepperpyError,
)
from pepperpy.core.config import Config, ConfigurationError
from pepperpy.core.errors import PluginError
from pepperpy.core.logging import get_logger
from pepperpy.plugins.manager import PluginInfo, create_provider_instance

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
    "create_provider_instance",
    # Logging
    "get_logger",
]
