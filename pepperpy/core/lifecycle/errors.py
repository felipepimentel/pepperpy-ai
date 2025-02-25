"""Error classes for the lifecycle module.

This module provides error classes specific to lifecycle operations.
"""

from pepperpy.core.errors import LifecycleError


class InvalidStateError(LifecycleError):
    """Error raised when a component is in an invalid state."""


class InvalidTransitionError(LifecycleError):
    """Error raised when a state transition is invalid."""


class LifecycleOperationError(LifecycleError):
    """Error raised when a lifecycle operation fails."""


# Export public API
__all__ = [
    "InvalidStateError",
    "InvalidTransitionError",
    "LifecycleOperationError",
]
