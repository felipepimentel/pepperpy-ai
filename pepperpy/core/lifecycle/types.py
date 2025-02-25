"""Lifecycle types module for the Pepperpy framework.

This module defines core lifecycle types used throughout the framework.
"""

from abc import abstractmethod
from enum import Enum
from typing import Protocol, TypeVar
from typing_extensions import TypeAlias


class LifecycleState(str, Enum):
    """Component lifecycle states."""

    UNREGISTERED = "unregistered"
    CREATED = "created"
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    CLEANING = "cleaning"
    CLEANED = "cleaned"
    EXECUTING = "executing"


class StateTransition:
    """State transition definition."""

    def __init__(self, from_state: LifecycleState, to_state: LifecycleState, description: str = "") -> None:
        """Initialize state transition.

        Args:
            from_state: Source state
            to_state: Target state
            description: Optional transition description
        """
        self.from_state = from_state
        self.to_state = to_state
        self.description = description


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
