"""Test fixtures for lifecycle management tests."""

from typing import AsyncGenerator

import pytest

from pepperpy.core.lifecycle import Lifecycle, LifecycleManager


class MockComponent(Lifecycle):
    """Mock component for testing."""

    def __init__(self) -> None:
        super().__init__()
        self.initialize_called = False
        self.cleanup_called = False
        self.start_called = False
        self.stop_called = False

    async def initialize(self) -> None:
        self.initialize_called = True

    async def cleanup(self) -> None:
        self.cleanup_called = True

    async def start(self) -> None:
        self.start_called = True

    async def stop(self) -> None:
        self.stop_called = True


@pytest.fixture
async def lifecycle_manager() -> AsyncGenerator[LifecycleManager, None]:
    """Fixture providing a lifecycle manager instance."""
    manager = LifecycleManager()
    yield manager
    await manager.shutdown()


@pytest.fixture
def mock_component() -> MockComponent:
    """Fixture providing a mock component instance."""
    return MockComponent()
