"""Base lifecycle module for the Pepperpy framework.

This module provides core lifecycle functionality including:
- Component lifecycle management
- State transitions
- Error handling
"""

from __future__ import annotations

import logging
from typing import ClassVar

from pepperpy.core.errors import LifecycleError, StateError
from pepperpy.core.lifecycle.types import Lifecycle, LifecycleState, StateTransition


class LifecycleComponent(Lifecycle):
    """Base class for components with lifecycle management."""

    # Define allowed state transitions
    _transitions: ClassVar[list[StateTransition]] = [
        StateTransition(LifecycleState.CREATED, LifecycleState.INITIALIZING),
        StateTransition(LifecycleState.INITIALIZING, LifecycleState.READY),
        StateTransition(LifecycleState.INITIALIZING, LifecycleState.ERROR),
        StateTransition(LifecycleState.READY, LifecycleState.CLEANING),
        StateTransition(LifecycleState.READY, LifecycleState.ERROR),
        StateTransition(LifecycleState.CLEANING, LifecycleState.CLEANED),
        StateTransition(LifecycleState.CLEANING, LifecycleState.ERROR),
    ]

    def __init__(self, name: str) -> None:
        """Initialize component.

        Args:
            name: Component name
        """
        self.name = name
        self._state = LifecycleState.CREATED
        self.logger = logging.getLogger(f"{__name__}.{name}")

    def _validate_transition(self, to_state: LifecycleState) -> None:
        """Validate state transition.

        Args:
            to_state: Target state

        Raises:
            StateError: If transition is not allowed
        """
        transition = StateTransition(self._state, to_state)
        if not any(t == transition for t in self._transitions):
            raise StateError(
                f"Invalid state transition for {self.name}: {self._state} -> {to_state}",
                recovery_hint="Check component lifecycle documentation for valid transitions.",
            )

    async def initialize(self) -> None:
        """Initialize component.

        Raises:
            LifecycleError: If initialization fails
            StateError: If state transition is invalid
        """
        try:
            self._validate_transition(LifecycleState.INITIALIZING)
            self._state = LifecycleState.INITIALIZING
            self.logger.debug(f"Initializing {self.name}")
            await self._initialize()
            self._validate_transition(LifecycleState.READY)
            self._state = LifecycleState.READY
            self.logger.debug(f"Initialized {self.name}")
        except Exception as e:
            self._state = LifecycleState.ERROR
            raise LifecycleError(
                f"Failed to initialize {self.name}: {e}",
                recovery_hint="Check component initialization requirements and try again.",
            ) from e

    async def cleanup(self) -> None:
        """Clean up component.

        Raises:
            LifecycleError: If cleanup fails
            StateError: If state transition is invalid
        """
        try:
            self._validate_transition(LifecycleState.CLEANING)
            self._state = LifecycleState.CLEANING
            self.logger.debug(f"Cleaning up {self.name}")
            await self._cleanup()
            self._validate_transition(LifecycleState.CLEANED)
            self._state = LifecycleState.CLEANED
            self.logger.debug(f"Cleaned up {self.name}")
        except Exception as e:
            self._state = LifecycleState.ERROR
            raise LifecycleError(
                f"Failed to clean up {self.name}: {e}",
                recovery_hint="Check component cleanup requirements and try again.",
            ) from e

    async def _initialize(self) -> None:
        """Initialize component implementation.

        This method should be overridden by subclasses to perform
        component-specific initialization.
        """
        pass

    async def _cleanup(self) -> None:
        """Clean up component implementation.

        This method should be overridden by subclasses to perform
        component-specific cleanup.
        """
        pass


# Export public API
__all__ = [
    "LifecycleComponent",
]
