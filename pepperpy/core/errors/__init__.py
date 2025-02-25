"""Core errors package.

This package provides error types used throughout the framework.
"""

from pepperpy.core.errors.unified import (
    AuthenticationError,
    AuthorizationError,
    ConfigError,
    ContentError,
    DuplicateError,
    ExtensionError,
    LifecycleError,
    NetworkError,
    NotFoundError,
    PepperError,
    ProviderError,
    ResourceError,
    SecurityError,
    StateError,
    ValidationError,
)

__all__ = [
    "AuthenticationError",
    "AuthorizationError",
    "ConfigError",
    "ContentError",
    "DuplicateError",
    "ExtensionError",
    "LifecycleError",
    "NetworkError",
    "NotFoundError",
    "PepperError",
    "ProviderError",
    "ResourceError",
    "SecurityError",
    "StateError",
    "ValidationError",
]
