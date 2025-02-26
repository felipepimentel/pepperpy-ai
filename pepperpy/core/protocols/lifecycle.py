"""
Core lifecycle protocol module.

This module defines the protocol for component lifecycle management.
"""

from abc import abstractmethod
from typing import Protocol


class Lifecycle(Protocol):
    """Protocol defining the lifecycle of a component."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the component.

        This method should be called before the component is used and should
        set up any necessary resources or state.
        """
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup the component.

        This method should be called when the component is no longer needed
        and should clean up any resources used by the component.
        """
        pass

    @abstractmethod
    async def _initialize(self) -> None:
        """Internal initialization logic.

        This method should be implemented by subclasses to provide their
        specific initialization logic.
        """
        pass

    @abstractmethod
    async def _cleanup(self) -> None:
        """Internal cleanup logic.

        This method should be implemented by subclasses to provide their
        specific cleanup logic.
        """
        pass


# Export all types
__all__ = ["Lifecycle"]
