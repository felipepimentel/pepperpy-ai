"""Base lifecycle component implementation.

This module provides the base implementation of the lifecycle protocol,
including state management, event handling, and hook execution.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from pepperpy.core.common.lifecycle.errors import (
    FinalizeError,
    HookError,
    InitializationError,
    RetryError,
    StartError,
    StateError,
    StopError,
)
from pepperpy.core.common.lifecycle.types import (  # TODO: Verificar se este é o import correto
    ALLOWED_TRANSITIONS,
    LifecycleConfig,
    LifecycleContext,
    LifecycleEvent,
    LifecycleHook,
    LifecycleMetrics,
    LifecycleState,
    LifecycleTransition,
    from,
    import,
    typing,
)


class LifecycleComponent(ABC):
    """Base class for components with lifecycle management.

    This class provides the core implementation of the Lifecycle protocol,
    including state management, event handling, and hook execution.

    Attributes:
        state (LifecycleState): Current state of the component
        config (LifecycleConfig): Configuration for the component
        context (LifecycleContext): Runtime context for the component
        hooks (list[LifecycleHook]): Registered lifecycle hooks
        metrics (LifecycleMetrics): Collected metrics about lifecycle events
    """

    def __init__(
        self,
        config: LifecycleConfig | None = None,
        context: LifecycleContext | None = None,
    ) -> None:
        """Initialize the lifecycle component.

        Args:
            config: Optional configuration for the component
            context: Optional runtime context for the component
        """
        self.state = LifecycleState.UNINITIALIZED
        self.config = config or LifecycleConfig()
        self.context = context or LifecycleContext(
            component_id=self.__class__.__name__,
            state=self.state,
            event=LifecycleEvent.INITIALIZE,
        )
        self.hooks: list[LifecycleHook] = []
        self.metrics = LifecycleMetrics()

    def add_hook(self, hook: LifecycleHook) -> None:
        """Add a lifecycle hook.

        Args:
            hook: Hook to add
        """
        self.hooks.append(hook)

    def remove_hook(self, hook: LifecycleHook) -> None:
        """Remove a lifecycle hook.

        Args:
            hook: Hook to remove
        """
        if hook in self.hooks:
            self.hooks.remove(hook)

    async def _execute_hooks(self, event: LifecycleEvent) -> None:
        """Execute all registered hooks for an event.

        Args:
            event: Event to execute hooks for

        Raises:
            HookError: If a hook fails to execute
        """
        self.context.event = event
        self.context.timestamp = datetime.utcnow()

        for hook in self.hooks:
            try:
                await hook.pre_event(self.context)
            except Exception as e:
                self.context.error = e
                await hook.on_error(self.context)
                raise HookError(f"Hook {hook} failed: {e}") from e

            try:
                await hook.post_event(self.context)
            except Exception as e:
                self.context.error = e
                await hook.on_error(self.context)
                raise HookError(f"Hook {hook} failed: {e}") from e

    async def _transition(self, target: LifecycleState, event: LifecycleEvent) -> None:
        """Transition to a new state.

        Args:
            target: Target state to transition to
            event: Event triggering the transition

        Raises:
            StateError: If transition is invalid
        """
        # Validate transition
        if target not in ALLOWED_TRANSITIONS.get(self.state, set()):
            raise StateError(
                f"Invalid transition from {self.state} to {target} during {event} event"
            )

        # Log transition
        self.context.state = target
        self.context.event = event
        self.context.timestamp = datetime.utcnow()

        # Execute hooks
        await self._execute_hooks(event)

        # Update state and record transition
        self.state = target
        self.metrics.transitions.append(
            LifecycleTransition(
                from_state=self.state,
                to_state=target,
                event=event,
                timestamp=self.context.timestamp,
                metadata=self.context.metadata,
            )
        )

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the component.

        This method should be implemented by subclasses to perform
        any necessary initialization.

        Raises:
            InitializationError: If initialization fails
        """
        try:
            await self._transition(
                LifecycleState.INITIALIZING, LifecycleEvent.INITIALIZE
            )
            # Subclass initialization here
            await self._transition(LifecycleState.READY, LifecycleEvent.INITIALIZE)
        except Exception as e:
            self.state = LifecycleState.ERROR
            self.context.error = e
            raise InitializationError(f"Failed to initialize: {e}") from e

    @abstractmethod
    async def start(self) -> None:
        """Start the component.

        This method should be implemented by subclasses to start
        the component's main functionality.

        Raises:
            StartError: If starting fails
        """
        try:
            await self._transition(LifecycleState.RUNNING, LifecycleEvent.START)
            # Subclass start here
        except Exception as e:
            self.state = LifecycleState.ERROR
            self.context.error = e
            raise StartError(f"Failed to start: {e}") from e

    @abstractmethod
    async def stop(self) -> None:
        """Stop the component.

        This method should be implemented by subclasses to stop
        the component's functionality.

        Raises:
            StopError: If stopping fails
        """
        try:
            await self._transition(LifecycleState.STOPPING, LifecycleEvent.STOP)
            # Subclass stop here
            await self._transition(LifecycleState.STOPPED, LifecycleEvent.STOP)
        except Exception as e:
            self.state = LifecycleState.ERROR
            self.context.error = e
            raise StopError(f"Failed to stop: {e}") from e

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up component resources.

        This method should be implemented by subclasses to perform
        any necessary cleanup.

        Raises:
            FinalizeError: If cleanup fails
        """
        try:
            await self._transition(LifecycleState.FINALIZING, LifecycleEvent.FINALIZE)
            # Subclass cleanup here
            await self._transition(LifecycleState.FINALIZED, LifecycleEvent.FINALIZE)
        except Exception as e:
            self.state = LifecycleState.ERROR
            self.context.error = e
            raise FinalizeError(f"Failed to finalize: {e}") from e

    async def retry(self, operation: str, **kwargs: Any) -> None:
        """Retry a failed operation.

        Args:
            operation: Name of operation to retry
            **kwargs: Additional arguments for the operation

        Raises:
            RetryError: If retry fails
        """
        try:
            await self._execute_hooks(LifecycleEvent.RETRY)
            if operation == "initialize":
                await self.initialize()
            elif operation == "start":
                await self.start()
            elif operation == "stop":
                await self.stop()
            elif operation == "cleanup":
                await self.cleanup()
            else:
                raise ValueError(f"Unknown operation: {operation}")
        except Exception as e:
            self.state = LifecycleState.ERROR
            self.context.error = e
            raise RetryError(f"Failed to retry {operation}: {e}") from e
