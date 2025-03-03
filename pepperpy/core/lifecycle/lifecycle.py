"""Lifecycle management for system components."""

import asyncio
import logging
from abc import ABC, abstractmethod
from enum import Enum

from pepperpy.core.errors import StateError


class LifecycleState(Enum):
    """Component lifecycle states."""

    CREATED = "created"
    INITIALIZING = "initializing"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class Lifecycle(ABC):
    """Base class for components with lifecycle management.

    This class provides a standard interface for managing component lifecycles,
    including initialization, startup, and shutdown procedures.
    """

    def __init__(self) -> None:
        """Initialize the lifecycle component."""
        self._state = LifecycleState.CREATED
        self._state_lock = asyncio.Lock()
        self._logger = logging.getLogger(self.__class__.__name__)
        self._stop_event: asyncio.Event | None = None

    @property
    def state(self) -> LifecycleState:
        """Get the current lifecycle state."""
        return self._state

    async def initialize(self) -> None:
        """Initialize the component.

        This method handles the transition from CREATED to RUNNING state,
        performing any necessary setup operations.

        Raises:
            StateError: If component is not in CREATED state

        """
        async with self._state_lock:
            if self._state != LifecycleState.CREATED:
                raise StateError(f"Cannot initialize component in {self._state} state")

            try:
                self._state = LifecycleState.INITIALIZING
                self._logger.info("Initializing component")

                # Create stop event
                self._stop_event = asyncio.Event()

                # Call implementation-specific initialization
                await self._initialize()

                self._state = LifecycleState.RUNNING
                self._logger.info("Component initialized and running")

            except Exception as e:
                self._state = LifecycleState.ERROR
                self._logger.error(
                    f"Failed to initialize component: {e}", exc_info=True,
                )
                raise

    async def stop(self) -> None:
        """Stop the component.

        This method handles the transition to STOPPED state, performing
        any necessary cleanup operations.

        Raises:
            StateError: If component is not in RUNNING state

        """
        async with self._state_lock:
            if self._state != LifecycleState.RUNNING:
                raise StateError(f"Cannot stop component in {self._state} state")

            try:
                self._state = LifecycleState.STOPPING
                self._logger.info("Stopping component")

                # Signal stop
                if self._stop_event:
                    self._stop_event.set()

                # Call implementation-specific cleanup
                await self._cleanup()

                self._state = LifecycleState.STOPPED
                self._logger.info("Component stopped")

            except Exception as e:
                self._state = LifecycleState.ERROR
                self._logger.error(f"Failed to stop component: {e}", exc_info=True)
                raise

    @abstractmethod
    async def _initialize(self) -> None:
        """Implementation-specific initialization.

        This method should be overridden by subclasses to perform any
        necessary initialization steps.
        """

    @abstractmethod
    async def _cleanup(self) -> None:
        """Implementation-specific cleanup.

        This method should be overridden by subclasses to perform any
        necessary cleanup steps.
        """

    def is_running(self) -> bool:
        """Check if the component is in RUNNING state."""
        return self._state == LifecycleState.RUNNING

    def is_stopped(self) -> bool:
        """Check if the component is in STOPPED state."""
        return self._state == LifecycleState.STOPPED

    def is_error(self) -> bool:
        """Check if the component is in ERROR state."""
        return self._state == LifecycleState.ERROR

    async def wait_until_stopped(self) -> None:
        """Wait until the component is stopped.

        This method blocks until the component transitions to STOPPED state,
        either through normal shutdown or error.
        """
        if self._stop_event:
            await self._stop_event.wait()

        while self._state not in (LifecycleState.STOPPED, LifecycleState.ERROR):
            await asyncio.sleep(0.1)
