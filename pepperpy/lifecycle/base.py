"""Lifecycle base module.

This module provides base implementations for the lifecycle system.
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Optional, Set

from pepperpy.lifecycle.errors import (
    FinalizeError,
    HookError,
    InitializationError,
    RetryError,
    StartError,
    StateError,
    StopError,
    TimeoutError,
)
from pepperpy.lifecycle.types import (
    LifecycleConfig,
    LifecycleContext,
    LifecycleEvent,
    LifecycleHook,
    LifecycleMetrics,
    LifecycleState,
    LifecycleTransition,
)

logger = logging.getLogger(__name__)


class BaseLifecycle:
    """Base lifecycle implementation."""

    def __init__(
        self,
        component_id: str,
        config: Optional[LifecycleConfig] = None,
    ) -> None:
        """Initialize base lifecycle.

        Args:
            component_id: Component ID
            config: Optional lifecycle configuration
        """
        self._component_id = component_id
        self._config = config or LifecycleConfig()
        self._state = LifecycleState.UNINITIALIZED
        self._hooks: Set[LifecycleHook] = set()
        self._history: List[LifecycleTransition] = []
        self._metrics = LifecycleMetrics(state=self._state)
        self._start_time: Optional[datetime] = None
        self._lock = asyncio.Lock()

    @property
    def component_id(self) -> str:
        """Get component ID."""
        return self._component_id

    @property
    def config(self) -> LifecycleConfig:
        """Get lifecycle configuration."""
        return self._config

    def get_state(self) -> LifecycleState:
        """Get current state.

        Returns:
            Current lifecycle state
        """
        return self._state

    def get_context(self) -> LifecycleContext:
        """Get lifecycle context.

        Returns:
            Current lifecycle context
        """
        return LifecycleContext(
            component_id=self._component_id,
            state=self._state,
            metrics=self._metrics,
            history=self._history,
        )

    def add_hook(self, hook: LifecycleHook) -> None:
        """Add lifecycle hook.

        Args:
            hook: Hook to add
        """
        self._hooks.add(hook)

    def remove_hook(self, hook: LifecycleHook) -> None:
        """Remove lifecycle hook.

        Args:
            hook: Hook to remove
        """
        self._hooks.discard(hook)

    async def _execute_hooks(
        self,
        event: LifecycleEvent,
        context: Optional[LifecycleContext] = None,
        error: Optional[Exception] = None,
    ) -> None:
        """Execute lifecycle hooks.

        Args:
            event: Lifecycle event
            context: Optional lifecycle context
            error: Optional error that occurred

        Raises:
            HookError: If hook execution fails
        """
        ctx = context or self.get_context()

        for hook in self._hooks:
            try:
                if event == LifecycleEvent.PRE_INIT:
                    await hook.pre_init(ctx)
                elif event == LifecycleEvent.POST_INIT:
                    await hook.post_init(ctx)
                elif event == LifecycleEvent.PRE_START:
                    await hook.pre_start(ctx)
                elif event == LifecycleEvent.POST_START:
                    await hook.post_start(ctx)
                elif event == LifecycleEvent.PRE_STOP:
                    await hook.pre_stop(ctx)
                elif event == LifecycleEvent.POST_STOP:
                    await hook.post_stop(ctx)
                elif event == LifecycleEvent.PRE_FINALIZE:
                    await hook.pre_finalize(ctx)
                elif event == LifecycleEvent.POST_FINALIZE:
                    await hook.post_finalize(ctx)
                elif event == LifecycleEvent.ERROR and error:
                    await hook.on_error(ctx, error)
            except Exception as e:
                logger.error(
                    f"Hook execution failed: {e}",
                    extra={
                        "component_id": self._component_id,
                        "event": event,
                        "hook": hook.__class__.__name__,
                    },
                    exc_info=True,
                )
                raise HookError(
                    message=f"Hook execution failed: {e}",
                    component_id=self._component_id,
                    state=self._state,
                    hook_name=hook.__class__.__name__,
                )

    def _record_transition(
        self,
        from_state: LifecycleState,
        to_state: LifecycleState,
        event: LifecycleEvent,
    ) -> None:
        """Record state transition.

        Args:
            from_state: Previous state
            to_state: New state
            event: Lifecycle event
        """
        transition = LifecycleTransition(
            from_state=from_state,
            to_state=to_state,
            event=event,
        )
        self._history.append(transition)
        self._metrics.transitions += 1
        self._metrics.last_transition = transition.timestamp

        logger.info(
            f"State transition: {from_state} -> {to_state}",
            extra={
                "component_id": self._component_id,
                "from_state": from_state,
                "to_state": to_state,
                "event": event,
            },
        )

    def _update_metrics(self) -> None:
        """Update lifecycle metrics."""
        self._metrics.state = self._state
        if self._start_time and self._state == LifecycleState.RUNNING:
            self._metrics.uptime = (
                datetime.utcnow() - self._start_time
            ).total_seconds()

    async def _transition_state(
        self,
        to_state: LifecycleState,
        event: LifecycleEvent,
    ) -> None:
        """Transition to new state.

        Args:
            to_state: New state
            event: Lifecycle event

        Raises:
            StateError: If state transition is invalid
        """
        async with self._lock:
            from_state = self._state

            # Validate transition
            if not self._is_valid_transition(from_state, to_state):
                raise StateError(
                    message=f"Invalid state transition: {from_state} -> {to_state}",
                    component_id=self._component_id,
                    state=from_state,
                )

            # Update state
            self._state = to_state
            self._record_transition(from_state, to_state, event)
            self._update_metrics()

    def _is_valid_transition(
        self,
        from_state: LifecycleState,
        to_state: LifecycleState,
    ) -> bool:
        """Check if state transition is valid.

        Args:
            from_state: Current state
            to_state: Target state

        Returns:
            True if transition is valid
        """
        valid_transitions = {
            LifecycleState.UNINITIALIZED: {
                LifecycleState.INITIALIZING,
                LifecycleState.ERROR,
            },
            LifecycleState.INITIALIZING: {
                LifecycleState.INITIALIZED,
                LifecycleState.ERROR,
            },
            LifecycleState.INITIALIZED: {
                LifecycleState.STARTING,
                LifecycleState.FINALIZING,
                LifecycleState.ERROR,
            },
            LifecycleState.STARTING: {
                LifecycleState.RUNNING,
                LifecycleState.ERROR,
            },
            LifecycleState.RUNNING: {
                LifecycleState.STOPPING,
                LifecycleState.ERROR,
            },
            LifecycleState.STOPPING: {
                LifecycleState.STOPPED,
                LifecycleState.ERROR,
            },
            LifecycleState.STOPPED: {
                LifecycleState.STARTING,
                LifecycleState.FINALIZING,
                LifecycleState.ERROR,
            },
            LifecycleState.FINALIZING: {
                LifecycleState.FINALIZED,
                LifecycleState.ERROR,
            },
            LifecycleState.ERROR: {
                LifecycleState.INITIALIZING,
                LifecycleState.STARTING,
                LifecycleState.STOPPING,
                LifecycleState.FINALIZING,
            },
        }

        return to_state in valid_transitions.get(from_state, set())

    async def _retry_operation(
        self,
        operation: str,
        func: callable,
        *args,
        **kwargs,
    ) -> None:
        """Retry operation with backoff.

        Args:
            operation: Operation name
            func: Function to retry
            *args: Function arguments
            **kwargs: Function keyword arguments

        Raises:
            RetryError: If maximum retries exceeded
            TimeoutError: If operation times out
        """
        retries = 0
        while retries < self._config.max_retries:
            try:
                await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=self._config.timeout,
                )
                return
            except asyncio.TimeoutError:
                logger.warning(
                    f"Operation timed out: {operation}",
                    extra={
                        "component_id": self._component_id,
                        "operation": operation,
                        "timeout": self._config.timeout,
                        "retry": retries + 1,
                    },
                )
                raise TimeoutError(
                    message=f"Operation timed out: {operation}",
                    component_id=self._component_id,
                    state=self._state,
                    operation=operation,
                    timeout=self._config.timeout,
                )
            except Exception as e:
                logger.warning(
                    f"Operation failed: {operation} - {e}",
                    extra={
                        "component_id": self._component_id,
                        "operation": operation,
                        "retry": retries + 1,
                    },
                    exc_info=True,
                )
                retries += 1
                if retries < self._config.max_retries:
                    await asyncio.sleep(self._config.retry_delay)
                else:
                    raise RetryError(
                        message=f"Maximum retries exceeded for operation: {operation}",
                        component_id=self._component_id,
                        state=self._state,
                        operation=operation,
                        max_retries=self._config.max_retries,
                    )

    async def initialize(self) -> None:
        """Initialize component.

        Raises:
            InitializationError: If initialization fails
            StateError: If state transition is invalid
            HookError: If hook execution fails
        """
        try:
            # Execute pre-init hooks
            await self._execute_hooks(LifecycleEvent.PRE_INIT)

            # Transition to initializing state
            await self._transition_state(
                LifecycleState.INITIALIZING,
                LifecycleEvent.PRE_INIT,
            )

            # Initialize component
            await self._initialize()

            # Transition to initialized state
            await self._transition_state(
                LifecycleState.INITIALIZED,
                LifecycleEvent.POST_INIT,
            )

            # Execute post-init hooks
            await self._execute_hooks(LifecycleEvent.POST_INIT)

            # Auto-start if configured
            if self._config.auto_start:
                await self.start()

        except Exception as e:
            logger.error(
                f"Initialization failed: {e}",
                extra={"component_id": self._component_id},
                exc_info=True,
            )
            await self._handle_error(e)
            raise InitializationError(
                message=f"Initialization failed: {e}",
                component_id=self._component_id,
                state=self._state,
            )

    async def start(self) -> None:
        """Start component.

        Raises:
            StartError: If start fails
            StateError: If state transition is invalid
            HookError: If hook execution fails
        """
        try:
            # Execute pre-start hooks
            await self._execute_hooks(LifecycleEvent.PRE_START)

            # Transition to starting state
            await self._transition_state(
                LifecycleState.STARTING,
                LifecycleEvent.PRE_START,
            )

            # Start component
            await self._start()

            # Record start time
            self._start_time = datetime.utcnow()

            # Transition to running state
            await self._transition_state(
                LifecycleState.RUNNING,
                LifecycleEvent.POST_START,
            )

            # Execute post-start hooks
            await self._execute_hooks(LifecycleEvent.POST_START)

        except Exception as e:
            logger.error(
                f"Start failed: {e}",
                extra={"component_id": self._component_id},
                exc_info=True,
            )
            await self._handle_error(e)
            raise StartError(
                message=f"Start failed: {e}",
                component_id=self._component_id,
                state=self._state,
            )

    async def stop(self) -> None:
        """Stop component.

        Raises:
            StopError: If stop fails
            StateError: If state transition is invalid
            HookError: If hook execution fails
        """
        try:
            # Execute pre-stop hooks
            await self._execute_hooks(LifecycleEvent.PRE_STOP)

            # Transition to stopping state
            await self._transition_state(
                LifecycleState.STOPPING,
                LifecycleEvent.PRE_STOP,
            )

            # Stop component
            await self._stop()

            # Clear start time
            self._start_time = None

            # Transition to stopped state
            await self._transition_state(
                LifecycleState.STOPPED,
                LifecycleEvent.POST_STOP,
            )

            # Execute post-stop hooks
            await self._execute_hooks(LifecycleEvent.POST_STOP)

            # Auto-finalize if configured
            if self._config.auto_finalize:
                await self.finalize()

        except Exception as e:
            logger.error(
                f"Stop failed: {e}",
                extra={"component_id": self._component_id},
                exc_info=True,
            )
            await self._handle_error(e)
            raise StopError(
                message=f"Stop failed: {e}",
                component_id=self._component_id,
                state=self._state,
            )

    async def finalize(self) -> None:
        """Finalize component.

        Raises:
            FinalizeError: If finalization fails
            StateError: If state transition is invalid
            HookError: If hook execution fails
        """
        try:
            # Execute pre-finalize hooks
            await self._execute_hooks(LifecycleEvent.PRE_FINALIZE)

            # Transition to finalizing state
            await self._transition_state(
                LifecycleState.FINALIZING,
                LifecycleEvent.PRE_FINALIZE,
            )

            # Finalize component
            await self._finalize()

            # Transition to finalized state
            await self._transition_state(
                LifecycleState.FINALIZED,
                LifecycleEvent.POST_FINALIZE,
            )

            # Execute post-finalize hooks
            await self._execute_hooks(LifecycleEvent.POST_FINALIZE)

        except Exception as e:
            logger.error(
                f"Finalization failed: {e}",
                extra={"component_id": self._component_id},
                exc_info=True,
            )
            await self._handle_error(e)
            raise FinalizeError(
                message=f"Finalization failed: {e}",
                component_id=self._component_id,
                state=self._state,
            )

    async def _handle_error(self, error: Exception) -> None:
        """Handle lifecycle error.

        Args:
            error: Error that occurred
        """
        # Update metrics
        self._metrics.errors += 1
        self._metrics.last_error = str(error)

        # Transition to error state
        await self._transition_state(
            LifecycleState.ERROR,
            LifecycleEvent.ERROR,
        )

        # Execute error hooks
        await self._execute_hooks(
            LifecycleEvent.ERROR,
            error=error,
        )

    async def _initialize(self) -> None:
        """Initialize component implementation."""
        pass

    async def _start(self) -> None:
        """Start component implementation."""
        pass

    async def _stop(self) -> None:
        """Stop component implementation."""
        pass

    async def _finalize(self) -> None:
        """Finalize component implementation."""
        pass
