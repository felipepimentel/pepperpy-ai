"""Lifecycle tests module."""

import asyncio
from typing import cast
from unittest.mock import MagicMock, patch

import pytest

from pepperpy.lifecycle.base import BaseLifecycle
from pepperpy.lifecycle.errors import (
    FinalizeError,
    HookError,
    InitializationError,
    RetryError,
    StartError,
    StopError,
    TimeoutError,
)
from pepperpy.lifecycle.hooks import LoggingHook, MetricsHook
from pepperpy.lifecycle.manager import LifecycleManager
from pepperpy.lifecycle.types import (
    LifecycleConfig,
    LifecycleContext,
    LifecycleEvent,
    LifecycleHook,
    LifecycleState,
)


class TestComponent(BaseLifecycle):
    """Test component implementation."""

    def __init__(
        self,
        component_id: str,
        config: LifecycleConfig | None = None,
        fail_init: bool = False,
        fail_start: bool = False,
        fail_stop: bool = False,
        fail_finalize: bool = False,
    ) -> None:
        """Initialize test component.

        Args:
            component_id: Component ID
            config: Optional lifecycle configuration
            fail_init: Whether to fail initialization
            fail_start: Whether to fail start
            fail_stop: Whether to fail stop
            fail_finalize: Whether to fail finalization
        """
        super().__init__(component_id, config)
        self.fail_init = fail_init
        self.fail_start = fail_start
        self.fail_stop = fail_stop
        self.fail_finalize = fail_finalize

    async def _initialize(self) -> None:
        """Initialize component implementation."""
        if self.fail_init:
            raise InitializationError(
                message="Test initialization failure",
                component_id=self._component_id,
                state=self._state,
            )

    async def _start(self) -> None:
        """Start component implementation."""
        if self.fail_start:
            raise StartError(
                message="Test start failure",
                component_id=self._component_id,
                state=self._state,
            )

    async def _stop(self) -> None:
        """Stop component implementation."""
        if self.fail_stop:
            raise StopError(
                message="Test stop failure",
                component_id=self._component_id,
                state=self._state,
            )

    async def _finalize(self) -> None:
        """Finalize component implementation."""
        if self.fail_finalize:
            raise FinalizeError(
                message="Test finalization failure",
                component_id=self._component_id,
                state=self._state,
            )


class TestHook(LifecycleHook):
    """Test hook implementation."""

    def __init__(self, fail_event: LifecycleEvent | None = None) -> None:
        """Initialize test hook.

        Args:
            fail_event: Event to fail on
        """
        self._fail_event = fail_event
        self._events: list[LifecycleEvent] = []

    @property
    def events(self) -> list[LifecycleEvent]:
        """Get recorded events."""
        return self._events

    def _handle_event(
        self,
        event: LifecycleEvent,
        context: LifecycleContext,
        error: Exception | None = None,
    ) -> None:
        """Handle lifecycle event.

        Args:
            event: Lifecycle event
            context: Lifecycle context
            error: Optional error that occurred

        Raises:
            HookError: If event matches fail event
        """
        self._events.append(event)
        if event == self._fail_event:
            raise HookError(
                message=f"Test hook failure: {event}",
                component_id=context.component_id,
                state=context.state,
                hook_name=self.__class__.__name__,
            )

    async def pre_init(self, context: LifecycleContext) -> None:
        """Handle pre-init event.

        Args:
            context: Lifecycle context
        """
        self._handle_event(LifecycleEvent.PRE_INIT, context)

    async def post_init(self, context: LifecycleContext) -> None:
        """Handle post-init event.

        Args:
            context: Lifecycle context
        """
        self._handle_event(LifecycleEvent.POST_INIT, context)

    async def pre_start(self, context: LifecycleContext) -> None:
        """Handle pre-start event.

        Args:
            context: Lifecycle context
        """
        self._handle_event(LifecycleEvent.PRE_START, context)

    async def post_start(self, context: LifecycleContext) -> None:
        """Handle post-start event.

        Args:
            context: Lifecycle context
        """
        self._handle_event(LifecycleEvent.POST_START, context)

    async def pre_stop(self, context: LifecycleContext) -> None:
        """Handle pre-stop event.

        Args:
            context: Lifecycle context
        """
        self._handle_event(LifecycleEvent.PRE_STOP, context)

    async def post_stop(self, context: LifecycleContext) -> None:
        """Handle post-stop event.

        Args:
            context: Lifecycle context
        """
        self._handle_event(LifecycleEvent.POST_STOP, context)

    async def pre_finalize(self, context: LifecycleContext) -> None:
        """Handle pre-finalize event.

        Args:
            context: Lifecycle context
        """
        self._handle_event(LifecycleEvent.PRE_FINALIZE, context)

    async def post_finalize(self, context: LifecycleContext) -> None:
        """Handle post-finalize event.

        Args:
            context: Lifecycle context
        """
        self._handle_event(LifecycleEvent.POST_FINALIZE, context)

    async def on_error(self, context: LifecycleContext, error: Exception) -> None:
        """Handle error event.

        Args:
            context: Lifecycle context
            error: Error that occurred
        """
        self._handle_event(LifecycleEvent.ERROR, context, error)


