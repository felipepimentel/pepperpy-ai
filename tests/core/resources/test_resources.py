"""Tests for resource management."""

from typing import AsyncGenerator, Dict, Any

import pytest

from pepperpy.core.resources import (
    Resource,
    ResourceConfig,
    ResourceManager,
    ResourceState,
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


@pytest.mark.asyncio
async def test_resource_lifecycle(test_resource: Resource):
    """Test resource lifecycle management."""
    # Test initial state
    assert test_resource.state == ResourceState.CREATED
    assert test_resource.error is None
    assert test_resource.metadata == {}

    # Test initialization
    await test_resource.initialize()
    assert test_resource.state == ResourceState.READY
    assert test_resource.metadata["initialized"] is True

    # Test cleanup
    await test_resource.cleanup()
    assert test_resource.state == ResourceState.TERMINATED
    assert test_resource.metadata["cleaned_up"] is True


@pytest.mark.asyncio
async def test_resource_error_handling(test_resource: Resource):
    """Test resource error handling."""
    error_message = "Test error"
    error_type = "TestError"
    error_details = {"detail": "test"}

    test_resource.set_error(error_message, error_type, error_details)
    assert test_resource.state == ResourceState.ERROR
    assert test_resource.error is not None
    assert test_resource.error.message == error_message
    assert test_resource.error.error_type == error_type
    assert test_resource.error.details == error_details

    test_resource.clear_error()
    assert test_resource.error is None


@pytest.mark.asyncio
async def test_resource_manager_registration(
    resource_manager: ResourceManager, test_config: ResourceConfig
):
    """Test resource registration and management."""
    # Test resource registration
    resource = await resource_manager.register("test", test_config)
    assert resource.state == ResourceState.READY
    assert resource.metadata["initialized"] is True

    # Test resource retrieval
    retrieved = await resource_manager.get("test")
    assert retrieved is not None
    assert retrieved.name == "test"
    assert retrieved.config == test_config

    # Test resource listing
    resources = await resource_manager.list()
    assert len(resources) == 1
    assert resources[0].name == "test"

    # Test resource unregistration
    await resource_manager.unregister("test")
    assert await resource_manager.get("test") is None


@pytest.mark.asyncio
async def test_resource_manager_error_handling(
    resource_manager: ResourceManager, test_config: ResourceConfig
):
    """Test resource manager error handling."""
    # Test duplicate registration
    await resource_manager.register("test", test_config)
    with pytest.raises(ValueError):
        await resource_manager.register("test", test_config)

    # Test unregistering non-existent resource
    with pytest.raises(ValueError):
        await resource_manager.unregister("non-existent")


@pytest.mark.asyncio
async def test_resource_manager_filtering(
    resource_manager: ResourceManager, test_config: ResourceConfig
):
    """Test resource filtering methods."""
    # Register multiple resources
    await resource_manager.register("test1", test_config)
    await resource_manager.register(
        "test2",
        ResourceConfig(
            type=ResourceType.COMPUTE,
            settings={"cpu": 2},
            metadata={"env": "test"},
        ),
    )

    # Test filtering by state
    ready_resources = resource_manager.get_resources_by_state(ResourceState.READY)
    assert len(ready_resources) == 2

    # Test filtering by type
    storage_resources = resource_manager.get_resources_by_type("storage")
    assert len(storage_resources) == 1
    assert storage_resources[0].name == "test1"

    compute_resources = resource_manager.get_resources_by_type("compute")
    assert len(compute_resources) == 1
    assert compute_resources[0].name == "test2"


@pytest.mark.asyncio
async def test_resource_metadata_update(
    resource_manager: ResourceManager,
    test_config: ResourceConfig,
    test_metadata: Dict[str, Any],
):
    """Test resource metadata updates."""
    # Register a resource
    await resource_manager.register("test", test_config)

    # Update metadata
    await resource_manager.update_metadata("test", test_metadata)

    # Verify metadata update
    resource = await resource_manager.get("test")
    assert resource is not None
    for key, value in test_metadata.items():
        assert resource.metadata[key] == value

    # Test updating non-existent resource
    with pytest.raises(ValueError):
        await resource_manager.update_metadata("non-existent", test_metadata)
