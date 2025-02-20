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

    This class provides a consistent interface for error handling across
    the Pepperpy framework, including support for:
    - Detailed error messages
    - Additional error details
    - Recovery hints
    - User-friendly messages
    """

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        recovery_hint: Optional[str] = None,
        user_message: Optional[str] = None,
    ) -> None:
        """Initialize the error.

        Args:
            message: Technical error message.
            details: Optional dictionary of additional error details.
            recovery_hint: Optional hint for recovering from the error.
            user_message: Optional user-friendly error message.
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.recovery_hint = recovery_hint
        self.user_message = user_message or message

    def __str__(self) -> str:
        """Get string representation of the error.

        Returns:
            str: Error message with optional recovery hint.
        """
        if self.recovery_hint:
            return f"{self.message} ({self.recovery_hint})"
        return self.message


# System Errors


class ConfigError(PepperpyError):
    """Raised when there is a configuration error."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        recovery_hint: Optional[str] = None,
    ) -> None:
        """Initialize the configuration error."""
        super().__init__(
            message,
            "ERR001",
            details,
            user_message,
            recovery_hint,
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
    ) -> None:
        """Initialize the validation error."""
        super().__init__(
            message,
            "ERR002",
            details,
            user_message,
            recovery_hint,
        )


class StateError(PepperpyError):
    """Raised when an operation is invalid for the current state."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        recovery_hint: Optional[str] = None,
    ) -> None:
        """Initialize the error."""
        super().__init__(
            message,
            "ERR003",
            details,
            user_message,
            recovery_hint,
        )


class LifecycleError(PepperpyError):
    """Raised when a lifecycle operation fails."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        recovery_hint: Optional[str] = None,
    ) -> None:
        """Initialize the error."""
        super().__init__(
            message,
            "ERR007",
            details,
            user_message,
            recovery_hint,
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
    ) -> None:
        """Initialize the error."""
        super().__init__(
            message,
            "ERR004",
            details,
            user_message,
            recovery_hint,
        )


class ResourceError(PepperpyError):
    """Raised when a resource operation fails."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        recovery_hint: Optional[str] = None,
    ) -> None:
        """Initialize the error."""
        super().__init__(
            message,
            "ERR005",
            details,
            user_message,
            recovery_hint,
        )


class RegistryError(PepperpyError):
    """Raised when a registry operation fails."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        recovery_hint: Optional[str] = None,
    ) -> None:
        """Initialize the registry error.

        Args:
            message: Error message
            details: Optional error details
            user_message: Optional user-friendly message
            recovery_hint: Optional recovery hint
        """
        super().__init__(
            message,
            "ERR008",
            details,
            user_message,
            recovery_hint,
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
    ) -> None:
        """Initialize the factory error."""
        super().__init__(
            message,
            "ERR008",
            details,
            user_message,
            recovery_hint,
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
    ) -> None:
        """Initialize the capability error.

        Args:
            message: Error message
            details: Optional error details
            user_message: Optional user-friendly message
            recovery_hint: Optional recovery hint
        """
        super().__init__(
            message,
            "ERR100",
            details,
            user_message,
            recovery_hint,
        )


class LearningError(CapabilityError):
    """Error raised by learning capabilities."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        recovery_hint: Optional[str] = None,
    ) -> None:
        """Initialize the learning error.

        Args:
            message: Error message
            details: Optional error details
            user_message: Optional user-friendly message
            recovery_hint: Optional recovery hint
        """
        super().__init__(
            message,
            details,
            user_message,
            recovery_hint,
        )


class PlanningError(CapabilityError):
    """Error raised by planning capabilities."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        recovery_hint: Optional[str] = None,
    ) -> None:
        """Initialize the error."""
        super().__init__(
            message,
            details,
            user_message,
            recovery_hint,
        )


class ReasoningError(CapabilityError):
    """Error raised by reasoning capabilities."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        recovery_hint: Optional[str] = None,
    ) -> None:
        """Initialize the error."""
        super().__init__(
            message,
            details,
            user_message,
            recovery_hint,
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
    ) -> None:
        """Initialize the error."""
        super().__init__(
            message,
            "ERR007",
            details,
            user_message,
            recovery_hint,
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
    ) -> None:
        """Initialize the error."""
        super().__init__(
            message,
            "ERR008",
            details,
            user_message,
            recovery_hint,
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
    ) -> None:
        """Initialize the error."""
        super().__init__(
            message,
            "ERR009",
            details,
            user_message,
            recovery_hint,
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
    ) -> None:
        """Initialize the error."""
        super().__init__(
            message,
            "ERR010",
            details,
            user_message,
            recovery_hint,
        )


