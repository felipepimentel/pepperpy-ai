"""Security error definitions.

This module provides error classes for the security system.
"""

from typing import Any

from pepperpy.core.errors import PepperError


class SecurityError(PepperError):
    """Base class for security errors."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize security error.

        Args:
            message: Error message
            details: Additional error details
        """
        error_details = details or {}
        error_details["error_code"] = "SEC000"
        super().__init__(message=message, details=error_details)


class AuthenticationError(SecurityError):
    """Authentication error."""

    def __init__(
        self,
        message: str = "Authentication failed",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize authentication error.

        Args:
            message: Error message
            details: Additional error details
        """
        error_details = details or {}
        error_details["error_code"] = "SEC001"
        super().__init__(message=message, details=error_details)


class AuthorizationError(SecurityError):
    """Authorization error."""

    def __init__(
        self,
        message: str = "Authorization failed",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize authorization error.

        Args:
            message: Error message
            details: Additional error details
        """
        error_details = details or {}
        error_details["error_code"] = "SEC002"
        super().__init__(message=message, details=error_details)


class TokenError(SecurityError):
    """Token error."""

    def __init__(
        self,
        message: str = "Invalid token",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize token error.

        Args:
            message: Error message
            details: Additional error details
        """
        error_details = details or {}
        error_details["error_code"] = "SEC003"
        super().__init__(message=message, details=error_details)


class EncryptionError(SecurityError):
    """Encryption error."""

    def __init__(
        self,
        message: str = "Encryption failed",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize encryption error.

        Args:
            message: Error message
            details: Additional error details
        """
        error_details = details or {}
        error_details["error_code"] = "SEC004"
        super().__init__(message=message, details=error_details)


class DecryptionError(SecurityError):
    """Decryption error."""

    def __init__(
        self,
        message: str = "Decryption failed",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize decryption error.

        Args:
            message: Error message
            details: Additional error details
        """
        error_details = details or {}
        error_details["error_code"] = "SEC005"
        super().__init__(message=message, details=error_details)


class ValidationError(SecurityError):
    """Security validation error."""

    def __init__(
        self,
        message: str = "Validation failed",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize validation error.

        Args:
            message: Error message
            details: Additional error details
        """
        error_details = details or {}
        error_details["error_code"] = "SEC006"
        super().__init__(message=message, details=error_details)


class ConfigurationError(SecurityError):
    """Security configuration error."""

    def __init__(
        self,
        message: str = "Invalid configuration",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize configuration error.

        Args:
            message: Error message
            details: Additional error details
        """
        error_details = details or {}
        error_details["error_code"] = "SEC007"
        super().__init__(message=message, details=error_details)


class RateLimitError(SecurityError):
    """Rate limit error."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize rate limit error.

        Args:
            message: Error message
            details: Additional error details
        """
        error_details = details or {}
        error_details["error_code"] = "SEC008"
        super().__init__(message=message, details=error_details)


class DuplicateError(SecurityError):
    """Duplicate error."""

    def __init__(
        self,
        message: str = "Resource already exists",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize duplicate error.

        Args:
            message: Error message
            details: Additional error details
        """
        error_details = details or {}
        error_details["error_code"] = "SEC009"
        super().__init__(message=message, details=error_details)
