"""Lifecycle types module for the Pepperpy framework.

This module defines core lifecycle types used throughout the framework.
"""

from abc import abstractmethod
from enum import Enum
from typing import Protocol, TypeAlias


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


class Lifecycle(Protocol):
    """Protocol for components with lifecycle management."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the component.

        This method should be called before using the component.
        It should set up any necessary resources and put the component
        in a ready state.

        Raises:
            LifecycleError: If initialization fails
        """
        ...

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up the component.

        This method should be called when the component is no longer needed.
        It should release any resources and put the component in a cleaned state.

        Raises:
            LifecycleError: If cleanup fails
        """
        ...


# Export public API
__all__ = [
    "Lifecycle",
    "LifecycleState",
    "StateTransition",
]
