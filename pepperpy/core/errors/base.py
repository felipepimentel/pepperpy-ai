"""Core error definitions for the Pepperpy framework.

This module defines core exceptions used throughout the framework, providing
specific error types for different failure scenarios. The error system includes:
- Error codes and categories
- Error tracking and logging
- Context handling
- Recovery hints
- Error chaining
- User-friendly messages

Status: Stable
"""

from __future__ import annotations

import time
import traceback
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional, TypedDict


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


class PepperError(Exception):
    """Base class for all Pepperpy errors."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
        error_code: str | None = None,
    ) -> None:
        """Initialize error.

        Args:
            message: Error message
            details: Optional error details
            error_code: Optional error code

        """
        super().__init__(message)
        self.details = details or {}
        if error_code:
            self.details["error_code"] = error_code
        self.metadata = ErrorMetadata()

    def __str__(self) -> str:
        """Get string representation of error.

        Returns:
            Error message with details if available

        """
        if self.details:
            return f"{super().__str__()} - {self.details}"
        return super().__str__()


# System Errors


class ConfigError(PepperError):
    """Raised when there is a configuration error."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the configuration error."""
        super().__init__(message, details=details, error_code="ERR001")


# Alias for backward compatibility
ConfigurationError = ConfigError


class ValidationError(PepperError):
    """Raised when validation fails."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the validation error."""
        super().__init__(message, details=details, error_code="ERR002")


class StateError(PepperError):
    """Raised when an operation is invalid for the current state."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the error."""
        super().__init__(message, details=details, error_code="ERR003")


class ComponentError(PepperError):
    """Raised when a component operation fails."""

    def __init__(
        self,
        message: str,
        component_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the error.

        Args:
            message: Error message
            component_id: Optional component identifier
            details: Optional error details

        """
        error_details = {"component_id": component_id} if component_id else {}
        if details:
            error_details.update(details)
        super().__init__(message, details=error_details, error_code="ERR004")


class LifecycleError(PepperError):
    """Raised when a lifecycle operation fails."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the error."""
        super().__init__(message, details=details, error_code="ERR007")


# Provider Errors


class ProviderError(PepperError):
    """Raised when a provider operation fails."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the error."""
        super().__init__(message, details=details, error_code="ERR004")


class ResourceError(PepperError):
    """Error raised by resource operations."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize resource error.

        Args:
            message: Error message
            details: Optional error details

        """
        super().__init__(message, details=details, error_code="ERR005")


class RegistryError(PepperError):
    """Raised when a registry operation fails."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the registry error.

        Args:
            message: Error message
            details: Optional error details

        """
        super().__init__(message, details=details, error_code="ERR008")


class FactoryError(PepperError):
    """Raised when a factory operation fails.

    This error is raised when there is a problem creating or configuring
    objects through a factory.
    """

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the factory error."""
        super().__init__(message, details=details, error_code="ERR009")


# Capability Errors


class CapabilityError(PepperError):
    """Base class for capability-related errors."""

    def __init__(
        self,
        message: str,
        capability_type: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the capability error.

        Args:
            message: Error message
            capability_type: Optional capability type
            details: Optional error details

        """
        error_details = {"capability_type": capability_type} if capability_type else {}
        if details:
            error_details.update(details)
        super().__init__(message, details=error_details, error_code="ERR010")


class LearningError(CapabilityError):
    """Raised when an AI learning operation fails.

    This error is raised when there is a problem with AI learning operations
    such as knowledge acquisition, model updates, or training processes.
    """

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the learning error."""
        error_details = details or {}
        error_details["error_code"] = "ERR101"
        super().__init__(
            message,
            capability_type="learning",
            details=error_details,
        )


class PlanningError(CapabilityError):
    """Error raised by planning capabilities."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
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
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the error."""
        super().__init__(
            message,
            capability_type="reasoning",
            details=details,
        )


# Workflow Errors


class WorkflowError(PepperError):
    """Raised when a workflow operation fails."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the error."""
        error_details = {"error_code": "ERR007", **(details or {})}
        super().__init__(message, details=error_details)


# Memory Errors


class PepperpyMemoryError(PepperError):
    """Raised when a memory operation fails."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the error."""
        error_details = {"error_code": "ERR008", **(details or {})}
        super().__init__(message, details=error_details)


# System Errors


class PepperpyTimeoutError(PepperError):
    """Raised when an operation times out."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the error."""
        error_details = {"error_code": "ERR009", **(details or {})}
        super().__init__(message, details=error_details)


# Security Errors


class AuthenticationError(PepperError):
    """Raised when authentication fails."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the error."""
        error_details = {"error_code": "ERR010", **(details or {})}
        super().__init__(message, details=error_details)


class AuthorizationError(PepperError):
    """Raised when authorization fails."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the error."""
        error_details = {"error_code": "ERR011", **(details or {})}
        super().__init__(message, details=error_details)


# Network Errors


class NetworkError(PepperError):
    """Raised when a network operation fails."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the error."""
        error_details = {"error_code": "ERR012", **(details or {})}
        super().__init__(message, details=error_details)


# Resource Errors


class NotFoundError(PepperError):
    """Raised when a resource is not found."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the error."""
        error_details = {"error_code": "ERR013", **(details or {})}
        super().__init__(message, details=error_details)


class DuplicateError(PepperError):
    """Raised when a duplicate resource is found."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the error."""
        error_details = {"error_code": "ERR014", **(details or {})}
        super().__init__(message, details=error_details)


# Error Utilities


def get_error_class(code: str) -> type[PepperError]:
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
        "ERR000": PepperError,
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
        "ERR015": ProcessingError,
        "ERR016": MonitoringError,
        "ERR017": MetricsError,
        "ERR018": PluginError,
        "ERR019": SecurityError,
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
    details: dict[str, Any] | None = None,
) -> PepperError:
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


