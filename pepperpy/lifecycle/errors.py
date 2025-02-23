"""Lifecycle errors module.

This module provides error classes for the lifecycle system.
"""

from typing import Any

from pepperpy.core.errors import PepperError
from pepperpy.lifecycle.types import LifecycleState


class LifecycleError(PepperError):
    """Base class for lifecycle errors."""

    def __init__(
        self,
        message: str,
        component_id: str,
        state: LifecycleState,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize lifecycle error.

        Args:
            message: Error message
            component_id: Component ID
            state: Current state
            details: Optional error details
        """
        error_details = details or {}
        error_details.update({
            "component_id": component_id,
            "state": state.value,
            "error_code": "LIF000",
        })
        super().__init__(message, details=error_details)


class InitializationError(LifecycleError):
    """Error raised when initialization fails."""

    def __init__(
        self,
        message: str = "Initialization failed",
        component_id: str = "",
        state: LifecycleState = LifecycleState.UNINITIALIZED,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize initialization error.

        Args:
            message: Error message
            component_id: Component ID
            state: Current state
            details: Optional error details
        """
        error_details = details or {}
        error_details["error_code"] = "LIF001"
        super().__init__(message, component_id, state, error_details)


class StartError(LifecycleError):
    """Error raised when start fails."""

    def __init__(
        self,
        message: str = "Start failed",
        component_id: str = "",
        state: LifecycleState = LifecycleState.INITIALIZED,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize start error.

        Args:
            message: Error message
            component_id: Component ID
            state: Current state
            details: Optional error details
        """
        error_details = details or {}
        error_details["error_code"] = "LIF002"
        super().__init__(message, component_id, state, error_details)


class StopError(LifecycleError):
    """Error raised when stop fails."""

    def __init__(
        self,
        message: str = "Stop failed",
        component_id: str = "",
        state: LifecycleState = LifecycleState.RUNNING,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize stop error.

        Args:
            message: Error message
            component_id: Component ID
            state: Current state
            details: Optional error details
        """
        error_details = details or {}
        error_details["error_code"] = "LIF003"
        super().__init__(message, component_id, state, error_details)


class FinalizeError(LifecycleError):
    """Error raised when finalization fails."""

    def __init__(
        self,
        message: str = "Finalize failed",
        component_id: str = "",
        state: LifecycleState = LifecycleState.STOPPED,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize finalize error.

        Args:
            message: Error message
            component_id: Component ID
            state: Current state
            details: Optional error details
        """
        error_details = details or {}
        error_details["error_code"] = "LIF004"
        super().__init__(message, component_id, state, error_details)


class StateError(LifecycleError):
    """Error raised when state transition is invalid."""

    def __init__(
        self,
        message: str = "Invalid state transition",
        component_id: str = "",
        state: LifecycleState = LifecycleState.ERROR,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize state error.

        Args:
            message: Error message
            component_id: Component ID
            state: Current state
            details: Optional error details
        """
        error_details = details or {}
        error_details["error_code"] = "LIF005"
        super().__init__(message, component_id, state, error_details)


class HookError(LifecycleError):
    """Error raised when hook execution fails."""

    def __init__(
        self,
        message: str = "Hook execution failed",
        component_id: str = "",
        state: LifecycleState = LifecycleState.ERROR,
        hook_name: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize hook error.

        Args:
            message: Error message
            component_id: Component ID
            state: Current state
            hook_name: Optional hook name
            details: Optional error details
        """
        error_details = details or {}
        error_details["error_code"] = "LIF006"
        if hook_name:
            error_details["hook_name"] = hook_name
        super().__init__(message, component_id, state, error_details)


class TimeoutError(LifecycleError):
    """Error raised when operation times out."""

    def __init__(
        self,
        message: str = "Operation timed out",
        component_id: str = "",
        state: LifecycleState = LifecycleState.ERROR,
        operation: str | None = None,
        timeout: float | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize timeout error.

        Args:
            message: Error message
            component_id: Component ID
            state: Current state
            operation: Optional operation name
            timeout: Optional timeout value
            details: Optional error details
        """
        error_details = details or {}
        error_details["error_code"] = "LIF007"
        if operation:
            error_details["operation"] = operation
        if timeout:
            error_details["timeout"] = str(timeout)
        super().__init__(message, component_id, state, error_details)


class RetryError(LifecycleError):
    """Error raised when maximum retries exceeded."""

    def __init__(
        self,
        message: str = "Maximum retries exceeded",
        component_id: str = "",
        state: LifecycleState = LifecycleState.ERROR,
        operation: str | None = None,
        max_retries: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize retry error.

        Args:
            message: Error message
            component_id: Component ID
            state: Current state
            operation: Optional operation name
            max_retries: Optional maximum retries
            details: Optional error details
        """
        error_details = details or {}
        error_details["error_code"] = "LIF008"
        if operation:
            error_details["operation"] = operation
        if max_retries:
            error_details["max_retries"] = str(max_retries)
        super().__init__(message, component_id, state, error_details)
