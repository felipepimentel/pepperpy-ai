"""Test configuration module.

This module provides shared fixtures and utilities for tests.
"""

import asyncio
import logging
from typing import Any, AsyncGenerator, Dict, Generator

import pytest

from pepperpy.core.base import ComponentBase
from pepperpy.core.metrics import Counter, Histogram
from pepperpy.tests.base import TestContext, TestUtils

# Configure logging
logger = logging.getLogger(__name__)


class TestComponent(ComponentBase):
    """Test component implementation."""

    def __init__(self) -> None:
        """Initialize component."""
        super().__init__()
        self._operations = Counter(
            "test_operations_total", "Total number of operations"
        )
        self._errors = Counter("test_errors_total", "Total number of errors")
        self._duration = Histogram(
            "test_duration_seconds", "Operation duration in seconds"
        )
        self._state: Dict[str, Any] = {}

    async def _initialize(self) -> None:
        """Initialize component."""
        await super()._initialize()
        logger.info("Initializing test component")

    async def _cleanup(self) -> None:
        """Clean up component."""
        logger.info("Cleaning up test component")
        await super()._cleanup()

    async def _execute(self) -> None:
        """Execute component operation."""
        logger.info("Executing test component operation")
        self._operations.inc()
        try:
            # Simulate work
            await asyncio.sleep(0.1)
            self._duration.observe(0.1)
        except Exception:
            self._errors.inc()
            raise

    def get_state(self) -> Dict[str, Any]:
        """Get component state.

        Returns:
            Dict[str, Any]: Component state
        """
        return self._state.copy()

    def set_state(self, state: Dict[str, Any]) -> None:
        """Set component state.

        Args:
            state: New state
        """
        self._state.update(state)


@pytest.fixture
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Fixture that provides an event loop.

    This fixture ensures that each test has its own event loop.

    Yields:
        asyncio.AbstractEventLoop: Event loop for test
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture
async def test_context(request: Any) -> AsyncGenerator[TestContext, None]:
    """Fixture that provides a test context.

    This fixture creates a test context for each test and handles cleanup.

    Args:
        request: Pytest request object

    Yields:
        TestContext: Test context
    """
    context = TestUtils.create_test_context(
        test_name=request.node.name,
        config={"test_module": request.module.__name__},
    )

    yield context

    # Clean up resources
    if context.resources:
        for resource in context.resources.values():
            if hasattr(resource, "cleanup"):
                await resource.cleanup()


@pytest.fixture
async def test_component() -> AsyncGenerator[ComponentBase, None]:
    """Fixture that provides a test component.

    This fixture creates a test component and handles initialization and cleanup.

    Yields:
        ComponentBase: Test component
    """
    component = TestComponent()
    await component._initialize()

    yield component

    await component._cleanup()


@pytest.fixture
def test_logger() -> Generator[logging.Logger, None, None]:
    """Fixture that provides a test logger.

    This fixture creates a logger for tests with appropriate handlers.

    Yields:
        logging.Logger: Test logger
    """
    # Create logger
    logger = logging.getLogger("test")
    logger.setLevel(logging.DEBUG)

    # Create console handler
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(handler)

    yield logger

    # Clean up
    logger.removeHandler(handler)
    handler.close()


@pytest.fixture
def test_metrics() -> Generator[Dict[str, Counter | Histogram], None, None]:
    """Fixture that provides test metrics.

    This fixture creates metrics for tests.

    Yields:
        Dict[str, Counter | Histogram]: Test metrics
    """
    metrics: Dict[str, Counter | Histogram] = {
        "operations": Counter("test_operations_total", "Total number of operations"),
        "errors": Counter("test_errors_total", "Total number of errors"),
        "duration": Histogram("test_duration_seconds", "Operation duration in seconds"),
    }

    yield metrics