class AgentError(PepperError):
    """Raised when an agent operation fails."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        error_details = {"error_code": "ERR300", **(details or {})}
        super().__init__(message, details=error_details)


class ContentError(PepperError):
    """Raised when content processing fails."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        error_details = {"error_code": "ERR400", **(details or {})}
        super().__init__(message, details=error_details)


class LLMError(PepperError):
    """Raised when LLM operations fail."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        error_details = {"error_code": "ERR500", **(details or {})}
        super().__init__(message, details=error_details)


class SynthesisError(PepperError):
    """Raised when synthesis operations fail."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        error_details = {"error_code": "ERR600", **(details or {})}
        super().__init__(message, details=error_details)


class MemoryBackendError(PepperpyMemoryError):
    """Error raised when memory backend operations fail."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize memory backend error.

        Args:
            message: Error message
            details: Optional error details

        """
        super().__init__(message, details=details)


class MemoryStorageError(MemoryBackendError):
    """Exception raised when storing data in memory fails."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, details=details)


class MemoryRetrievalError(MemoryBackendError):
    """Exception raised when retrieving data from memory fails."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, details=details)


class MemoryDeletionError(MemoryBackendError):
    """Exception raised when deleting data from memory fails."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, details=details)


class MemoryExistsError(MemoryBackendError):
    """Exception raised when checking key existence in memory fails."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, details=details)


class MemoryCleanupError(MemoryBackendError):
    """Exception raised when cleaning up memory resources fails."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, details=details)


class MemoryBackendNotFoundError(PepperpyMemoryError):
    """Error raised when memory backend is not found."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize memory backend not found error.

        Args:
            message: Error message
            details: Optional error details

        """
        super().__init__(message, details=details)


class MemoryBackendAlreadyExistsError(PepperpyMemoryError):
    """Error raised when memory backend already exists."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize memory backend already exists error.

        Args:
            message: Error message
            details: Optional error details

        """
        super().__init__(message, details=details)


class MemoryBackendInvalidError(PepperpyMemoryError):
    """Error raised when memory backend is invalid."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize memory backend invalid error.

        Args:
            message: Error message
            details: Optional error details

        """
        super().__init__(message, details=details)


class StorageError(PepperError):
    """Error raised by storage operations."""



class ExtensionError(PepperError):
    """Error raised when extension operation fails."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize extension error.

        Args:
            message: Error message
            details: Optional error details

        """
        error_details = {"error_code": "ERR-106", **(details or {})}
        super().__init__(message, details=error_details)


class HubError(PepperError):
    """Error raised by Hub operations."""



class ProcessingError(PepperError):
    """Raised when processing operations fail."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the error."""
        error_details = {"error_code": "ERR015", **(details or {})}
        super().__init__(message, details=error_details)


