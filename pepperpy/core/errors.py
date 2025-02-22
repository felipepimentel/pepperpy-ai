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
    EXTENSION = "extension"


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
    """Base error class for all framework errors."""

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize error.

        Args:
            message: Error message
            code: Optional error code
            details: Optional error details
        """
        super().__init__(message)
        self.code = code
        self.details = details or {}

    def with_context(self, **kwargs: Any) -> "PepperpyError":
        """Add context to error.

        Args:
            **kwargs: Context key-value pairs

        Returns:
            Error with added context
        """
        self.details.update(kwargs)
        return self


# System Errors


class ConfigError(PepperpyError):
    """Raised when there is a configuration error."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the configuration error."""
        error_details = {"error_code": "ERR001", **(details or {})}
        super().__init__(
            message,
            details=error_details,
        )


# Alias for backward compatibility
ConfigurationError = ConfigError


class ValidationError(PepperpyError):
    """Raised when validation fails."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the validation error."""
        error_details = {"error_code": "ERR002", **(details or {})}
        super().__init__(
            message,
            details=error_details,
        )


class StateError(PepperpyError):
    """Raised when an operation is invalid for the current state."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the error."""
        error_details = {"error_code": "ERR003", **(details or {})}
        super().__init__(
            message,
            details=error_details,
        )


class LifecycleError(PepperpyError):
    """Raised when a lifecycle operation fails."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the error."""
        error_details = {"error_code": "ERR007", **(details or {})}
        super().__init__(
            message,
            details=error_details,
        )


# Provider Errors


class ProviderError(PepperpyError):
    """Raised when a provider operation fails."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the error."""
        error_details = {"error_code": "ERR004", **(details or {})}
        super().__init__(
            message,
            details=error_details,
        )


class ResourceError(PepperpyError):
    """Error raised by resource operations."""

    pass


class RegistryError(PepperpyError):
    """Raised when a registry operation fails."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the registry error.

        Args:
            message: Error message
            details: Optional error details
        """
        error_details = {"error_code": "ERR008", **(details or {})}
        super().__init__(
            message,
            details=error_details,
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
    ) -> None:
        """Initialize the factory error."""
        error_details = {"error_code": "ERR008", **(details or {})}
        super().__init__(
            message,
            details=error_details,
        )


# Capability Errors


