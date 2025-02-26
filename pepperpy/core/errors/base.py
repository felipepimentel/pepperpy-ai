"""
Core errors module defining error handling functionality.

This module provides base exception classes and error handling utilities used
throughout PepperPy.
"""

from typing import Any, Dict, Optional, Type


class PepperError(Exception):
    """Base class for all PepperPy exceptions."""

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = details or {}

    def __str__(self) -> str:
        if self.details:
            return f"{self.code}: {self.message} - {self.details}"
        return f"{self.code}: {self.message}"


class ConfigurationError(PepperError):
    """Raised when there is a configuration-related error."""

    pass


class ValidationError(PepperError):
    """Raised when validation fails."""

    pass


class ComponentError(PepperError):
    """Raised when there is an error with a component."""

    pass


class InitializationError(ComponentError):
    """Raised when component initialization fails."""

    pass


class StateError(ComponentError):
    """Raised when a component is in an invalid state."""

    pass


class ProviderError(PepperError):
    """Raised when there is an error with a service provider."""

    pass


class ConnectionError(ProviderError):
    """Raised when connection to a service fails."""

    pass


class AuthenticationError(ProviderError):
    """Raised when authentication with a service fails."""

    pass


class ResourceError(PepperError):
    """Raised when there is an error with a resource."""

    pass


class NotFoundError(ResourceError):
    """Raised when a resource is not found."""

    pass


class DuplicateError(ResourceError):
    """Raised when a resource already exists."""

    pass


class SecurityError(PepperError):
    """Raised when there is a security-related error."""

    pass


class PermissionError(SecurityError):
    """Raised when an operation is not permitted."""

    pass


class EventError(PepperError):
    """Raised when there is an error with event handling."""

    pass


class WorkflowError(PepperError):
    """Raised when there is an error in a workflow."""

    pass


def error_handler(error_type: Type[PepperError]):
    """Decorator to handle specific types of errors."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except error_type:
                # Log the error and possibly take recovery action
                raise

        return wrapper

    return decorator


# Export all types
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
