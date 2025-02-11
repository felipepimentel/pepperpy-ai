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


class ErrorContext(TypedDict, total=False):
    """Type definition for error context information."""

    error_type: str
    error_code: str
    details: dict[str, Any]
    source: str
    timestamp: str


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
        error_type: Type of error that occurred
        details: Additional error details
        user_message: User-friendly error message
        recovery_hint: Hint for recovering from the error
        context: Error context information

    """

    def __init__(
        self,
        message: str,
        *,
        category: ErrorCategory = ErrorCategory.RUNTIME,
        error_code: str | None = None,
        details: dict[str, Any] | None = None,
        user_message: str | None = None,
        recovery_hint: str | None = None,
        context: ErrorContext | None = None,
    ) -> None:
        """Initialize the error.

        Args:
        ----
            message: Error message
            category: Error category
            error_code: Error code
            details: Additional error details
            user_message: User-friendly error message
            recovery_hint: Hint for recovering from the error
            context: Error context information

        """
        super().__init__(message)
        self.message = message
        self.category = category
        self.error_code = error_code
        self.details = details or {}
        self.user_message = user_message or message
        self.recovery_hint = recovery_hint
        self.context = context or ErrorContext()
        self.metadata = ErrorMetadata()

    def __str__(self) -> str:
        """Return string representation of error."""
        parts = [self.message]
        if self.user_message:
            parts.append(f"User Message: {self.user_message}")
        if self.recovery_hint:
            parts.append(f"Recovery Hint: {self.recovery_hint}")
        if self.details:
            parts.append(f"Details: {self.details}")
        return " | ".join(parts)


class ValidationError(PepperpyError):
    """Raised when input validation fails."""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        code: str = "VALIDATION_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the validation error.

        Args:
        ----
            message: Error message
            field: Optional name of the field that failed validation
            value: Optional invalid value
            code: Error code
            details: Optional additional error details

        """
        super().__init__(message, error_code=code, details=details)
        self.field = field
        self.value = value


class StateError(PepperpyError):
    """Raised when an operation is invalid for the current state."""

    def __init__(
        self,
        message: str,
        *,
        current_state: str | None = None,
        expected_state: str | None = None,
        details: dict[str, Any] | None = None,
        user_message: str | None = None,
        recovery_hint: str | None = None,
        context: ErrorContext | None = None,
    ) -> None:
        """Initialize the error.

        Args:
        ----
            message: Error message
            current_state: Current state when error occurred
            expected_state: Expected state for operation
            details: Additional error details
            user_message: User-friendly error message
            recovery_hint: Hint for recovering from the error
            context: Error context information

        """
        details = details or {}
        if current_state:
            details["current_state"] = current_state
        if expected_state:
            details["expected_state"] = expected_state

        super().__init__(
            message,
            category=ErrorCategory.RUNTIME,
            error_code="STE001",
            details=details,
            user_message=user_message,
            recovery_hint=recovery_hint,
            context=context,
        )


