"""
Base classes for the lifecycle management system.
"""

from abc import ABC, abstractmethod
from typing import Any

from pepperpy.core.lifecycle.errors import (
    InvalidStateError,
    InvalidTransitionError,
    LifecycleOperationError,
)
from pepperpy.core.lifecycle.types import LifecycleState, StateTransition
from pepperpy.core.metrics.base import MetricsManager


class LifecycleHook(ABC):
    """Abstract base class for lifecycle hooks."""

    async def pre_init(self) -> None:
        """Called before initialization."""
        pass

    async def post_init(self) -> None:
        """Called after initialization."""
        pass

    async def pre_start(self) -> None:
        """Called before starting."""
        pass

    async def post_start(self) -> None:
        """Called after starting."""
        pass

    async def pre_stop(self) -> None:
        """Called before stopping."""
        pass

    async def post_stop(self) -> None:
        """Called after stopping."""
        pass

    async def pre_finalize(self) -> None:
        """Called before finalization."""
        pass

    async def post_finalize(self) -> None:
        """Called after finalization."""
        pass

    async def on_error(self, error: Exception) -> None:
        """Called when an error occurs."""
        pass


class LifecycleComponent(ABC):
    """Abstract base class for components with lifecycle management."""

    def __init__(self, name: str):
        self.name = name
        self._state = LifecycleState.UNINITIALIZED
        self._hooks: list[LifecycleHook] = []
        self._history: list[StateTransition] = []
        self._metadata: dict[str, Any] = {}
        self._metrics = MetricsManager.get_instance()

    @property
    def state(self) -> LifecycleState:
        """Get the current state."""
        return self._state

    def add_hook(self, hook: LifecycleHook) -> None:
        """Add a lifecycle hook."""
        if hook not in self._hooks:
            self._hooks.append(hook)

    def remove_hook(self, hook: LifecycleHook) -> None:
        """Remove a lifecycle hook."""
        if hook in self._hooks:
            self._hooks.remove(hook)

    def get_history(self) -> list[StateTransition]:
        """Get the state transition history."""
        return self._history.copy()

    def set_metadata(self, key: str, value: Any) -> None:
        """Set metadata for the component."""
        self._metadata[key] = value

    def get_metadata(self, key: str) -> Any | None:
        """Get metadata for the component."""
        return self._metadata.get(key)

    async def _transition_state(self, to_state: LifecycleState) -> None:
        """Transition to a new state."""
        transition = StateTransition(self._state, to_state)

        if not transition.is_valid():
            raise InvalidTransitionError(self._state, to_state)

        self._history.append(transition)
        self._state = to_state

        # Record metrics
        self._metrics.record_metric(
            "lifecycle_transition",
            1,
            {
                "component": self.name,
                "from_state": str(transition.from_state),
                "to_state": str(transition.to_state),
            },
        )

    async def _execute_hooks(self, hook_method: str, *args, **kwargs) -> None:
        """Execute all hooks of a given type."""
        for hook in self._hooks:
            try:
                await getattr(hook, hook_method)(*args, **kwargs)
            except Exception as e:
                await hook.on_error(e)
                raise LifecycleOperationError(hook_method, self.name, e)

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the component."""
        try:
            await self._execute_hooks("pre_init")
            await self._transition_state(LifecycleState.INITIALIZING)

            # Component-specific initialization
            await self._do_initialize()

            await self._transition_state(LifecycleState.INITIALIZED)
            await self._execute_hooks("post_init")

        except Exception as e:
            await self._transition_state(LifecycleState.ERROR)
            raise LifecycleOperationError("initialize", self.name, e)

    @abstractmethod
    async def start(self) -> None:
        """Start the component."""
        if self._state not in [LifecycleState.INITIALIZED, LifecycleState.STOPPED]:
            raise InvalidStateError(
                self._state, [LifecycleState.INITIALIZED, LifecycleState.STOPPED]
            )

        try:
            await self._execute_hooks("pre_start")
            await self._transition_state(LifecycleState.STARTING)

            # Component-specific start
            await self._do_start()

            await self._transition_state(LifecycleState.RUNNING)
            await self._execute_hooks("post_start")

        except Exception as e:
            await self._transition_state(LifecycleState.ERROR)
            raise LifecycleOperationError("start", self.name, e)

    @abstractmethod
    async def stop(self) -> None:
        """Stop the component."""
        if self._state != LifecycleState.RUNNING:
            raise InvalidStateError(self._state, [LifecycleState.RUNNING])

        try:
            await self._execute_hooks("pre_stop")
            await self._transition_state(LifecycleState.STOPPING)

            # Component-specific stop
            await self._do_stop()

            await self._transition_state(LifecycleState.STOPPED)
            await self._execute_hooks("post_stop")

        except Exception as e:
            await self._transition_state(LifecycleState.ERROR)
            raise LifecycleOperationError("stop", self.name, e)

    @abstractmethod
    async def finalize(self) -> None:
        """Finalize the component."""
        if self._state not in [LifecycleState.INITIALIZED, LifecycleState.STOPPED]:
            raise InvalidStateError(
                self._state, [LifecycleState.INITIALIZED, LifecycleState.STOPPED]
            )

        try:
            await self._execute_hooks("pre_finalize")
            await self._transition_state(LifecycleState.FINALIZING)

            # Component-specific finalization
            await self._do_finalize()

            await self._transition_state(LifecycleState.FINALIZED)
            await self._execute_hooks("post_finalize")

        except Exception as e:
            await self._transition_state(LifecycleState.ERROR)
            raise LifecycleOperationError("finalize", self.name, e)

    @abstractmethod
    async def _do_initialize(self) -> None:
        """Component-specific initialization logic."""
        pass

    @abstractmethod
    async def _do_start(self) -> None:
        """Component-specific start logic."""
        pass

    @abstractmethod
    async def _do_stop(self) -> None:
        """Component-specific stop logic."""
        pass

    @abstractmethod
    async def _do_finalize(self) -> None:
        """Component-specific finalization logic."""
        pass
