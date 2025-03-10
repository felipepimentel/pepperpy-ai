"""PepperPy Core Module.

This module provides the core functionality of the PepperPy framework, including:
- Common types and utilities
- Core interfaces and protocols
- Base classes for providers and processors

The core module is the foundation of the PepperPy framework and is used by
all other modules.
"""

# Import directly from core.py to avoid circular imports
from pepperpy.core.core import (
    AuthenticationError,
    AuthorizationError,
    ConfigurationError,
    PepperPyError,
    RateLimitError,
    ResourceNotFoundError,
    ServiceUnavailableError,
    TimeoutError,
    ValidationError,
    ensure_dir,
    get_config_dir,
    get_data_dir,
    get_env_var,
    get_logger,
    get_output_dir,
    get_project_root,
)
from pepperpy.core.public import *

# Re-export everything
__all__ = [
    # Errors
    "PepperPyError",
    "ConfigurationError",
    "ValidationError",
    "ResourceNotFoundError",
    "AuthenticationError",
    "AuthorizationError",
    "TimeoutError",
    "RateLimitError",
    "ServiceUnavailableError",
    # Utility functions
    "get_logger",
    "get_env_var",
    "get_project_root",
    "get_config_dir",
    "get_data_dir",
    "get_output_dir",
    "ensure_dir",
]