class ConfigurationError(PepperpyError):
    """Raised when there is an error in configuration."""

    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        code: str = "CONFIG_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the configuration error.

        Args:
        ----
            message: Error message
            config_key: Optional configuration key that caused the error
            code: Error code
            details: Optional additional error details

        """
        super().__init__(message, error_code=code, details=details)
        self.config_key = config_key


class ProviderError(PepperpyError):
    """Raised when there is a provider-related error."""

    def __init__(
        self,
        message: str,
        *,
        provider: str | None = None,
        operation: str | None = None,
        details: dict[str, Any] | None = None,
        user_message: str | None = None,
        recovery_hint: str | None = None,
        context: ErrorContext | None = None,
    ) -> None:
        """Initialize the error.

        Args:
        ----
            message: Error message
            provider: Provider that caused the error
            operation: Operation that failed
            details: Additional error details
            user_message: User-friendly error message
            recovery_hint: Hint for recovering from the error
            context: Error context information

        """
        details = details or {}
        if provider:
            details["provider"] = provider
        if operation:
            details["operation"] = operation

        super().__init__(
            message,
            category=ErrorCategory.RUNTIME,
            error_code="PRV001",
            details=details,
            user_message=user_message,
            recovery_hint=recovery_hint,
            context=context,
        )


class RuntimeError(PepperpyError):
    """Raised when there is a runtime error."""

    def __init__(
        self,
        message: str,
        *,
        details: dict[str, Any] | None = None,
        user_message: str | None = None,
        recovery_hint: str | None = None,
        context: ErrorContext | None = None,
    ) -> None:
        """Initialize the error.

        Args:
        ----
            message: Error message
            details: Additional error details
            user_message: User-friendly error message
            recovery_hint: Hint for recovering from the error
            context: Error context information

        """
        super().__init__(
            message,
            category=ErrorCategory.RUNTIME,
            error_code="RUN001",
            details=details,
            user_message=user_message,
            recovery_hint=recovery_hint,
            context=context,
        )


class ToolError(PepperpyError):
    """Raised when there is a tool-related error."""

    def __init__(
        self,
        message: str,
        *,
        tool_name: str | None = None,
        operation: str | None = None,
        details: dict[str, Any] | None = None,
        user_message: str | None = None,
        recovery_hint: str | None = None,
        context: ErrorContext | None = None,
    ) -> None:
        """Initialize the error.

        Args:
        ----
            message: Error message
            tool_name: Name of the tool that caused the error
            operation: Operation that failed
            details: Additional error details
            user_message: User-friendly error message
            recovery_hint: Hint for recovering from the error
            context: Error context information

        """
        details = details or {}
        if tool_name:
            details["tool_name"] = tool_name
        if operation:
            details["operation"] = operation

        super().__init__(
            message,
            category=ErrorCategory.TOOLS,
            error_code="TOOL001",
            details=details,
            user_message=user_message,
            recovery_hint=recovery_hint,
            context=context,
        )


class PermissionError(PepperpyError):
    """Raised when there is a permission-related error."""

    def __init__(
        self,
        message: str,
        *,
        resource: str | None = None,
        action: str | None = None,
        details: dict[str, Any] | None = None,
        user_message: str | None = None,
        recovery_hint: str | None = None,
        context: ErrorContext | None = None,
    ) -> None:
        """Initialize the error.

        Args:
        ----
            message: Error message
            resource: Resource that was being accessed
            action: Action that was attempted
            details: Additional error details
            user_message: User-friendly error message
            recovery_hint: Hint for recovering from the error
            context: Error context information

        """
        details = details or {}
        if resource:
            details["resource"] = resource
        if action:
            details["action"] = action

        super().__init__(
            message,
            category=ErrorCategory.SECURITY,
            error_code="SEC001",
            details=details,
            user_message=user_message,
            recovery_hint=recovery_hint,
            context=context,
        )


class ContextError(PepperpyError):
    """Error raised when there is an issue with context management."""

    def __init__(self, message: str, context: ErrorContext | None = None) -> None:
        """Initialize the error.

        Args:
        ----
            message: The error message
            context: Optional context information about the error

        """
        super().__init__(message)
        self.context = context or ErrorContext()


class LifecycleError(PepperpyError):
    """Error raised when there is an issue with component lifecycle management."""

    def __init__(self, message: str, component: str, state: str | None = None) -> None:
        """Initialize the error.

        Args:
        ----
            message: The error message
            component: The name of the component that encountered the error
            state: Optional lifecycle state when the error occurred

        """
        super().__init__(message)
        self.component = component
        self.state = state


class FactoryError(PepperpyError):
    """Error raised when there is an issue with component factory operations."""

    def __init__(
        self, message: str, component_type: str, config: dict[str, Any] | None = None
    ) -> None:
        """Initialize the error.

        Args:
        ----
            message: The error message
            component_type: The type of component that failed to be created
            config: Optional configuration that caused the error

        """
        super().__init__(message)
        self.component_type = component_type
        self.config = config or {}


class OrchestratorError(PepperpyError):
    """Error raised when there is an issue with task orchestration."""

    def __init__(
        self,
        message: str,
        task_id: str | None = None,
        state: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the error.

        Args:
        ----
            message: The error message
            task_id: Optional ID of the task that encountered the error
            state: Optional orchestrator state when the error occurred

        """
        super().__init__(message)
        self.task_id = task_id
        self.state = state or {}


