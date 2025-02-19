"""Core error definitions for the Pepperpy framework.

This module defines core exceptions used throughout the framework, providing
specific error types for different failure scenarios. The error system includes:
- Error codes and categories
- Error tracking and logging
- Context handling
- Recovery hints
- Error chaining
- User-friendly messages
"""

import time
import traceback
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional, Type, TypedDict


class ErrorCategory(str, Enum):
    """Categories of errors in the system."""

    SYSTEM = "system"
    VALIDATION = "validation"
    RESOURCE = "resource"
    RUNTIME = "runtime"
    SECURITY = "security"
    NETWORK = "network"
    PLANNING = "planning"
    TOOLS = "tools"
    REASONING = "reasoning"
    LEARNING = "learning"
    FACTORY = "factory"


class ErrorContext(TypedDict, total=False):
    """Type definition for error context information."""

    error_type: str
    error_code: str
    details: dict[str, Any]
    source: str
    timestamp: str
    user_message: str
    recovery_hint: str


@dataclass
class ErrorMetadata:
    """Metadata for error tracking."""

    timestamp: float = field(default_factory=time.time)
    traceback: str = field(default_factory=lambda: traceback.format_exc())


class PepperpyError(Exception):
    """Base class for all Pepperpy errors.

    Attributes
    ----------
        message: Error message
        code: Error code
        details: Additional error details
        user_message: User-friendly error message
        recovery_hint: Hint for recovering from the error
        context: Error context information
        metadata: Error tracking metadata

    """

    def __init__(
        self,
        message: str,
        code: str = "ERR000",
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        recovery_hint: Optional[str] = None,
        context: Optional[ErrorContext] = None,
    ) -> None:
        """Initialize the error.

        Args:
        ----
            message: Error message
            code: Error code
            details: Additional error details
            user_message: User-friendly error message
            recovery_hint: Hint for recovering from the error
            context: Error context information

        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}
        self.user_message = user_message or message
        self.recovery_hint = recovery_hint
        self.context = context or {}
        self.metadata = ErrorMetadata()

    def __str__(self) -> str:
        """Return string representation of error."""
        return f"[{self.code}] {self.message}"


# System Errors


class ConfigError(PepperpyError):
    """Raised when there is a configuration error."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        recovery_hint: Optional[str] = None,
        context: Optional[ErrorContext] = None,
    ) -> None:
        """Initialize the configuration error."""
        super().__init__(
            message,
            "ERR001",
            details,
            user_message,
            recovery_hint,
            context,
        )


# Alias for backward compatibility
ConfigurationError = ConfigError


class ValidationError(PepperpyError):
    """Raised when validation fails."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        recovery_hint: Optional[str] = None,
        context: Optional[ErrorContext] = None,
    ) -> None:
        """Initialize the validation error."""
        super().__init__(
            message,
            "ERR002",
            details,
            user_message,
            recovery_hint,
            context,
        )


class StateError(PepperpyError):
    """Raised when an operation is invalid for the current state."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        recovery_hint: Optional[str] = None,
        context: Optional[ErrorContext] = None,
    ) -> None:
        """Initialize the error."""
        super().__init__(
            message,
            "ERR003",
            details,
            user_message,
            recovery_hint,
            context,
        )


class LifecycleError(PepperpyError):
    """Raised when a lifecycle operation fails."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        recovery_hint: Optional[str] = None,
        context: Optional[ErrorContext] = None,
    ) -> None:
        """Initialize the error."""
        super().__init__(
            message,
            "ERR007",
            details,
            user_message,
            recovery_hint,
            context,
        )


# Provider Errors


class ProviderError(PepperpyError):
    """Raised when a provider operation fails."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        recovery_hint: Optional[str] = None,
        context: Optional[ErrorContext] = None,
    ) -> None:
        """Initialize the error."""
        super().__init__(
            message,
            "ERR004",
            details,
            user_message,
            recovery_hint,
            context,
        )


class ResourceError(PepperpyError):
    """Raised when a resource operation fails."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        recovery_hint: Optional[str] = None,
        context: Optional[ErrorContext] = None,
    ) -> None:
        """Initialize the error."""
        super().__init__(
            message,
            "ERR005",
            details,
            user_message,
            recovery_hint,
            context,
        )


class RegistryError(PepperpyError):
    """Raised when a registry operation fails."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        recovery_hint: Optional[str] = None,
        context: Optional[ErrorContext] = None,
    ) -> None:
        """Initialize the error."""
        super().__init__(
            message,
            "ERR006",
            details,
            user_message,
            recovery_hint,
            context,
        )


class FactoryError(PepperpyError):
    """Raised when a factory operation fails.

    This error is raised when there is a problem creating or configuring
    objects through a factory.
    """

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        recovery_hint: Optional[str] = None,
        context: Optional[ErrorContext] = None,
    ) -> None:
        """Initialize the factory error."""
        super().__init__(
            message,
            "ERR008",
            details,
            user_message,
            recovery_hint,
            context,
        )


# Capability Errors


