"""Lifecycle types module for the Pepperpy framework.

This module defines core lifecycle types used throughout the framework.
"""

from enum import Enum
from typing import TypeAlias


class LifecycleState(str, Enum):
    """Component lifecycle states."""

    CREATED = "created"
    INITIALIZING = "initializing"
    READY = "ready"
    EXECUTING = "executing"
    CLEANING = "cleaning"
    CLEANED = "cleaned"
    ERROR = "error"


# Type alias for state transitions
StateTransition: TypeAlias = tuple[LifecycleState, LifecycleState]


# Export public API
__all__ = [
    "LifecycleState",
    "StateTransition",
]