class CapabilityError(PepperpyError):
    """Base class for capability-related errors."""

    def __init__(
        self,
        message: str,
        capability_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the capability error.

        Args:
            message: Error message
            capability_type: Optional capability type
            details: Optional error details
        """
        error_details = {"error_code": "ERR100", **(details or {})}
        if capability_type:
            error_details["capability_type"] = capability_type
        super().__init__(
            message,
            details=error_details,
        )


class LearningError(CapabilityError):
    """Error raised by learning capabilities."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the learning error.

        Args:
            message: Error message
            details: Optional error details
        """
        super().__init__(
            message,
            capability_type="learning",
            details=details,
        )


class PlanningError(CapabilityError):
    """Error raised by planning capabilities."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the error."""
        super().__init__(
            message,
            capability_type="planning",
            details=details,
        )


class ReasoningError(CapabilityError):
    """Error raised by reasoning capabilities."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the error."""
        super().__init__(
            message,
            capability_type="reasoning",
            details=details,
        )


# Workflow Errors


class WorkflowError(PepperpyError):
    """Raised when a workflow operation fails."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the error."""
        error_details = {"error_code": "ERR007", **(details or {})}
        super().__init__(
            message,
            code="ERR007",
            details=error_details,
        )


# Memory Errors


class PepperpyMemoryError(PepperpyError):
    """Raised when a memory operation fails."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the error."""
        error_details = {"error_code": "ERR008", **(details or {})}
        super().__init__(
            message,
            code="ERR008",
            details=error_details,
        )


# System Errors


class PepperpyTimeoutError(PepperpyError):
    """Raised when an operation times out."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the error."""
        error_details = {"error_code": "ERR009", **(details or {})}
        super().__init__(
            message,
            code="ERR009",
            details=error_details,
        )


# Security Errors


class AuthenticationError(PepperpyError):
    """Raised when authentication fails."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the error."""
        error_details = {"error_code": "ERR010", **(details or {})}
        super().__init__(
            message,
            code="ERR010",
            details=error_details,
        )


class AuthorizationError(PepperpyError):
    """Raised when authorization fails."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the error."""
        error_details = {"error_code": "ERR011", **(details or {})}
        super().__init__(
            message,
            code="ERR011",
            details=error_details,
        )


# Network Errors


class NetworkError(PepperpyError):
    """Raised when a network operation fails."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the error."""
        error_details = {"error_code": "ERR012", **(details or {})}
        super().__init__(
            message,
            code="ERR012",
            details=error_details,
        )


# Resource Errors


class NotFoundError(PepperpyError):
    """Raised when a resource is not found."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the error."""
        error_details = {"error_code": "ERR013", **(details or {})}
        super().__init__(
            message,
            code="ERR013",
            details=error_details,
        )


class DuplicateError(PepperpyError):
    """Raised when a duplicate resource is found."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the error."""
        error_details = {"error_code": "ERR014", **(details or {})}
        super().__init__(
            message,
            code="ERR014",
            details=error_details,
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
) -> PepperpyError:
    """Create error instance by error code.

    Args:
    ----
        code: Error code
        message: Error message
        details: Additional error details

    Returns:
    -------
        Error instance

    """
    error_class = get_error_class(code)
    return error_class(
        message,
        details=details,
    )


class AgentError(PepperpyError):
    """Raised when an agent operation fails."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        error_details = {"error_code": "ERR300", **(details or {})}
        super().__init__(
            message,
            code="ERR300",
            details=error_details,
        )


class ContentError(PepperpyError):
    """Raised when content processing fails."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        error_details = {"error_code": "ERR400", **(details or {})}
        super().__init__(
            message,
            code="ERR400",
            details=error_details,
        )


class LLMError(PepperpyError):
    """Raised when LLM operations fail."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        error_details = {"error_code": "ERR500", **(details or {})}
        super().__init__(
            message,
            code="ERR500",
            details=error_details,
        )


class SynthesisError(PepperpyError):
    """Raised when synthesis operations fail."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        error_details = {"error_code": "ERR600", **(details or {})}
        super().__init__(
            message,
            code="ERR600",
            details=error_details,
        )


class MemoryBackendError(PepperpyMemoryError):
    """Error raised when memory backend operations fail."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize memory backend error.

        Args:
            message: Error message
            details: Optional error details
        """
        super().__init__(
            message,
            details=details,
        )


class MemoryStorageError(MemoryBackendError):
    """Exception raised when storing data in memory fails."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message,
            details=details,
        )


class MemoryRetrievalError(MemoryBackendError):
    """Exception raised when retrieving data from memory fails."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message,
            details=details,
        )


class MemoryDeletionError(MemoryBackendError):
    """Exception raised when deleting data from memory fails."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message,
            details=details,
        )


class MemoryExistsError(MemoryBackendError):
    """Exception raised when checking key existence in memory fails."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message,
            details=details,
        )


class MemoryCleanupError(MemoryBackendError):
    """Exception raised when cleaning up memory resources fails."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message,
            details=details,
        )


class MemoryBackendNotFoundError(PepperpyMemoryError):
    """Error raised when memory backend is not found."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize memory backend not found error.

        Args:
            message: Error message
            details: Optional error details
        """
        super().__init__(
            message,
            details=details,
        )


class MemoryBackendAlreadyExistsError(PepperpyMemoryError):
    """Error raised when memory backend already exists."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize memory backend already exists error.

        Args:
            message: Error message
            details: Optional error details
        """
        super().__init__(
            message,
            details=details,
        )


class MemoryBackendInvalidError(PepperpyMemoryError):
    """Error raised when memory backend is invalid."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize memory backend invalid error.

        Args:
            message: Error message
            details: Optional error details
        """
        super().__init__(
            message,
            details=details,
        )


class StorageError(PepperpyError):
    """Error raised by storage operations."""

    pass


class ExtensionError(PepperpyError):
    """Error raised when extension operation fails."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize extension error.

        Args:
            message: Error message
            details: Optional error details
        """
        error_details = {"error_code": "ERR-106", **(details or {})}
        super().__init__(
            message=message,
            code="ERR-106",
            details=error_details,
        )


class HubError(PepperpyError):
    """Error raised by Hub operations."""

    pass


class ProcessingError(PepperpyError):
    """Raised when processing operations fail."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the error."""
        error_details = {"error_code": "ERR015", **(details or {})}
        super().__init__(
            message,
            code="ERR015",
            details=error_details,
        )


class MonitoringError(PepperpyError):
    """Raised when a monitoring operation fails."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the error."""
        error_details = {"error_code": "ERR016", **(details or {})}
        super().__init__(
            message,
            details=error_details,
        )
