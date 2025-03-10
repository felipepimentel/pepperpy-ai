"""Public interfaces for PepperPy Errors module.

This module provides a stable public interface for the errors functionality.
It exposes the core error types and utilities that are considered part
of the public API.
"""

from pepperpy.errors.core import (
    AuthenticationError,
    AuthorizationError,
    ConfigError,
    ConfigNotFoundError,
    ConfigValidationError,
    ImportError,
    NetworkError,
    NotFoundError,
    PepperPyError,
    ProviderError,
    RateLimitError,
    SerializationError,
    TimeoutError,
    ValidationError,
    convert_exception,
    wrap_exception,
)

# Re-export everything
__all__ = [
    # Base classes
    "PepperPyError",
    "ValidationError",
    "NotFoundError",
    "ConfigError",
    # Authentication and authorization
    "AuthenticationError",
    "AuthorizationError",
    # Network and communication
    "NetworkError",
    "TimeoutError",
    "RateLimitError",
    # Configuration
    "ConfigValidationError",
    "ConfigNotFoundError",
    # Utility
    "ProviderError",
    "SerializationError",
    "ImportError",
    # Functions
    "convert_exception",
    "wrap_exception",
]
