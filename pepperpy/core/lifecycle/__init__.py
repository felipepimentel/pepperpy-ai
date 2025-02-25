"""Lifecycle management module.

This module provides lifecycle management functionality for components.
"""

from pepperpy.core.lifecycle.base import LifecycleComponent
from pepperpy.core.lifecycle.errors import (
    InvalidStateError,
    InvalidTransitionError,
    LifecycleOperationError,
)
from pepperpy.core.lifecycle.manager import LifecycleManager
from pepperpy.core.lifecycle.types import LifecycleState, StateTransition
from pepperpy.core.protocols.lifecycle import Lifecycle

__all__ = [
    "InvalidStateError",
    "InvalidTransitionError",
    "Lifecycle",
    "LifecycleComponent",
    "LifecycleManager",
    "LifecycleOperationError",
    "LifecycleState",
    "StateTransition",
]
