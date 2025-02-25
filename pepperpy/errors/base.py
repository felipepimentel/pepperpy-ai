"""Base error classes for the Pepperpy error handling system.

This module provides the foundational error classes used throughout the Pepperpy system.
All custom errors should inherit from PepperpyError.

Example:
    >>> error = PepperpyError(
    ...     message="Failed to process request",
    ...     code="SYS-E-001",
    ...     details={"request_id": "123"},
    ...     recovery_hint="Retry the request"
    ... )
    >>> str(error)
    '[SYS-E-001] Failed to process request | Recovery hint: Retry the request'
"""

import traceback
from datetime import datetime
from typing import Any

from .codes import ErrorCategory


class PepperpyError(Exception):
    """Base error class for all Pepperpy errors.

    Provides standardized error handling with error codes, recovery hints,
    and detailed context information.

    Args:
        message: Human-readable error description
        code: Unique error code (format: CAT-SEV-XXX)
        details: Additional context about the error
        recovery_hint: Suggestion for resolving the error
        cause: Original exception that caused this error

    Example:
        >>> error = PepperpyError(
        ...     message="Failed to process request",
        ...     code="SYS-E-001",
        ...     details={"request_id": "123"},
        ...     recovery_hint="Retry the request"
        ... )
        >>> str(error)
        '[SYS-E-001] Failed to process request | Recovery hint: Retry the request'
    """

    def __init__(
        self,
        message: str,
        code: str | None = None,
        details: dict[str, Any] | None = None,
        recovery_hint: str | None = None,
        cause: Exception | None = None,
    ) -> None:
        self.message = message
        self.code = code
        self.details = details or {}
        self.recovery_hint = recovery_hint
        self.cause = cause
        self.timestamp = datetime.now()
        self.stack_trace = traceback.format_exc()
        super().__init__(message)

    def __str__(self) -> str:
        """Format the error as a human-readable string.

        Returns:
            str: Formatted error message with code, message, and optional details
        """
        parts = [f"[{self.code}] {self.message}" if self.code else self.message]
        if self.recovery_hint:
            parts.append(f"Recovery hint: {self.recovery_hint}")
        if self.details:
            parts.append(f"Details: {self.details}")
        return " | ".join(parts)


class ValidationError(PepperpyError):
    """Error raised when data validation fails.

    Args:
        message: Description of the validation error
        code: Optional error code (defaults to VAL-E-XXX)
        details: Additional validation context
        recovery_hint: Suggestion for fixing the validation error
        cause: Original validation exception if any

    Example:
        >>> raise ValidationError(
        ...     "Invalid user data",
        ...     details={"field": "email", "value": "invalid"}
        ... )
    """

    ERROR_CODE_PREFIX = ErrorCategory.VALIDATION.value


class ResourceError(PepperpyError):
    """Error raised for resource-related issues (not found, access denied, etc).

    Args:
        message: Description of the resource error
        code: Optional error code (defaults to RES-E-XXX)
        details: Additional resource context
        recovery_hint: Suggestion for resolving the resource issue
        cause: Original resource exception if any

    Example:
        >>> raise ResourceError(
        ...     "Resource not found",
        ...     code="RES-E-001",
        ...     details={"resource_id": "123"}
        ... )
    """

    ERROR_CODE_PREFIX = ErrorCategory.RESOURCE.value


class ConfigurationError(PepperpyError):
    """Error raised for configuration-related issues.

    Args:
        message: Description of the configuration error
        code: Optional error code (defaults to CFG-E-XXX)
        details: Additional configuration context
        recovery_hint: Suggestion for fixing the configuration
        cause: Original configuration exception if any

    Example:
        >>> raise ConfigurationError(
        ...     "Missing required config",
        ...     code="CFG-E-001",
        ...     recovery_hint="Set PEPPERPY_API_KEY environment variable"
        ... )
    """

    ERROR_CODE_PREFIX = ErrorCategory.CONFIG.value


class StateError(PepperpyError):
    """Error raised for invalid state transitions or state-related issues.

    Args:
        message: Description of the state error
        code: Optional error code (defaults to STA-E-XXX)
        details: Additional state context
        recovery_hint: Suggestion for resolving the state issue
        cause: Original state exception if any

    Example:
        >>> raise StateError(
        ...     "Invalid state transition",
        ...     code="STA-E-001",
        ...     details={"from": "pending", "to": "completed"}
        ... )
    """

    ERROR_CODE_PREFIX = ErrorCategory.STATE.value


class SecurityError(PepperpyError):
    """Error raised for security-related issues.

    Args:
        message: Description of the security error
        code: Optional error code (defaults to SEC-E-XXX)
        details: Additional security context
        recovery_hint: Suggestion for resolving the security issue
        cause: Original security exception if any

    Example:
        >>> raise SecurityError(
        ...     "Invalid authentication token",
        ...     code="SEC-E-001",
        ...     recovery_hint="Please re-authenticate"
        ... )
    """

    ERROR_CODE_PREFIX = ErrorCategory.SECURITY.value


class NetworkError(PepperpyError):
    """Error raised for network-related issues.

    Args:
        message: Description of the network error
        code: Optional error code (defaults to NET-E-XXX)
        details: Additional network context
        recovery_hint: Suggestion for resolving the network issue
        cause: Original network exception if any

    Example:
        >>> raise NetworkError(
        ...     "Connection failed",
        ...     code="NET-E-001",
        ...     recovery_hint="Check network connectivity"
        ... )
    """

    ERROR_CODE_PREFIX = ErrorCategory.NETWORK.value


class DatabaseError(PepperpyError):
    """Error raised for database-related issues.

    Args:
        message: Description of the database error
        code: Optional error code (defaults to DB-E-XXX)
        details: Additional database context
        recovery_hint: Suggestion for resolving the database issue
        cause: Original database exception if any

    Example:
        >>> raise DatabaseError(
        ...     "Query execution failed",
        ...     code="DB-E-001",
        ...     details={"query_id": "123"}
        ... )
    """

    ERROR_CODE_PREFIX = ErrorCategory.DATABASE.value
