"""Core error types for the Pepperpy framework."""

from typing import Any


class PepperpyError(Exception):
    """Base class for all Pepperpy errors."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        """Initialize the error.

        Args:
            message: Error message
            **kwargs: Additional error context
        """
        super().__init__(message)
        self.message = message
        self.context = kwargs


class ValidationError(PepperpyError):
    """Raised when validation fails."""

    pass


class StateError(PepperpyError):
    """Raised when an operation is invalid for the current state."""

    pass


class ConfigurationError(PepperpyError):
    """Raised when there is a configuration error."""

    pass


class ProviderError(PepperpyError):
    """Raised when there is a provider-related error."""

    pass


class RuntimeError(PepperpyError):
    """Raised when there is a runtime error."""

    pass
