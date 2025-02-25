"""Lifecycle errors for the Pepperpy framework.

This module provides error classes for lifecycle operations.
"""

from typing import Any

from pepperpy.core.errors import PepperError
from pepperpy.core.lifecycle.types import LifecycleState


class LifecycleError(PepperError):
    """Base class for lifecycle errors."""

    def __init__(
        self,
        operation: str,
        details: dict[str, Any] | None = None,
        recovery_hint: str | None = None,
    ) -> None:
        """Initialize the error.

        Args:
            operation: Operation that failed
            details: Optional error details
            recovery_hint: Optional recovery hint
        """
        super().__init__(
            f"Lifecycle operation {operation} failed",
            details=details,
        )
        self.operation = operation
        self.recovery_hint = recovery_hint


class InvalidStateError(LifecycleError):
    """Error raised when a component is in an invalid state for an operation."""

    def __init__(
        self,
        operation: str,
        current_state: LifecycleState,
        expected_states: list[LifecycleState],
    ) -> None:
        """Initialize the error.

        Args:
            operation: Operation that failed
            current_state: Current component state
            expected_states: List of valid states for the operation
        """
        super().__init__(
            operation,
            details={
                "current_state": current_state,
                "expected_states": expected_states,
            },
            recovery_hint=f"Component must be in one of {expected_states} states to perform {operation}",
        )


class InvalidTransitionError(LifecycleError):
    """Error raised when attempting an invalid state transition."""

    def __init__(
        self,
        from_state: LifecycleState,
        to_state: LifecycleState,
        valid_transitions: list[tuple[LifecycleState, LifecycleState]] | None = None,
    ) -> None:
        """Initialize the error.

        Args:
            from_state: Current state
            to_state: Target state
            valid_transitions: Optional list of valid state transitions
        """
        super().__init__(
            "state_transition",
            details={
                "from_state": from_state,
                "to_state": to_state,
                "valid_transitions": valid_transitions,
            },
            recovery_hint=f"Cannot transition from {from_state} to {to_state}",
        )


class ComponentAlreadyExistsError(LifecycleError):
    """Error raised when a component already exists."""

    def __init__(self, component_name: str) -> None:
        """Initialize the error.

        Args:
            component_name: Name of the existing component
        """
        super().__init__(
            "register",
            details={"component": component_name},
            recovery_hint="Use a different component name or unregister the existing component",
        )


class ComponentNotFoundError(LifecycleError):
    """Error raised when a component is not found."""

    def __init__(self, component_name: str) -> None:
        """Initialize the error.

        Args:
            component_name: Name of the missing component
        """
        super().__init__(
            "lookup",
            details={"component": component_name},
            recovery_hint="Register the component before using it",
        )


class LifecycleOperationError(LifecycleError):
    """Error raised when a lifecycle operation fails."""

    def __init__(
        self,
        operation: str,
        component_name: str,
        error: Exception | None = None,
    ) -> None:
        """Initialize the error.

        Args:
            operation: Operation that failed
            component_name: Name of the component
            error: Optional underlying error
        """
        super().__init__(
            operation,
            details={
                "component": component_name,
                "error": str(error) if error else None,
            },
            recovery_hint="Check component logs for details",
        )


__all__ = [
    "ComponentAlreadyExistsError",
    "ComponentNotFoundError",
    "InvalidStateError",
    "InvalidTransitionError",
    "LifecycleError",
    "LifecycleOperationError",
]
