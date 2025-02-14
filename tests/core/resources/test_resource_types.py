"""Tests for specific resource types."""

import pytest

from pepperpy.core.resources import (
    Resource,
    ResourceConfig,
    ResourceManager,
    ResourceState,
    ResourceType,
)


class StorageResource(Resource):
    """Test storage resource implementation."""

    async def _initialize(self) -> None:
        """Initialize the storage resource."""
        self._metadata["path"] = self.config.settings["path"]
        self._metadata["initialized"] = True

    async def _cleanup(self) -> None:
        """Clean up the storage resource."""
        self._metadata["cleaned_up"] = True


class ComputeResource(Resource):
    """Test compute resource implementation."""

    async def _initialize(self) -> None:
        """Initialize the compute resource."""
        self._metadata["cpu"] = self.config.settings["cpu"]
        self._metadata["memory"] = self.config.settings.get("memory", "1GB")
        self._metadata["initialized"] = True

    async def _cleanup(self) -> None:
        """Clean up the compute resource."""
        self._metadata["cleaned_up"] = True


class NetworkResource(Resource):
    """Test network resource implementation."""

    async def _initialize(self) -> None:
        """Initialize the network resource."""
        self._metadata["port"] = self.config.settings["port"]
        self._metadata["host"] = self.config.settings.get("host", "localhost")
        self._metadata["initialized"] = True

    async def _cleanup(self) -> None:
        """Clean up the network resource."""
        self._metadata["cleaned_up"] = True


@pytest.fixture
async def storage_config() -> ResourceConfig:
    """Create a storage resource configuration."""
    return ResourceConfig(
        type=ResourceType.STORAGE,
        settings={"path": "/tmp/storage"},
        metadata={"env": "test"},
    )


@pytest.fixture
async def compute_config() -> ResourceConfig:
    """Create a compute resource configuration."""
    return ResourceConfig(
        type=ResourceType.COMPUTE,
        settings={"cpu": 4, "memory": "8GB"},
        metadata={"env": "test"},
    )


@pytest.fixture
async def network_config() -> ResourceConfig:
    """Create a network resource configuration."""
    return ResourceConfig(
        type=ResourceType.NETWORK,
        settings={"port": 8080, "host": "localhost"},
        metadata={"env": "test"},
    )


@pytest.mark.asyncio
async def test_storage_resource(
    resource_manager: ResourceManager, storage_config: ResourceConfig
):
    """Test storage resource functionality."""
    resource = await resource_manager.register("storage", storage_config)
    assert resource.state == ResourceState.READY
    assert resource.metadata["initialized"] is True
    assert resource.metadata["path"] == "/tmp/storage"

    await resource_manager.unregister("storage")
    assert resource.state == ResourceState.TERMINATED
    assert resource.metadata["cleaned_up"] is True


@pytest.mark.asyncio
async def test_compute_resource(
    resource_manager: ResourceManager, compute_config: ResourceConfig
):
    """Test compute resource functionality."""
    resource = await resource_manager.register("compute", compute_config)
    assert resource.state == ResourceState.READY
    assert resource.metadata["initialized"] is True
    assert resource.metadata["cpu"] == 4
    assert resource.metadata["memory"] == "8GB"

    await resource_manager.unregister("compute")
    assert resource.state == ResourceState.TERMINATED
    assert resource.metadata["cleaned_up"] is True


@pytest.mark.asyncio
async def test_network_resource(
    resource_manager: ResourceManager, network_config: ResourceConfig
):
    """Test network resource functionality."""
    resource = await resource_manager.register("network", network_config)
    assert resource.state == ResourceState.READY
    assert resource.metadata["initialized"] is True
    assert resource.metadata["port"] == 8080
    assert resource.metadata["host"] == "localhost"

    await resource_manager.unregister("network")
    assert resource.state == ResourceState.TERMINATED
    assert resource.metadata["cleaned_up"] is True


@pytest.mark.asyncio
async def test_mixed_resources(
    resource_manager: ResourceManager,
    storage_config: ResourceConfig,
    compute_config: ResourceConfig,
    network_config: ResourceConfig,
):
    """Test managing multiple resource types."""
    # Register different types of resources
    storage = await resource_manager.register("storage", storage_config)
    compute = await resource_manager.register("compute", compute_config)
    network = await resource_manager.register("network", network_config)

    # Verify all resources are initialized
    assert all(r.state == ResourceState.READY for r in [storage, compute, network])

    # Test type-specific filtering
    storage_resources = resource_manager.get_resources_by_type("storage")
    assert len(storage_resources) == 1
    assert storage_resources[0].name == "storage"

    compute_resources = resource_manager.get_resources_by_type("compute")
    assert len(compute_resources) == 1
    assert compute_resources[0].name == "compute"

    network_resources = resource_manager.get_resources_by_type("network")
    assert len(network_resources) == 1
    assert network_resources[0].name == "network"

    # Clean up all resources
    for name in ["storage", "compute", "network"]:
        await resource_manager.unregister(name)

    # Verify all resources are cleaned up
    resources = await resource_manager.list()
    assert len(resources) == 0
