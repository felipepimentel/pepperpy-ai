"""Base lifecycle module.

This module provides the core lifecycle management functionality.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Protocol

from pepperpy.core.errors.unified import (
    LifecycleError,
    StateError,
)


class LifecycleState(Enum):
    """Component lifecycle states."""

    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    INITIALIZED = "initialized"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FINALIZING = "finalizing"
    FINALIZED = "finalized"
    ERROR = "error"


class LifecycleTransition:
    """Represents a state transition in the lifecycle."""

    def __init__(self, from_state: LifecycleState, to_state: LifecycleState) -> None:
        """Initialize transition.

        Args:
            from_state: Starting state
            to_state: Target state
        """
        self.from_state = from_state
        self.to_state = to_state
        self.timestamp = datetime.utcnow()
        self.error: Exception | None = None

    def __str__(self) -> str:
        """Get string representation.

        Returns:
            String representation of transition
        """
        return f"{self.from_state.value} -> {self.to_state.value}"


class LifecycleHook(Protocol):
    """Protocol for lifecycle hooks."""

    async def pre_initialize(self, component: Any) -> None:
        """Called before initialization.

        Args:
            component: Component being initialized
        """
        ...

    async def post_initialize(self, component: Any) -> None:
        """Called after initialization.

        Args:
            component: Component that was initialized
        """
        ...

    async def pre_cleanup(self, component: Any) -> None:
        """Called before cleanup.

        Args:
            component: Component being cleaned up
        """
        ...

    async def post_cleanup(self, component: Any) -> None:
        """Called after cleanup.

        Args:
            component: Component that was cleaned up
        """
        ...

    async def on_error(self, component: Any, error: Exception) -> None:
        """Called when an error occurs.

        Args:
            component: Component that had an error
            error: The error that occurred
        """
        ...


class Lifecycle(Protocol):
    """Protocol for components with lifecycle management."""

    @property
    def state(self) -> LifecycleState:
        """Get current state.

        Returns:
            Current lifecycle state
        """
        ...

    @property
    def transitions(self) -> list[LifecycleTransition]:
        """Get transition history.

        Returns:
            List of state transitions
        """
        ...

    @property
    def hooks(self) -> set[LifecycleHook]:
        """Get registered hooks.

        Returns:
            Set of lifecycle hooks
        """
        ...

    @property
    def metadata(self) -> dict[str, Any]:
        """Get component metadata.

        Returns:
            Dictionary of metadata
        """
        ...

    async def initialize(self, timeout: float | None = None) -> None:
        """Initialize the component.

        Args:
            timeout: Optional timeout in seconds

        Raises:
            ComponentError: If initialization fails
            PepperpyTimeoutError: If initialization times out
            StateError: If in invalid state
        """
        ...

    async def cleanup(self, timeout: float | None = None) -> None:
        """Clean up the component.

        Args:
            timeout: Optional timeout in seconds

        Raises:
            ComponentError: If cleanup fails
            PepperpyTimeoutError: If cleanup times out
            StateError: If in invalid state
        """
        ...

    async def wait_ready(self, timeout: float | None = None) -> None:
        """Wait for component to be ready.

        Args:
            timeout: Optional timeout in seconds

        Raises:
            PepperpyTimeoutError: If wait times out
            StateError: If component enters error state
        """
        ...

    def add_hook(self, hook: LifecycleHook) -> None:
        """Add lifecycle hook.

        Args:
            hook: Hook to add
        """
        ...

    def remove_hook(self, hook: LifecycleHook) -> None:
        """Remove lifecycle hook.

        Args:
            hook: Hook to remove
        """
        ...


class LifecycleComponent(ABC):
    """Base class for components with lifecycle management."""

    def __init__(self, name: str) -> None:
        """Initialize the component.

        Args:
            name: The name of the component.
        """
        self.name = name
        self._state = LifecycleState.UNINITIALIZED
        self._transitions: list[LifecycleTransition] = []
        self._hooks: set[LifecycleHook] = set()
        self._metadata: dict[str, Any] = {
            "name": name,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

    @property
    def state(self) -> LifecycleState:
        """Get current state."""
        return self._state

    @property
    def transitions(self) -> list[LifecycleTransition]:
        """Get transition history."""
        return self._transitions.copy()

    @property
    def hooks(self) -> set[LifecycleHook]:
        """Get registered hooks."""
        return self._hooks.copy()

    @property
    def metadata(self) -> dict[str, Any]:
        """Get component metadata."""
        return self._metadata.copy()

    def add_hook(self, hook: LifecycleHook) -> None:
        """Add lifecycle hook."""
        self._hooks.add(hook)

    def remove_hook(self, hook: LifecycleHook) -> None:
        """Remove lifecycle hook."""
        self._hooks.discard(hook)

    async def initialize(self, timeout: float | None = None) -> None:
        """Initialize the component.

        Args:
            timeout: Optional timeout in seconds

        Raises:
            ComponentError: If initialization fails
            PepperpyTimeoutError: If initialization times out
            StateError: If in invalid state
        """
        if self._state != LifecycleState.UNINITIALIZED:
            raise StateError(
                message=f"Component {self.name} is not in uninitialized state",
                component_id=self.name,
                current_state=self._state.value,
                target_state=LifecycleState.INITIALIZING.value,
            )

        transition = LifecycleTransition(self._state, LifecycleState.INITIALIZING)
        self._transitions.append(transition)
        self._state = LifecycleState.INITIALIZING
        self._metadata["updated_at"] = datetime.utcnow()

        try:
            # Call pre-initialize hooks
            for hook in self._hooks:
                await hook.pre_initialize(self)

            # Initialize component
            await self._initialize()

            # Call post-initialize hooks
            for hook in self._hooks:
                await hook.post_initialize(self)

            self._state = LifecycleState.INITIALIZED
            self._metadata["updated_at"] = datetime.utcnow()
            self._transitions.append(
                LifecycleTransition(LifecycleState.INITIALIZING, self._state)
            )

        except Exception as e:
            transition.error = e
            self._state = LifecycleState.ERROR
            self._metadata["updated_at"] = datetime.utcnow()
            self._metadata["error"] = str(e)
            self._transitions.append(
                LifecycleTransition(LifecycleState.INITIALIZING, self._state)
            )

            # Call error hooks
            for hook in self._hooks:
                await hook.on_error(self, e)

            raise LifecycleError(
                message=f"Failed to initialize component {self.name}: {e}",
                component_id=self.name,
                state=self._state.value,
                operation="initialize",
                details={"error": str(e)},
            ) from e

    async def cleanup(self, timeout: float | None = None) -> None:
        """Clean up the component.

        Args:
            timeout: Optional timeout in seconds

        Raises:
            ComponentError: If cleanup fails
            PepperpyTimeoutError: If cleanup times out
            StateError: If in invalid state
        """
        if self._state not in {LifecycleState.INITIALIZED, LifecycleState.ERROR}:
            raise StateError(
                message=f"Component {self.name} cannot be cleaned up from state {self._state}",
                component_id=self.name,
                current_state=self._state.value,
                target_state=LifecycleState.FINALIZING.value,
            )

        transition = LifecycleTransition(self._state, LifecycleState.FINALIZING)
        self._transitions.append(transition)
        self._state = LifecycleState.FINALIZING
        self._metadata["updated_at"] = datetime.utcnow()

        try:
            # Call pre-cleanup hooks
            for hook in self._hooks:
                await hook.pre_cleanup(self)

            # Clean up component
            await self._cleanup()

            # Call post-cleanup hooks
            for hook in self._hooks:
                await hook.post_cleanup(self)

            self._state = LifecycleState.FINALIZED
            self._metadata["updated_at"] = datetime.utcnow()
            self._transitions.append(
                LifecycleTransition(LifecycleState.FINALIZING, self._state)
            )

        except Exception as e:
            transition.error = e
            self._state = LifecycleState.ERROR
            self._metadata["updated_at"] = datetime.utcnow()
            self._metadata["error"] = str(e)
            self._transitions.append(
                LifecycleTransition(LifecycleState.FINALIZING, self._state)
            )

            # Call error hooks
            for hook in self._hooks:
                await hook.on_error(self, e)

            raise LifecycleError(
                message=f"Failed to clean up component {self.name}: {e}",
                component_id=self.name,
                state=self._state.value,
                operation="cleanup",
                details={"error": str(e)},
            ) from e

    async def wait_ready(self, timeout: float | None = None) -> None:
        """Wait for component to be ready.

        Args:
            timeout: Optional timeout in seconds

        Raises:
            PepperpyTimeoutError: If wait times out
            StateError: If component enters error state
        """
        if self._state == LifecycleState.ERROR:
            raise StateError(
                message=f"Component {self.name} is in error state",
                component_id=self.name,
                current_state=self._state.value,
            )

        if self._state == LifecycleState.INITIALIZED:
            return

        # TODO: Implement actual waiting with timeout
        raise NotImplementedError("wait_ready not implemented")

    @abstractmethod
    async def _initialize(self) -> None:
        """Initialize the component.

        This method should be implemented by subclasses to perform their
        specific initialization logic.

        Raises:
            ComponentError: If initialization fails
        """
        pass

    @abstractmethod
    async def _cleanup(self) -> None:
        """Clean up the component.

        This method should be implemented by subclasses to perform their
        specific cleanup logic.

        Raises:
            ComponentError: If cleanup fails
        """
        pass
