"""Tests for resource pooling."""

from typing import AsyncGenerator

import pytest

from pepperpy.core.resources import (
    Resource,
    ResourceConfig,
    ResourceManager,
    ResourcePool,
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
def test_config() -> ResourceConfig:
    """Create a test resource configuration."""
    return ResourceConfig(
        type=ResourceType.STORAGE,
        settings={"path": "/tmp/test"},
        metadata={"env": "test"},
    )


@pytest.fixture
async def resource_pool(
    resource_manager: ResourceManager,
) -> AsyncGenerator[ResourcePool, None]:
    """Create a resource pool."""
    pool = ResourcePool(ResourceType.STORAGE, resource_manager)
    await pool.initialize()
    yield pool
    await pool.cleanup()


@pytest.mark.asyncio
async def test_resource_pool_basic(
    resource_pool: ResourcePool, test_config: ResourceConfig
):
    """Test basic resource pool operations."""
    # Add a resource
    resource = await resource_pool.add_resource("test", test_config)
    assert resource.state == ResourceState.READY
    assert resource.metadata["initialized"] is True

    # Allocate the resource
    allocated = await resource_pool.allocate("test_owner")
    assert allocated is not None
    assert allocated.name == "test"

    # Verify allocation
    allocation = resource_pool.get_allocation("test")
    assert allocation is not None
    assert allocation.owner_id == "test_owner"

    # Release the resource
    await resource_pool.release("test")
    assert resource_pool.get_allocation("test") is None

    # Verify resource is available again
    available = await resource_pool.list_available()
    assert len(available) == 1
    assert available[0].name == "test"


@pytest.mark.asyncio
async def test_resource_pool_multiple(
    resource_pool: ResourcePool, test_config: ResourceConfig
):
    """Test managing multiple resources in a pool."""
    # Add multiple resources
    resources = []
    for i in range(3):
        resource = await resource_pool.add_resource(
            f"test{i}",
            ResourceConfig(
                type=ResourceType.STORAGE,
                settings={"path": f"/tmp/test{i}"},
                metadata={"env": "test"},
            ),
        )
        resources.append(resource)

    # Verify all resources are available
    available = await resource_pool.list_available()
    assert len(available) == 3

    # Allocate all resources
    allocated = []
    for i in range(3):
        resource = await resource_pool.allocate(f"owner{i}")
        assert resource is not None
        allocated.append(resource)

    # Verify no resources are available
    available = await resource_pool.list_available()
    assert len(available) == 0

    # Verify all resources are allocated
    allocated_list = resource_pool.list_allocated()
    assert len(allocated_list) == 3

    # Release all resources
    for resource in allocated:
        await resource_pool.release(resource.name)

    # Verify all resources are available again
    available = await resource_pool.list_available()
    assert len(available) == 3


@pytest.mark.asyncio
async def test_resource_pool_error_handling(
    resource_pool: ResourcePool, test_config: ResourceConfig
):
    """Test resource pool error handling."""
    # Test adding resource with wrong type
    wrong_config = ResourceConfig(
        type=ResourceType.COMPUTE,
        settings={"cpu": 2},
        metadata={"env": "test"},
    )
    with pytest.raises(ValueError):
        await resource_pool.add_resource("test", wrong_config)

    # Test allocating from empty pool
    assert await resource_pool.allocate("owner") is None

    # Add and allocate a resource
    await resource_pool.add_resource("test", test_config)
    resource = await resource_pool.allocate("owner")
    assert resource is not None

    # Test allocating when no resources available
    assert await resource_pool.allocate("owner2") is None

    # Test releasing non-existent resource
    with pytest.raises(ValueError):
        await resource_pool.release("non-existent")

    # Test releasing already released resource
    await resource_pool.release("test")
    with pytest.raises(ValueError):
        await resource_pool.release("test")
