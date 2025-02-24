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
    """Raised when authentication fails."""

    def __init__(
        self,
        message: str,
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
    """Raised when authorization fails."""

    def __init__(
        self,
        message: str,
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
    """Raised when token validation or manipulation fails."""

    def __init__(
        self,
        message: str,
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
    """Raised when encryption fails."""

    def __init__(
        self,
        message: str,
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
    """Raised when decryption fails."""

    def __init__(
        self,
        message: str,
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
    """Raised when security validation fails."""

    def __init__(
        self,
        message: str,
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
    """Raised when security configuration is invalid."""

    def __init__(
        self,
        message: str,
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
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str,
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
    """Raised when a duplicate security entity is detected."""

    def __init__(
        self,
        message: str,
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


class CircularDependencyError(SecurityError):
    """Raised when a circular dependency is detected."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize circular dependency error.

        Args:
            message: Error message
            details: Additional error details
        """
        error_details = details or {}
        error_details["error_code"] = "SEC010"
        super().__init__(message=message, details=error_details)


class SecurityScanError(SecurityError):
    """Raised when security scanning fails."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize security scan error.

        Args:
            message: Error message
            details: Additional error details
        """
        error_details = details or {}
        error_details["error_code"] = "SEC011"
        super().__init__(message=message, details=error_details)


class AuditError(SecurityError):
    """Raised when security audit fails."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize audit error.

        Args:
            message: Error message
            details: Additional error details
        """
        error_details = details or {}
        error_details["error_code"] = "SEC012"
        super().__init__(message=message, details=error_details)


# Export public API
__all__ = [
    "SecurityError",
    "AuthenticationError",
    "AuthorizationError",
    "TokenError",
    "EncryptionError",
    "DecryptionError",
    "ValidationError",
    "ConfigurationError",
    "RateLimitError",
    "DuplicateError",
    "CircularDependencyError",
    "SecurityScanError",
    "AuditError",
]
