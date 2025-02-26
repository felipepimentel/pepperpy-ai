"""Core exception classes for the pepperpy framework."""


class PepperError(Exception):
    """Base exception class for all pepperpy errors."""

    pass


class ConfigurationError(PepperError):
    """Raised when there is an error in configuration."""

    pass


class ValidationError(PepperError):
    """Raised when validation fails."""

    pass


class CommunicationError(PepperError):
    """Raised when there is an error in service communication."""

    pass


class ServiceError(PepperError):
    """Raised when there is an error in service operation."""

    pass


class NotFoundError(PepperError):
    """Raised when a requested resource is not found."""

    pass


class AuthenticationError(PepperError):
    """Raised when authentication fails."""

    pass


class AuthorizationError(PepperError):
    """Raised when authorization fails."""

    pass


class TimeoutError(PepperError):
    """Raised when an operation times out."""

    pass


class StateError(PepperError):
    """Raised when an operation fails due to invalid state."""

    pass


class ResourceError(PepperError):
    """Raised when there is an error with system resources."""

    pass


class DependencyError(PepperError):
    """Raised when there is an error with dependencies."""

    pass


class ComponentError(PepperError):
    """Raised when there is an error with a component."""

    pass


__all__ = [
    "AuthenticationError",
    "AuthorizationError",
    "CommunicationError",
    "ComponentError",
    "ConfigurationError",
    "DependencyError",
    "NotFoundError",
    "PepperError",
    "ResourceError",
    "ServiceError",
    "StateError",
    "TimeoutError",
    "ValidationError",
]
