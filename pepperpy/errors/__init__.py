"""PepperPy Errors Module.

This module provides error handling functionality for the PepperPy framework, including:
- Base exception classes for different error types
- Specific exceptions for common error scenarios
- Utilities for converting and wrapping exceptions

The errors module is designed to provide a consistent error handling approach
across the PepperPy framework, making it easier to understand and handle errors.
"""

from pepperpy.errors.public import *

"""Base error classes for the PepperPy framework."""


class PepperpyError(Exception):
    """Base exception class for PepperPy framework."""

    def __init__(self, message: str, status_code: int = 500):
        """Initialize the error.

        Args:
            message: Error message
            status_code: HTTP status code (default: 500)
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class PepperpyValueError(PepperpyError):
    """Exception raised for invalid values."""

    def __init__(self, message: str):
        """Initialize the error.

        Args:
            message: Error message
        """
        super().__init__(message, status_code=400)


class PepperpyTypeError(PepperpyError):
    """Exception raised for type errors."""

    def __init__(self, message: str):
        """Initialize the error.

        Args:
            message: Error message
        """
        super().__init__(message, status_code=400)


class PepperpyNotFoundError(PepperpyError):
    """Exception raised when a resource is not found."""

    def __init__(self, message: str):
        """Initialize the error.

        Args:
            message: Error message
        """
        super().__init__(message, status_code=404)


class PepperpyAuthenticationError(PepperpyError):
    """Exception raised for authentication errors."""

    def __init__(self, message: str):
        """Initialize the error.

        Args:
            message: Error message
        """
        super().__init__(message, status_code=401)


class PepperpyAuthorizationError(PepperpyError):
    """Exception raised for authorization errors."""

    def __init__(self, message: str):
        """Initialize the error.

        Args:
            message: Error message
        """
        super().__init__(message, status_code=403)


class PepperpyTimeoutError(PepperpyError):
    """Exception raised for timeout errors."""

    def __init__(self, message: str):
        """Initialize the error.

        Args:
            message: Error message
        """
        super().__init__(message, status_code=408)


class PepperpyRateLimitError(PepperpyError):
    """Exception raised for rate limit errors."""

    def __init__(self, message: str):
        """Initialize the error.

        Args:
            message: Error message
        """
        super().__init__(message, status_code=429)


class PepperpyConfigurationError(PepperpyError):
    """Exception raised for configuration errors."""

    def __init__(self, message: str):
        """Initialize the error.

        Args:
            message: Error message
        """
        super().__init__(message, status_code=500)


class PepperpyDependencyError(PepperpyError):
    """Exception raised for dependency errors."""

    def __init__(self, message: str):
        """Initialize the error.

        Args:
            message: Error message
        """
        super().__init__(message, status_code=500)


class PepperpyValidationError(PepperpyError):
    """Exception raised for validation errors."""

    def __init__(self, message: str):
        """Initialize the error.

        Args:
            message: Error message
        """
        super().__init__(message, status_code=400)


class PepperpyIntegrationError(PepperpyError):
    """Exception raised for integration errors."""

    def __init__(self, message: str):
        """Initialize the error.

        Args:
            message: Error message
        """
        super().__init__(message, status_code=502)


# Export all error classes
__all__ = [
    "PepperpyError",
    "PepperpyValueError",
    "PepperpyTypeError",
    "PepperpyNotFoundError",
    "PepperpyAuthenticationError",
    "PepperpyAuthorizationError",
    "PepperpyTimeoutError",
    "PepperpyRateLimitError",
    "PepperpyConfigurationError",
    "PepperpyDependencyError",
    "PepperpyValidationError",
    "PepperpyIntegrationError",
]
