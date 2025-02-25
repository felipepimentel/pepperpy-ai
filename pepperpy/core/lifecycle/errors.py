"""Lifecycle errors module for the Pepperpy framework.

This module defines lifecycle-related errors used throughout the framework.
"""

from pepperpy.core.errors import ComponentError


class LifecycleOperationError(ComponentError):
    """Error raised when a lifecycle operation fails."""

    pass


class InvalidStateError(ComponentError):
    """Error raised when a component is in an invalid state."""

    pass


class InvalidTransitionError(ComponentError):
    """Error raised when a state transition is invalid."""

    pass


# Export public API
__all__ = [
    "InvalidStateError",
    "InvalidTransitionError",
    "LifecycleOperationError",
]
