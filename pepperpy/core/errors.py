"""Error hierarchy for the PepperPy framework.

This module defines the base error classes used throughout the PepperPy framework.
All framework-specific errors should inherit from PepperPyError.
"""


class PepperPyError(Exception):
    """Base class for all errors in the PepperPy framework."""

    def __init__(self, message: str = "", *args, **kwargs):
        """Initialize the error with a message and optional context."""
        self.message = message
        self.context = kwargs
        super().__init__(message, *args)

    def __str__(self) -> str:
        """Return a string representation of the error."""
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            return f"{self.message} [{context_str}]"
        return self.message


class ValidationError(PepperPyError):
    """Raised when validation fails."""

    pass


class NotFoundError(PepperPyError):
    """Raised when a requested resource is not found."""

    pass


class ConfigError(PepperPyError):
    """Raised when there is an error in configuration."""

    pass


class ResourceError(PepperPyError):
    """Raised when there is an error with a resource."""

    pass


class InitializationError(PepperPyError):
    """Raised when initialization fails."""

    pass


class DisposalError(PepperPyError):
    """Raised when disposal fails."""

    pass


class TimeoutError(PepperPyError):
    """Raised when an operation times out."""

    pass


class ConcurrencyError(PepperPyError):
    """Raised when there is an error with concurrent operations."""

    pass


# Adicionando as classes de erro que estão sendo importadas mas não estão definidas
class NetworkError(PepperPyError):
    """Raised when there is a network-related error."""

    pass


class QueryError(PepperPyError):
    """Raised when there is an error with a query."""

    pass


class SchemaError(PepperPyError):
    """Raised when there is an error with a schema."""

    pass


class StorageError(PepperPyError):
    """Raised when there is an error with storage operations."""

    pass


class TransformError(PepperPyError):
    """Raised when there is an error during data transformation."""

    pass


class ProviderError(PepperPyError):
    """Raised when there is an error with a provider."""

    pass


class AuthenticationError(PepperPyError):
    """Raised when authentication fails."""

    pass


class RateLimitError(PepperPyError):
    """Raised when a rate limit is exceeded."""

    pass


class ServerError(PepperPyError):
    """Raised when a server error occurs."""

    pass