class ShardingError(PepperpyError):
    """Error raised when there is an issue with data sharding operations."""

    def __init__(
        self, message: str, shard_key: str | None = None, operation: str | None = None
    ) -> None:
        """Initialize the error.

        Args:
        ----
            message: The error message
            shard_key: Optional key used for sharding that caused the error
            operation: Optional operation that failed

        """
        super().__init__(message)
        self.shard_key = shard_key
        self.operation = operation


class ResourceNotFoundError(PepperpyError):
    """Raised when a requested resource is not found."""

    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        code: str = "NOT_FOUND",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the resource not found error.

        Args:
        ----
            message: Error message
            resource_type: Optional type of resource that was not found
            resource_id: Optional ID of the resource that was not found
            code: Error code
            details: Optional additional error details

        """
        super().__init__(message, error_code=code, details=details)
        self.resource_type = resource_type
        self.resource_id = resource_id


class OperationError(PepperpyError):
    """Raised when an operation fails."""

    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        code: str = "OPERATION_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the operation error.

        Args:
        ----
            message: Error message
            operation: Optional name of the operation that failed
            code: Error code
            details: Optional additional error details

        """
        super().__init__(message, error_code=code, details=details)
        self.operation = operation


class RegistryError(PepperpyError):
    """Raised when there is a registry-related error."""

    def __init__(
        self,
        message: str,
        *,
        registry_name: str | None = None,
        operation: str | None = None,
        details: dict[str, Any] | None = None,
        user_message: str | None = None,
        recovery_hint: str | None = None,
        context: ErrorContext | None = None,
    ) -> None:
        """Initialize the error.

        Args:
        ----
            message: Error message
            registry_name: Name of the registry where the error occurred
            operation: Operation that failed
            details: Additional error details
            user_message: User-friendly error message
            recovery_hint: Hint for recovering from the error
            context: Error context information

        """
        details = details or {}
        if registry_name:
            details["registry_name"] = registry_name
        if operation:
            details["operation"] = operation

        super().__init__(
            message,
            category=ErrorCategory.SYSTEM,
            error_code="REG001",
            details=details,
            user_message=user_message,
            recovery_hint=recovery_hint,
            context=context,
        )


class LearningError(PepperpyError):
    """Raised when there is a learning-related error."""

    def __init__(
        self,
        message: str,
        *,
        context: Any | None = None,
        details: dict[str, Any] | None = None,
        user_message: str | None = None,
        recovery_hint: str | None = None,
    ) -> None:
        """Initialize the error.

        Args:
        ----
            message: Error message
            context: Learning context that caused the error
            details: Additional error details
            user_message: User-friendly error message
            recovery_hint: Hint for recovering from the error

        """
        error_context = (
            ErrorContext(
                error_type="learning_error",
                details={"learning_context": str(context)} if context else {},
            )
            if context
            else None
        )

        super().__init__(
            message,
            category=ErrorCategory.LEARNING,
            error_code="LRN001",
            details=details,
            user_message=user_message,
            recovery_hint=recovery_hint,
            context=error_context,
        )


class WorkflowError(PepperpyError):
    """Raised when there is a workflow-related error."""

    pass


class AgentError(PepperpyError):
    """Raised when there is an agent-related error."""

    pass
