"""
Core errors package.

This package provides error handling functionality used throughout PepperPy.
"""

from .base import (
    AuthenticationError,
    ComponentError,
    ConfigurationError,
    ConnectionError,
    DuplicateError,
    EventError,
    InitializationError,
    NotFoundError,
    PepperError,
    PermissionError,
    ProviderError,
    ResourceError,
    SecurityError,
    StateError,
    ValidationError,
    WorkflowError,
    error_handler,
)

__all__ = [
    "PepperError",
    "ConfigurationError",
    "ValidationError",
    "ComponentError",
    "InitializationError",
    "StateError",
    "ProviderError",
    "ConnectionError",
    "AuthenticationError",
    "ResourceError",
    "NotFoundError",
    "DuplicateError",
    "SecurityError",
    "PermissionError",
    "EventError",
    "WorkflowError",
    "error_handler",
]