@pytest.fixture
def component() -> TestComponent:
    """Create test component.

    Returns:
        Test component instance
    """
    return TestComponent("test")


@pytest.fixture
def hook() -> TestHook:
    """Create test hook.

    Returns:
        Test hook instance
    """
    return TestHook()


@pytest.fixture
def manager() -> LifecycleManager:
    """Create lifecycle manager.

    Returns:
        Lifecycle manager instance
    """
    return LifecycleManager()


@pytest.mark.asyncio
async def test_component_lifecycle(component: TestComponent, hook: TestHook) -> None:
    """Test component lifecycle.

    Args:
        component: Test component
        hook: Test hook
    """
    # Add hook
    component.add_hook(hook)

    # Initialize
    await component.initialize()
    assert component.get_state() == LifecycleState.INITIALIZED
    assert LifecycleEvent.PRE_INIT in hook.events
    assert LifecycleEvent.POST_INIT in hook.events

    # Start
    await component.start()
    assert component.get_state() == LifecycleState.RUNNING
    assert LifecycleEvent.PRE_START in hook.events
    assert LifecycleEvent.POST_START in hook.events

    # Stop
    await component.stop()
    assert component.get_state() == LifecycleState.STOPPED
    assert LifecycleEvent.PRE_STOP in hook.events
    assert LifecycleEvent.POST_STOP in hook.events

    # Finalize
    await component.finalize()
    assert component.get_state() == LifecycleState.FINALIZED
    assert LifecycleEvent.PRE_FINALIZE in hook.events
    assert LifecycleEvent.POST_FINALIZE in hook.events


@pytest.mark.asyncio
async def test_component_lifecycle_failure(
    component: TestComponent,
    hook: TestHook,
) -> None:
    """Test component lifecycle failure.

    Args:
        component: Test component
        hook: Test hook
    """
    # Add hook
    component.add_hook(hook)

    # Initialize with failure
    component.fail_init = True
    with pytest.raises(InitializationError):
        await component.initialize()
    assert component.get_state() == LifecycleState.ERROR
    assert LifecycleEvent.ERROR in hook.events

    # Start with failure
    component.fail_start = True
    with pytest.raises(StartError):
        await component.start()
    assert component.get_state() == LifecycleState.ERROR
    assert LifecycleEvent.ERROR in hook.events

    # Stop with failure
    component.fail_stop = True
    with pytest.raises(StopError):
        await component.stop()
    assert component.get_state() == LifecycleState.ERROR
    assert LifecycleEvent.ERROR in hook.events

    # Finalize with failure
    component.fail_finalize = True
    with pytest.raises(FinalizeError):
        await component.finalize()
    assert component.get_state() == LifecycleState.ERROR
    assert LifecycleEvent.ERROR in hook.events


@pytest.mark.asyncio
async def test_component_hook_failure(component: TestComponent) -> None:
    """Test component hook failure.

    Args:
        component: Test component
    """
    # Add hook that fails on pre-init
    hook = TestHook(fail_event=LifecycleEvent.PRE_INIT)
    component.add_hook(hook)

    # Initialize with hook failure
    with pytest.raises(HookError):
        await component.initialize()
    assert component.get_state() == LifecycleState.ERROR
    assert LifecycleEvent.ERROR in hook.events


