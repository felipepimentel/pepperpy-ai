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
from typing import Any


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


@dataclass
class ErrorContext:
    """Context information for errors.

    Attributes:
        timestamp: Time the error occurred
        traceback: Stack trace at time of error
        operation: Operation being performed
        component: Component where error occurred
        details: Additional error details
    """

    timestamp: float = field(default_factory=time.time)
    traceback: str = ""
    operation: str = ""
    component: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Initialize error context."""
        if not self.traceback:
            self.traceback = traceback.format_exc()


class PepperpyError(Exception):
    """Base class for all Pepperpy errors."""

    def __init__(
        self,
        message: str,
        *,
        category: ErrorCategory = ErrorCategory.RUNTIME,
        error_code: str | None = None,
        recovery_hint: str | None = None,
        user_message: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the error.

        Args:
            message: The error message
            category: The category of the error
            error_code: Optional error code
            recovery_hint: Optional recovery hint
            user_message: Optional user-friendly message
            details: Optional dictionary with additional error details
        """
        super().__init__(message)
        self.message = message
        self.category = category
        self.error_code = error_code
        self.recovery_hint = recovery_hint
        self.user_message = user_message or message
        self.details = details or {}


class AdapterError(PepperpyError):
    """Raised when there is an error with a framework adapter."""

    def __init__(
        self,
        message: str,
        *,
        adapter_name: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the error.

        Args:
            message: The error message
            adapter_name: Name of the adapter that failed
            **kwargs: Additional error details
        """
        details = {"adapter_name": adapter_name} if adapter_name else {}
        super().__init__(
            message,
            category=ErrorCategory.SYSTEM,
            error_code="ADP001",
            details=details,
            **kwargs,
        )


class AuthenticationError(PepperpyError):
    """Raised when there is an authentication error."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        """Initialize the error.

        Args:
            message: The error message
            **kwargs: Additional error details
        """
        super().__init__(
            message,
            category=ErrorCategory.SECURITY,
            error_code="AUTH001",
            **kwargs,
        )


class AuthorizationError(PepperpyError):
    """Raised when there is an authorization error."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        """Initialize the error.

        Args:
            message: The error message
            **kwargs: Additional error details
        """
        super().__init__(
            message,
            category=ErrorCategory.SECURITY,
            error_code="AUTHZ001",
            **kwargs,
        )


class ConfigurationError(PepperpyError):
    """Error in configuration.

    Example:
        >>> raise ConfigurationError(
        ...     "Invalid API key",
        ...     config_key="api_key",
        ...     recovery_hint="Check your configuration file"
        ... )
    """

    def __init__(
        self,
        message: str,
        *,
        config_key: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the error.

        Args:
            message: Error message
            config_key: Configuration key that caused the error
            **kwargs: Additional error details
        """
        details = {"config_key": config_key} if config_key else {}
        super().__init__(
            message,
            category=ErrorCategory.SYSTEM,
            error_code="CFG001",
            details=details,
            **kwargs,
        )


class FactoryError(PepperpyError):
    """Error in factory operations.

    Example:
        >>> raise FactoryError(
        ...     "Failed to create component",
        ...     component_type="agent",
        ...     recovery_hint="Check component configuration"
        ... )
    """

    def __init__(
        self,
        message: str,
        *,
        component_type: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the error.

        Args:
            message: Error message
            component_type: Type of component that failed to be created
            **kwargs: Additional error details
        """
        details = {"component_type": component_type} if component_type else {}
        super().__init__(
            message,
            category=ErrorCategory.SYSTEM,
            error_code="FAC001",
            details=details,
            **kwargs,
        )


class NotFoundError(PepperpyError):
    """Error when a requested resource is not found.

    Example:
        >>> raise NotFoundError(
        ...     "Agent not found",
        ...     resource_type="agent",
        ...     resource_id="123",
        ...     recovery_hint="Check if the agent exists"
        ... )
    """

    def __init__(
        self,
        message: str,
        *,
        resource_type: str | None = None,
        resource_id: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the error.

        Args:
            message: Error message
            resource_type: Type of resource that was not found
            resource_id: ID of the resource that was not found
            **kwargs: Additional error details
        """
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id
        super().__init__(
            message,
            category=ErrorCategory.RESOURCE,
            error_code="NF001",
            details=details,
            **kwargs,
        )


class ProviderError(PepperpyError):
    """Error in provider operations.

    Example:
        >>> raise ProviderError(
        ...     "API rate limit exceeded",
        ...     provider_type="openai",
        ...     recovery_hint="Wait before retrying"
        ... )
    """

    def __init__(
        self,
        message: str,
        *,
        provider_name: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the error.

        Args:
            message: Error message
            provider_name: Name of the provider that failed
            **kwargs: Additional error details
        """
        details = {"provider_name": provider_name} if provider_name else {}
        super().__init__(
            message,
            category=ErrorCategory.SYSTEM,
            error_code="PROV001",
            details=details,
            **kwargs,
        )


class RuntimeError(PepperpyError):
    """Raised when there is a runtime error."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        """Initialize the error.

        Args:
            message: The error message
            **kwargs: Additional error details
        """
        super().__init__(
            message,
            category=ErrorCategory.RUNTIME,
            error_code="RT001",
            **kwargs,
        )


class ValidationError(PepperpyError):
    """Error in data validation.

    Example:
        >>> raise ValidationError(
        ...     "Invalid input format",
        ...     validation_type="schema",
        ...     recovery_hint="Check input format"
        ... )
    """

    def __init__(
        self,
        message: str,
        *,
        validation_type: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the error.

        Args:
            message: Error message
            validation_type: Type of validation that failed
            **kwargs: Additional error details
        """
        details = {"validation_type": validation_type} if validation_type else {}
        super().__init__(
            message,
            category=ErrorCategory.VALIDATION,
            error_code="VAL001",
            details=details,
            **kwargs,
        )


class MemoryError(PepperpyError):
    """Error in memory operations.

    Example:
        >>> raise MemoryError(
        ...     "Failed to store data",
        ...     store_name="redis",
        ...     recovery_hint="Check Redis connection"
        ... )
    """

    def __init__(
        self,
        message: str,
        *,
        store_name: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the error.

        Args:
            message: Error message
            store_name: Name of the memory store
            **kwargs: Additional error details
        """
        details = {"store_name": store_name} if store_name else {}
        super().__init__(
            message,
            category=ErrorCategory.SYSTEM,
            error_code="MEM001",
            details=details,
            **kwargs,
        )


class SecurityError(PepperpyError):
    """Error in security operations.

    Example:
        >>> raise SecurityError(
        ...     "Invalid authentication token",
        ...     security_type="jwt",
        ...     recovery_hint="Re-authenticate"
        ... )
    """

    def __init__(
        self,
        message: str,
        *,
        security_type: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the error.

        Args:
            message: The error message
            security_type: Type of security error
            **kwargs: Additional error details
        """
        details = {"security_type": security_type} if security_type else {}
        super().__init__(
            message,
            category=ErrorCategory.SECURITY,
            error_code="SEC001",
            details=details,
            **kwargs,
        )


class StateError(PepperpyError):
    """Error in state management.

    Example:
        >>> raise StateError(
        ...     "Invalid state transition",
        ...     current_state="ready",
        ...     target_state="running",
        ...     recovery_hint="Reset state"
        ... )
    """

    def __init__(
        self,
        message: str,
        *,
        current_state: str | None = None,
        target_state: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the error.

        Args:
            message: The error message
            current_state: Current state when error occurred
            target_state: Target state that failed to transition to
            **kwargs: Additional error details
        """
        details = {}
        if current_state:
            details["current_state"] = current_state
        if target_state:
            details["target_state"] = target_state
        super().__init__(
            message,
            error_code="STA001",
            category=ErrorCategory.RUNTIME,
            details=details,
            **kwargs,
        )


class NetworkError(PepperpyError):
    """Error in network operations.

    Example:
        >>> raise NetworkError(
        ...     "Connection timeout",
        ...     endpoint="api.example.com",
        ...     recovery_hint="Check network connection"
        ... )
    """

    def __init__(
        self,
        message: str,
        *,
        endpoint: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the error.

        Args:
            message: Error message
            endpoint: Network endpoint
            **kwargs: Additional error details
        """
        details = {"endpoint": endpoint} if endpoint else {}
        super().__init__(
            message,
            category=ErrorCategory.NETWORK,
            error_code="NET001",
            details=details,
            **kwargs,
        )


class ResourceError(PepperpyError):
    """Error in resource management.

    Example:
        >>> raise ResourceError(
        ...     "Out of memory",
        ...     resource_type="memory",
        ...     recovery_hint="Free up memory"
        ... )
    """

    def __init__(
        self,
        message: str,
        *,
        resource_type: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the error.

        Args:
            message: The error message
            resource_type: Type of resource that caused the error
            **kwargs: Additional error details
        """
        details = {"resource_type": resource_type} if resource_type else {}
        super().__init__(
            message,
            category=ErrorCategory.RESOURCE,
            error_code="RES001",
            details=details,
            **kwargs,
        )


class ContextError(PepperpyError):
    """Raised when there is an error in the execution context."""

    def __init__(
        self,
        message: str,
        *,
        context_id: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the error.

        Args:
            message: The error message
            context_id: ID of the context that caused the error
            **kwargs: Additional error details
        """
        details = {"context_id": context_id} if context_id else {}
        super().__init__(
            message,
            category=ErrorCategory.RUNTIME,
            error_code="CTX001",
            details=details,
            **kwargs,
        )


class LifecycleError(PepperpyError):
    """Raised when there is an error in agent lifecycle management."""

    def __init__(
        self,
        message: str,
        *,
        agent_id: str | None = None,
        state: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the error.

        Args:
            message: The error message
            agent_id: ID of the agent that failed
            state: State of the agent when the error occurred
            **kwargs: Additional error details
        """
        details = {}
        if agent_id:
            details["agent_id"] = agent_id
        if state:
            details["state"] = state
        super().__init__(
            message,
            category=ErrorCategory.RUNTIME,
            error_code="LIFE001",
            details=details,
            **kwargs,
        )


class OrchestratorError(PepperpyError):
    """Raised when there is an error in agent orchestration."""

    def __init__(
        self,
        message: str,
        *,
        orchestrator_id: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the error.

        Args:
            message: The error message
            orchestrator_id: ID of the orchestrator that failed
            **kwargs: Additional error details
        """
        details = {"orchestrator_id": orchestrator_id} if orchestrator_id else {}
        super().__init__(
            message,
            category=ErrorCategory.SYSTEM,
            error_code="ORCH001",
            details=details,
            **kwargs,
        )


class ShardingError(PepperpyError):
    """Raised when there is an error in shard management."""

    def __init__(
        self,
        message: str,
        *,
        shard_id: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the error.

        Args:
            message: The error message
            shard_id: ID of the shard that failed
            **kwargs: Additional error details
        """
        details = {"shard_id": shard_id} if shard_id else {}
        super().__init__(
            message,
            category=ErrorCategory.SYSTEM,
            error_code="SHARD001",
            details=details,
            **kwargs,
        )


class PlanningError(PepperpyError):
    """Raised when there is an error in planning operations.

    Example:
        >>> raise PlanningError(
        ...     "Failed to create plan",
        ...     plan_type="task",
        ...     recovery_hint="Check planning constraints"
        ... )
    """

    def __init__(
        self,
        message: str,
        *,
        plan_type: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the error.

        Args:
            message: Error message
            plan_type: Type of plan that failed
            **kwargs: Additional error details
        """
        details = {"plan_type": plan_type} if plan_type else {}
        super().__init__(
            message,
            category=ErrorCategory.PLANNING,
            error_code="PLN001",
            details=details,
            **kwargs,
        )


class ToolError(PepperpyError):
    """Error in tool operations.

    Example:
        >>> raise ToolError(
        ...     "Tool execution failed",
        ...     tool_name="code_search",
        ...     recovery_hint="Check tool configuration"
        ... )
    """

    def __init__(
        self,
        message: str,
        *,
        tool_name: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the error.

        Args:
            message: Error message
            tool_name: Name of the tool that failed
            **kwargs: Additional error details
        """
        details = {"tool_name": tool_name} if tool_name else {}
        super().__init__(
            message,
            category=ErrorCategory.TOOLS,
            error_code="TOOL001",
            details=details,
            **kwargs,
        )


class PermissionError(PepperpyError):
    """Error in permission checks.

    Example:
        >>> raise PermissionError(
        ...     "Operation not permitted",
        ...     operation="delete_file",
        ...     required_permission="write",
        ...     recovery_hint="Request elevated permissions"
        ... )
    """

    def __init__(
        self,
        message: str,
        *,
        operation: str | None = None,
        required_permission: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the error.

        Args:
            message: Error message
            operation: Operation that was denied
            required_permission: Permission that was required
            **kwargs: Additional error details
        """
        details = {}
        if operation:
            details["operation"] = operation
        if required_permission:
            details["required_permission"] = required_permission
        super().__init__(
            message,
            category=ErrorCategory.SECURITY,
            error_code="PERM001",
            details=details,
            **kwargs,
        )


class ReasoningError(PepperpyError):
    """Error in reasoning operations.

    Example:
        >>> raise ReasoningError(
        ...     "Failed to perform reasoning",
        ...     reasoning_type="deductive",
        ...     context=context,
        ...     recovery_hint="Check input format"
        ... )
    """

    def __init__(
        self,
        message: str,
        *,
        reasoning_type: str | None = None,
        context: Any | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the error.

        Args:
            message: Error message
            reasoning_type: Type of reasoning that failed
            context: Reasoning context when error occurred
            **kwargs: Additional error details
        """
        details = {}
        if reasoning_type:
            details["reasoning_type"] = reasoning_type
        if context:
            details["context"] = str(context)
        super().__init__(
            message,
            category=ErrorCategory.REASONING,
            error_code="RSN001",
            details=details,
            **kwargs,
        )


class LearningError(PepperpyError):
    """Error in learning operations.

    Example:
        >>> raise LearningError(
        ...     "Failed to train model",
        ...     learning_type="supervised",
        ...     context=context,
        ...     recovery_hint="Check training data format"
        ... )
    """

    def __init__(
        self,
        message: str,
        *,
        learning_type: str | None = None,
        context: Any | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the error.

        Args:
            message: Error message
            learning_type: Type of learning that failed
            context: Learning context when error occurred
            **kwargs: Additional error details
        """
        details = {}
        if learning_type:
            details["learning_type"] = learning_type
        if context:
            details["context"] = str(context)
        super().__init__(
            message,
            category=ErrorCategory.LEARNING,
            error_code="LRN001",
            details=details,
            **kwargs,
        )
