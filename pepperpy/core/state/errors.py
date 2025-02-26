"""Custom exceptions for the state management system.

This module defines custom exceptions used by the state management system
to handle various error scenarios during state transitions and validation.
"""

from .types import State


class StateError(Exception):
    """Base class for all state management related errors.

    Example:
        >>> try:
        ...     raise StateError("Generic state error")
        ... except StateError as e:
        ...     print(str(e))
        Generic state error
    """

    pass


class InvalidStateTransitionError(StateError):
    """Raised when attempting an invalid state transition.

    Args:
        current_state (State): The current state.
        target_state (State): The target state that was invalid.
        message (Optional[str]): Optional custom error message.

    Example:
        >>> try:
        ...     raise InvalidStateTransitionError(
        ...         State.UNREGISTERED,
        ...         State.RUNNING,
        ...         "Must be REGISTERED first"
        ...     )
        ... except InvalidStateTransitionError as e:
        ...     print(str(e))
        Invalid transition from UNREGISTERED to RUNNING: Must be REGISTERED first
    """

    def __init__(
        self, current_state: State, target_state: State, message: str | None = None
    ):
        self.current_state = current_state
        self.target_state = target_state
        self.message = (
            message
            or f"Invalid transition from {current_state.name} to {target_state.name}"
        )
        super().__init__(self.message)


class StateValidationError(StateError):
    """Raised when state validation fails.

    Args:
        state (State): The state that failed validation.
        reason (str): The reason for validation failure.

    Example:
        >>> try:
        ...     raise StateValidationError(
        ...         State.READY,
        ...         "Required dependencies not initialized"
        ...     )
        ... except StateValidationError as e:
        ...     print(str(e))
        State READY validation failed: Required dependencies not initialized
    """

    def __init__(self, state: State, reason: str):
        self.state = state
        self.reason = reason
        self.message = f"State {state.name} validation failed: {reason}"
        super().__init__(self.message)


class StateHookError(StateError):
    """Raised when a state transition hook fails.

    Args:
        hook_type (str): The type of hook that failed (pre/post/error).
        state (State): The state during which the hook failed.
        original_error (Exception): The original error that occurred.

    Example:
        >>> try:
        ...     raise StateHookError(
        ...         "pre_transition",
        ...         State.INITIALIZING,
        ...         ValueError("Invalid config")
        ...     )
        ... except StateHookError as e:
        ...     print(str(e))
        Hook pre_transition failed for state INITIALIZING: Invalid config
    """

    def __init__(self, hook_type: str, state: State, original_error: Exception):
        self.hook_type = hook_type
        self.state = state
        self.original_error = original_error
        self.message = (
            f"Hook {hook_type} failed for state {state.name}: {original_error!s}"
        )
        super().__init__(self.message)


__all__ = [
    "InvalidStateTransitionError",
    "StateError",
    "StateHookError",
    "StateValidationError",
]
