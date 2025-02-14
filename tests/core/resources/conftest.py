"""Shared fixtures for resource tests."""

from typing import Any, AsyncGenerator, Dict

import pytest

from pepperpy.core.resources import (
    Resource,
    ResourceConfig,
    ResourceManager,
    ResourceType,
)


class TestResource(Resource):
    """Test resource implementation."""

    async def _initialize(self) -> None:
        """Initialize the test resource."""
        self._metadata["initialized"] = True

    async def _cleanup(self) -> None:
        """Clean up the test resource."""
        self._metadata["cleaned_up"] = True


@pytest.fixture
async def test_config() -> ResourceConfig:
    """Create a test resource configuration."""
    return ResourceConfig(
        type=ResourceType.STORAGE,
        settings={"path": "/tmp/test"},
        metadata={"env": "test"},
    )


@pytest.fixture
async def test_resource(test_config: ResourceConfig) -> TestResource:
    """Create a test resource."""
    return TestResource("test-resource", test_config)


@pytest.fixture
async def resource_manager() -> AsyncGenerator[ResourceManager, None]:
    """Create a resource manager."""
    manager = ResourceManager()
    await manager.initialize()
    yield manager
    await manager.cleanup()


@pytest.fixture
async def test_metadata() -> Dict[str, Any]:
    """Create test metadata."""
    return {
        "created_at": 1234567890,
        "owner": "test-user",
        "tags": ["test", "fixture"],
        "version": "1.0.0",
    }
