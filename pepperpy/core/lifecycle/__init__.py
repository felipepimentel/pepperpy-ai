"""Lifecycle management module.

This module provides lifecycle management functionality for components.
"""

from pepperpy.core.lifecycle.base import LifecycleComponent as Lifecycle
from pepperpy.core.lifecycle.errors import (
    InvalidStateError,
    InvalidTransitionError,
    LifecycleOperationError,
)
from pepperpy.core.lifecycle.types import LifecycleState, StateTransition

__all__ = [
    "Lifecycle",
    "LifecycleState",
    "StateTransition",
    "InvalidStateError",
    "InvalidTransitionError",
    "LifecycleOperationError",
]