class AuthorizationError(PepperpyError):
    """Raised when authorization fails."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        recovery_hint: Optional[str] = None,
    ) -> None:
        """Initialize the error."""
        super().__init__(
            message,
            "ERR011",
            details,
            user_message,
            recovery_hint,
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
    ) -> None:
        """Initialize the error."""
        super().__init__(
            message,
            "ERR012",
            details,
            user_message,
            recovery_hint,
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
    ) -> None:
        """Initialize the error."""
        super().__init__(
            message,
            "ERR013",
            details,
            user_message,
            recovery_hint,
        )


class DuplicateError(PepperpyError):
    """Raised when a duplicate resource is found."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        recovery_hint: Optional[str] = None,
    ) -> None:
        """Initialize the error."""
        super().__init__(
            message,
            "ERR014",
            details,
            user_message,
            recovery_hint,
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
        "ERR008": RegistryError,
        "ERR007": WorkflowError,
        "ERR009": PepperpyMemoryError,
        "ERR010": PepperpyTimeoutError,
        "ERR011": AuthenticationError,
        "ERR012": AuthorizationError,
        "ERR013": NotFoundError,
        "ERR014": DuplicateError,
        "ERR100": CapabilityError,
        "ERR300": AgentError,
        "ERR400": ContentError,
        "ERR500": LLMError,
        "ERR600": SynthesisError,
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
) -> PepperpyError:
    """Create error instance by error code.

    Args:
    ----
        code: Error code
        message: Error message
        details: Additional error details
        user_message: User-friendly error message
        recovery_hint: Hint for recovering from the error

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
    )


class AgentError(PepperpyError):
    """Raised when an agent operation fails."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        recovery_hint: Optional[str] = None,
    ) -> None:
        super().__init__(
            message,
            code="ERR300",
            details=details,
            user_message=user_message,
            recovery_hint=recovery_hint,
        )


class ContentError(PepperpyError):
    """Raised when content processing fails."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        recovery_hint: Optional[str] = None,
    ) -> None:
        super().__init__(
            message,
            code="ERR400",
            details=details,
            user_message=user_message,
            recovery_hint=recovery_hint,
        )


class LLMError(PepperpyError):
    """Raised when LLM operations fail."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        recovery_hint: Optional[str] = None,
    ) -> None:
        super().__init__(
            message,
            code="ERR500",
            details=details,
            user_message=user_message,
            recovery_hint=recovery_hint,
        )


class SynthesisError(PepperpyError):
    """Raised when synthesis operations fail."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        recovery_hint: Optional[str] = None,
    ) -> None:
        super().__init__(
            message,
            code="ERR600",
            details=details,
            user_message=user_message,
            recovery_hint=recovery_hint,
        )


class MemoryBackendError(PepperpyMemoryError):
    """Error raised when memory backend operations fail."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        recovery_hint: Optional[str] = None,
    ) -> None:
        """Initialize memory backend error.

        Args:
            message: Error message
            details: Optional error details
            user_message: Optional user-friendly message
            recovery_hint: Optional recovery hint
        """
        super().__init__(
            message,
            details=details,
            user_message=user_message,
            recovery_hint=recovery_hint,
        )


class MemoryStorageError(MemoryBackendError):
    """Exception raised when storing data in memory fails."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        recovery_hint: Optional[str] = None,
    ) -> None:
        super().__init__(
            message,
            details=details,
            user_message=user_message,
            recovery_hint=recovery_hint,
        )


class MemoryRetrievalError(MemoryBackendError):
    """Exception raised when retrieving data from memory fails."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        recovery_hint: Optional[str] = None,
    ) -> None:
        super().__init__(
            message,
            details=details,
            user_message=user_message,
            recovery_hint=recovery_hint,
        )


class MemoryDeletionError(MemoryBackendError):
    """Exception raised when deleting data from memory fails."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        recovery_hint: Optional[str] = None,
    ) -> None:
        super().__init__(
            message,
            details=details,
            user_message=user_message,
            recovery_hint=recovery_hint,
        )


class MemoryExistsError(MemoryBackendError):
    """Exception raised when checking key existence in memory fails."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        recovery_hint: Optional[str] = None,
    ) -> None:
        super().__init__(
            message,
            details=details,
            user_message=user_message,
            recovery_hint=recovery_hint,
        )


class MemoryCleanupError(MemoryBackendError):
    """Exception raised when cleaning up memory resources fails."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        recovery_hint: Optional[str] = None,
    ) -> None:
        super().__init__(
            message,
            details=details,
            user_message=user_message,
            recovery_hint=recovery_hint,
        )


class MemoryBackendNotFoundError(PepperpyMemoryError):
    """Error raised when memory backend is not found."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        recovery_hint: Optional[str] = None,
    ) -> None:
        """Initialize memory backend not found error.

        Args:
            message: Error message
            details: Optional error details
            user_message: Optional user-friendly message
            recovery_hint: Optional recovery hint
        """
        super().__init__(
            message,
            details=details,
            user_message=user_message,
            recovery_hint=recovery_hint,
        )


class MemoryBackendAlreadyExistsError(PepperpyMemoryError):
    """Error raised when memory backend already exists."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        recovery_hint: Optional[str] = None,
    ) -> None:
        """Initialize memory backend already exists error.

        Args:
            message: Error message
            details: Optional error details
            user_message: Optional user-friendly message
            recovery_hint: Optional recovery hint
        """
        super().__init__(
            message,
            details=details,
            user_message=user_message,
            recovery_hint=recovery_hint,
        )


class MemoryBackendInvalidError(PepperpyMemoryError):
    """Error raised when memory backend is invalid."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        recovery_hint: Optional[str] = None,
    ) -> None:
        """Initialize memory backend invalid error.

        Args:
            message: Error message
            details: Optional error details
            user_message: Optional user-friendly message
            recovery_hint: Optional recovery hint
        """
        super().__init__(
            message,
            details=details,
            user_message=user_message,
            recovery_hint=recovery_hint,
        )


class StorageError(PepperpyError):
    """Error raised by storage operations."""

    pass
