"""
Error classes for the lifecycle management system.
"""

from pepperpy.core.errors import PepperpyError
from pepperpy.core.lifecycle.types import LifecycleState


class LifecycleError(PepperpyError):
    """Base error class for lifecycle-related errors."""

    pass


class InvalidStateError(LifecycleError):
    """Error raised when a component is in an invalid state."""

    def __init__(
        self, current_state: LifecycleState, expected_states: list[LifecycleState]
    ):
        self.current_state = current_state
        self.expected_states = expected_states
        super().__init__(
            f"Invalid state: {current_state}. Expected one of: {[str(s) for s in expected_states]}"
        )


class InvalidTransitionError(LifecycleError):
    """Error raised when an invalid state transition is attempted."""

    def __init__(self, from_state: LifecycleState, to_state: LifecycleState):
        self.from_state = from_state
        self.to_state = to_state
        super().__init__(f"Invalid transition from {from_state} to {to_state}")


class ComponentNotFoundError(LifecycleError):
    """Error raised when a component is not found in the pool."""

    def __init__(self, component_name: str):
        self.component_name = component_name
        super().__init__(f"Component not found: {component_name}")


class ComponentAlreadyExistsError(LifecycleError):
    """Error raised when attempting to register a component that already exists."""

    def __init__(self, component_name: str):
        self.component_name = component_name
        super().__init__(f"Component already exists: {component_name}")


class LifecycleOperationError(LifecycleError):
    """Error raised when a lifecycle operation fails."""

    def __init__(self, operation: str, component_name: str, error: Exception):
        self.operation = operation
        self.component_name = component_name
        self.original_error = error
        super().__init__(
            f"Lifecycle operation '{operation}' failed for component '{component_name}': {error!s}"
        )
