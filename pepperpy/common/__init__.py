"""Common utilities and shared functionality for the Pepperpy system.

This package contains common utilities, configurations, error types, and shared
functionality used throughout the Pepperpy system. It provides:

- Configuration management and validation
- Error types and handling
- Common utilities and helper functions
"""

from pepperpy.common.config import AutoConfig, PepperpyConfig, ProviderConfig
from pepperpy.common.errors import (
    ConfigurationError,
    NotFoundError,
    PepperpyError,
    StateError,
)

__all__ = [
    "AutoConfig",
    "ConfigurationError",
    "NotFoundError",
    "PepperpyConfig",
    "PepperpyError",
    "ProviderConfig",
    "StateError",
]