class MonitoringError(PepperError):
    """Raised when a monitoring operation fails."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the error."""
        error_details = {"error_code": "ERR016", **(details or {})}
        super().__init__(message, details=error_details)


class CLIError(PepperError):
    """Error raised by CLI commands.

    This error is raised when a CLI command fails to execute.
    It includes details about the failure to help with debugging.
    """

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize CLI error.

        Args:
            message: Error message
            details: Optional error details

        """
        super().__init__(message)
        self.details = details or {}


class AdapterError(PepperError):
    """Error raised by adapter operations.

    This error is raised when an adapter operation fails.
    It includes details about the failure to help with debugging.
    """

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize adapter error.

        Args:
            message: Error message
            details: Optional error details

        """
        super().__init__(message)
        self.details = details or {}


class AssetError(Exception):
    """Asset error.

    This error is raised when an asset operation fails.
    """

    def __init__(self, message: str) -> None:
        """Initialize error.

        Args:
            message: Error message

        """
        super().__init__(message)


class MetricsError(PepperError):
    """Raised when a metrics operation fails."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the error."""
        error_details = {"error_code": "ERR017", **(details or {})}
        super().__init__(message, details=error_details)


class PluginError(PepperError):
    """Raised when a plugin operation fails."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the error."""
        error_details = {"error_code": "ERR018", **(details or {})}
        super().__init__(message, details=error_details)


class SecurityError(PepperError):
    """Raised when a security operation fails."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the error."""
        error_details = {"error_code": "ERR019", **(details or {})}
        super().__init__(message, details=error_details)


class VersionCompatibilityError(PepperError):
    """Error raised when version compatibility check fails."""

    def __init__(
        self, from_version, to_version, message: str, details: Optional[Dict] = None,
    ):
        """Initialize version compatibility error.

        Args:
            from_version: Source version
            to_version: Target version
            message: Error message
            details: Optional error details

        """
        super().__init__(
            message=message,
            details={
                "from_version": str(from_version) if from_version else None,
                "to_version": str(to_version) if to_version else None,
                **(details or {}),
            },
            error_code="ERR011",
        )


class VersionMigrationError(PepperError):
    """Error raised when version migration fails."""

    def __init__(
        self, from_version, to_version, message: str, details: Optional[Dict] = None,
    ):
        """Initialize version migration error.

        Args:
            from_version: Source version
            to_version: Target version
            message: Error message
            details: Optional error details

        """
        super().__init__(
            message=message,
            details={
                "from_version": str(from_version) if from_version else None,
                "to_version": str(to_version) if to_version else None,
                **(details or {}),
            },
            error_code="ERR012",
        )


class VersionParseError(PepperError):
    """Error raised when version parsing fails."""

    def __init__(self, version_str: str, message: str, details: Optional[Dict] = None):
        """Initialize version parse error.

        Args:
            version_str: Version string that failed to parse
            message: Error message
            details: Optional error details

        """
        super().__init__(
            message=message,
            details={
                "version_str": version_str,
                **(details or {}),
            },
            error_code="ERR013",
        )


class VersionValidationError(PepperError):
    """Error raised when version validation fails."""

    def __init__(self, version, message: str, details: Optional[Dict] = None):
        """Initialize version validation error.

        Args:
            version: Version that failed validation
            message: Error message
            details: Optional error details

        """
        super().__init__(
            message=message,
            details={
                "version": str(version) if version else None,
                **(details or {}),
            },
            error_code="ERR014",
        )


class VersionDependencyError(PepperError):
    """Error raised when version dependency check fails."""

    def __init__(
        self, version, dependency, message: str, details: Optional[Dict] = None,
    ):
        """Initialize version dependency error.

        Args:
            version: Version with dependency issue
            dependency: Dependency version
            message: Error message
            details: Optional error details

        """
        super().__init__(
            message=message,
            details={
                "version": str(version) if version else None,
                "dependency": str(dependency) if dependency else None,
                **(details or {}),
            },
            error_code="ERR015",
        )
