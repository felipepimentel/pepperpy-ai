"""Core base classes for PepperPy.

This module provides base classes and interfaces used throughout the PepperPy system.
"""

from abc import ABC, abstractmethod

from .types import ComponentState


class Lifecycle(ABC):
    """Base class for components with lifecycle management."""

    def __init__(self):
        """Initialize the lifecycle component."""
        self._state = ComponentState.UNREGISTERED

    @property
    def state(self) -> ComponentState:
        """Get the current state of the component."""
        return self._state

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the component.

        This method should be implemented by subclasses to perform any necessary
        initialization steps.
        """
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up the component.

        This method should be implemented by subclasses to perform any necessary
        cleanup steps before shutdown.
        """
        pass

    async def start(self) -> None:
        """Start the component.

        This method handles the transition to the RUNNING state and performs
        any necessary initialization.
        """
        try:
            self._state = ComponentState.INITIALIZING
            await self.initialize()
            self._state = ComponentState.RUNNING
        except Exception as e:
            self._state = ComponentState.ERROR
            raise RuntimeError(f"Failed to start component: {str(e)}") from e

    async def stop(self) -> None:
        """Stop the component.

        This method handles the transition to the UNREGISTERED state and performs
        any necessary cleanup.
        """
        try:
            self._state = ComponentState.SHUTTING_DOWN
            await self.cleanup()
            self._state = ComponentState.UNREGISTERED
        except Exception as e:
            self._state = ComponentState.ERROR
            raise RuntimeError(f"Failed to stop component: {str(e)}") from e