class CapabilityError(PepperpyError):
    """Base class for capability-related errors."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        recovery_hint: Optional[str] = None,
        context: Optional[ErrorContext] = None,
    ) -> None:
        """Initialize the error."""
        super().__init__(
            message,
            "ERR006",
            details,
            user_message,
            recovery_hint,
            context,
        )


class LearningError(CapabilityError):
    """Error raised by learning capabilities."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        recovery_hint: Optional[str] = None,
        context: Optional[ErrorContext] = None,
    ) -> None:
        """Initialize the error."""
        super().__init__(
            message,
            details,
            user_message,
            recovery_hint,
            context,
        )


class PlanningError(CapabilityError):
    """Error raised by planning capabilities."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        recovery_hint: Optional[str] = None,
        context: Optional[ErrorContext] = None,
    ) -> None:
        """Initialize the error."""
        super().__init__(
            message,
            details,
            user_message,
            recovery_hint,
            context,
        )


class ReasoningError(CapabilityError):
    """Error raised by reasoning capabilities."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        recovery_hint: Optional[str] = None,
        context: Optional[ErrorContext] = None,
    ) -> None:
        """Initialize the error."""
        super().__init__(
            message,
            details,
            user_message,
            recovery_hint,
            context,
        )


# Workflow Errors


class WorkflowError(PepperpyError):
    """Raised when a workflow operation fails."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        recovery_hint: Optional[str] = None,
        context: Optional[ErrorContext] = None,
    ) -> None:
        """Initialize the error."""
        super().__init__(
            message,
            "ERR007",
            details,
            user_message,
            recovery_hint,
            context,
        )


# Memory Errors


class PepperpyMemoryError(PepperpyError):
    """Raised when a memory operation fails."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        recovery_hint: Optional[str] = None,
        context: Optional[ErrorContext] = None,
    ) -> None:
        """Initialize the error."""
        super().__init__(
            message,
            "ERR008",
            details,
            user_message,
            recovery_hint,
            context,
        )


# System Errors


class PepperpyTimeoutError(PepperpyError):
    """Raised when an operation times out."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        recovery_hint: Optional[str] = None,
        context: Optional[ErrorContext] = None,
    ) -> None:
        """Initialize the error."""
        super().__init__(
            message,
            "ERR009",
            details,
            user_message,
            recovery_hint,
            context,
        )


# Security Errors


class AuthenticationError(PepperpyError):
    """Raised when authentication fails."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        recovery_hint: Optional[str] = None,
        context: Optional[ErrorContext] = None,
    ) -> None:
        """Initialize the error."""
        super().__init__(
            message,
            "ERR010",
            details,
            user_message,
            recovery_hint,
            context,
        )


class AuthorizationError(PepperpyError):
    """Raised when authorization fails."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        recovery_hint: Optional[str] = None,
        context: Optional[ErrorContext] = None,
    ) -> None:
        """Initialize the error."""
        super().__init__(
            message,
            "ERR011",
            details,
            user_message,
            recovery_hint,
            context,
        )


# Network Errors


class NetworkError(PepperpyError):
    """Raised when a network operation fails."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        recovery_hint: Optional[str] = None,
        context: Optional[ErrorContext] = None,
    ) -> None:
        """Initialize the error."""
        super().__init__(
            message,
            "ERR012",
            details,
            user_message,
            recovery_hint,
            context,
        )


# Resource Errors


class NotFoundError(PepperpyError):
    """Raised when a resource is not found."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        recovery_hint: Optional[str] = None,
        context: Optional[ErrorContext] = None,
    ) -> None:
        """Initialize the error."""
        super().__init__(
            message,
            "ERR013",
            details,
            user_message,
            recovery_hint,
            context,
        )


class DuplicateError(PepperpyError):
    """Raised when a duplicate resource is found."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        recovery_hint: Optional[str] = None,
        context: Optional[ErrorContext] = None,
    ) -> None:
        """Initialize the error."""
        super().__init__(
            message,
            "ERR014",
            details,
            user_message,
            recovery_hint,
            context,
        )


# Error Utilities


def get_error_class(code: str) -> Type[PepperpyError]:
    """Get error class by error code.

    Args:
    ----
        code: Error code

    Returns:
    -------
        Error class

    Raises:
    ------
        ValueError: If error code is not found

    """
    error_classes = {
        "ERR000": PepperpyError,
        "ERR001": ConfigError,
        "ERR002": ValidationError,
        "ERR003": StateError,
        "ERR004": ProviderError,
        "ERR005": ResourceError,
        "ERR006": CapabilityError,
        "ERR007": WorkflowError,
        "ERR008": PepperpyMemoryError,
        "ERR009": PepperpyTimeoutError,
        "ERR010": AuthenticationError,
        "ERR011": AuthorizationError,
        "ERR012": NetworkError,
        "ERR013": NotFoundError,
        "ERR014": DuplicateError,
    }
    if code not in error_classes:
        raise ValueError(f"Unknown error code: {code}")
    return error_classes[code]


def create_error(
    code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    user_message: Optional[str] = None,
    recovery_hint: Optional[str] = None,
    context: Optional[ErrorContext] = None,
) -> PepperpyError:
    """Create error instance by error code.

    Args:
    ----
        code: Error code
        message: Error message
        details: Additional error details
        user_message: User-friendly error message
        recovery_hint: Hint for recovering from the error
        context: Error context information

    Returns:
    -------
        Error instance

    """
    error_class = get_error_class(code)
    return error_class(
        message,
        details=details,
        user_message=user_message,
        recovery_hint=recovery_hint,
        context=context,
    )