@pytest.mark.asyncio
async def test_component_retry_operation(component: TestComponent) -> None:
    """Test component retry operation.

    Args:
        component: Test component
    """
    # Configure retry
    component._config.max_retries = 3
    component._config.retry_delay = 0.1

    # Create mock function that fails twice
    mock_func = MagicMock()
    mock_func.side_effect = [
        Exception("First failure"),
        Exception("Second failure"),
        None,
    ]

    # Retry operation
    await component._retry_operation("test", mock_func)
    assert mock_func.call_count == 3


@pytest.mark.asyncio
async def test_component_retry_operation_failure(component: TestComponent) -> None:
    """Test component retry operation failure.

    Args:
        component: Test component
    """
    # Configure retry
    component._config.max_retries = 3
    component._config.retry_delay = 0.1

    # Create mock function that always fails
    mock_func = MagicMock()
    mock_func.side_effect = Exception("Test failure")

    # Retry operation with failure
    with pytest.raises(RetryError):
        await component._retry_operation("test", mock_func)
    assert mock_func.call_count == 3


@pytest.mark.asyncio
async def test_component_retry_operation_timeout(component: TestComponent) -> None:
    """Test component retry operation timeout.

    Args:
        component: Test component
    """
    # Configure retry
    component._config.timeout = 0.1

    # Create mock function that sleeps
    async def mock_func() -> None:
        await asyncio.sleep(1.0)

    # Retry operation with timeout
    with pytest.raises(TimeoutError):
        await component._retry_operation("test", mock_func)


@pytest.mark.asyncio
async def test_manager_lifecycle(manager: LifecycleManager) -> None:
    """Test manager lifecycle.

    Args:
        manager: Lifecycle manager
    """
    # Register components
    component1 = await manager.register_component("test1", TestComponent)
    component2 = await manager.register_component("test2", TestComponent)

    # Initialize all
    await manager.initialize_all()
    assert component1.get_state() == LifecycleState.INITIALIZED
    assert component2.get_state() == LifecycleState.INITIALIZED

    # Start all
    await manager.start_all()
    assert component1.get_state() == LifecycleState.RUNNING
    assert component2.get_state() == LifecycleState.RUNNING

    # Stop all
    await manager.stop_all()
    assert component1.get_state() == LifecycleState.STOPPED
    assert component2.get_state() == LifecycleState.STOPPED

    # Finalize all
    await manager.finalize_all()
    assert component1.get_state() == LifecycleState.FINALIZED
    assert component2.get_state() == LifecycleState.FINALIZED


@pytest.mark.asyncio
async def test_manager_component_failure(manager: LifecycleManager) -> None:
    """Test manager component failure.

    Args:
        manager: Lifecycle manager
    """
    # Register components
    component1 = cast(
        TestComponent,
        await manager.register_component(
            "test1",
            TestComponent,
            config=LifecycleConfig(auto_start=True),
        ),
    )
    component2 = cast(
        TestComponent,
        await manager.register_component(
            "test2",
            TestComponent,
            config=LifecycleConfig(auto_start=True),
        ),
    )

    # Initialize all with component1 failure
    component1.fail_init = True
    await manager.initialize_all()
    assert component1.get_state() == LifecycleState.ERROR
    assert component2.get_state() == LifecycleState.INITIALIZED

    # Start all with component2 failure
    component2.fail_start = True
    await manager.start_all()
    assert component1.get_state() == LifecycleState.ERROR
    assert component2.get_state() == LifecycleState.ERROR


@pytest.mark.asyncio
async def test_logging_hook() -> None:
    """Test logging hook."""
    # Create component and hook
    component = TestComponent("test")
    hook = LoggingHook()
    component.add_hook(hook)

    # Initialize with mock logger
    with patch("logging.Logger.log") as mock_log:
        await component.initialize()
        assert mock_log.call_count == 2  # pre_init and post_init


@pytest.mark.asyncio
async def test_metrics_hook() -> None:
    """Test metrics hook."""
    # Create component and hook
    component = TestComponent("test")
    hook = MetricsHook()
    component.add_hook(hook)

    # Initialize and check metrics
    await component.initialize()
    metrics = hook.get_metrics("test")
    assert metrics is not None
    assert metrics["state"] == LifecycleState.INITIALIZED
    assert metrics["transitions"] == 2  # UNINITIALIZED -> INITIALIZING -> INITIALIZED
