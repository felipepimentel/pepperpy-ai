"""Tests for the unified resource management system."""

from datetime import datetime, timedelta

import pytest

from pepperpy.core.resources.unified import (
    MemoryResourceProvider,
    Resource,
    ResourceError,
    ResourceMetadata,
    ResourceMonitor,
    UnifiedResourceManager,
)


@pytest.fixture
def metadata() -> ResourceMetadata:
    """Fixture providing resource metadata."""
    return ResourceMetadata(
        resource_type="test",
        allocation_time=datetime.now(),
        expiration_time=None,
        limits={"max_size": 1000},
        tags={"purpose": "test"},
    )


@pytest.fixture
def memory_provider() -> MemoryResourceProvider:
    """Fixture providing a memory resource provider."""
    return MemoryResourceProvider({"total": 1000000, "max_size": 100000})


@pytest.fixture
def manager() -> UnifiedResourceManager:
    """Fixture providing a resource manager."""
    return UnifiedResourceManager()


@pytest.fixture
def monitor() -> ResourceMonitor:
    """Fixture providing a resource monitor."""
    return ResourceMonitor()


def test_resource_metadata():
    """Test resource metadata creation and conversion."""
    expiration = datetime.now() + timedelta(hours=1)
    metadata = ResourceMetadata(
        resource_type="test",
        allocation_time=datetime.now(),
        expiration_time=expiration,
        limits={"max_size": 1000},
        tags={"purpose": "test"},
    )

    assert metadata.resource_type == "test"
    assert metadata.limits == {"max_size": 1000}
    assert metadata.tags == {"purpose": "test"}
    assert metadata.expiration_time == expiration

    # Test dictionary conversion
    metadata_dict = metadata.to_dict()
    assert metadata_dict["resource_type"] == "test"
    assert metadata_dict["limits"] == {"max_size": 1000}
    assert metadata_dict["tags"] == {"purpose": "test"}
    assert isinstance(metadata_dict["allocation_time"], str)
    assert isinstance(metadata_dict["expiration_time"], str)


def test_resource():
    """Test resource creation and conversion."""
    metadata = ResourceMetadata(
        resource_type="test",
        allocation_time=datetime.now(),
        expiration_time=None,
        limits={},
        tags={},
    )

    resource = Resource(
        id="test-id",
        data=1000,
        metadata=metadata,
        state="allocated",
        error=None,
    )

    assert resource.id == "test-id"
    assert resource.data == 1000
    assert resource.state == "allocated"
    assert not resource.error

    # Test dictionary conversion
    resource_dict = resource.to_dict()
    assert resource_dict["id"] == "test-id"
    assert resource_dict["data"] == 1000
    assert resource_dict["state"] == "allocated"
    assert not resource_dict["error"]
    assert isinstance(resource_dict["metadata"], dict)


class TestMemoryResourceProvider:
    """Tests for the memory resource provider."""

    @pytest.mark.asyncio
    async def test_allocate_memory(self, memory_provider, metadata):
        """Test memory allocation."""
        resource = await memory_provider.allocate("memory", metadata, size=1000)

        assert resource.data == 1000
        assert resource.state == "allocated"
        assert not resource.error
        assert resource.id in memory_provider._allocated

    @pytest.mark.asyncio
    async def test_allocate_exceeding_total(self, memory_provider, metadata):
        """Test allocating memory exceeding total limit."""
        with pytest.raises(ResourceError) as exc:
            await memory_provider.allocate("memory", metadata, size=2000000)
        assert exc.value.code == "RES007"

    @pytest.mark.asyncio
    async def test_release_memory(self, memory_provider, metadata):
        """Test memory release."""
        resource = await memory_provider.allocate("memory", metadata, size=1000)
        await memory_provider.release(resource)

        assert resource.id not in memory_provider._allocated

    @pytest.mark.asyncio
    async def test_release_nonexistent(self, memory_provider, metadata):
        """Test releasing non-existent memory."""
        resource = Resource(
            id="nonexistent",
            data=1000,
            metadata=metadata,
            state="allocated",
            error=None,
        )

        with pytest.raises(ResourceError) as exc:
            await memory_provider.release(resource)
        assert exc.value.code == "RES008"

    @pytest.mark.asyncio
    async def test_validate_memory(self, memory_provider, metadata):
        """Test memory validation."""
        resource = await memory_provider.allocate("memory", metadata, size=1000)
        errors = await memory_provider.validate(resource)

        assert not errors

    @pytest.mark.asyncio
    async def test_validate_exceeding_size(self, memory_provider, metadata):
        """Test validating memory exceeding size limit."""
        resource = Resource(
            id="test",
            data=200000,
            metadata=metadata,
            state="allocated",
            error=None,
        )

        errors = await memory_provider.validate(resource)
        assert len(errors) == 1
        assert "Resource size exceeds limit" in errors

    @pytest.mark.asyncio
    async def test_cleanup(self, memory_provider, metadata):
        """Test memory cleanup."""
        await memory_provider.allocate("memory", metadata, size=1000)
        await memory_provider.cleanup()

        assert not memory_provider._allocated


class TestUnifiedResourceManager:
    """Tests for the unified resource manager."""

    def test_register_provider(self, manager, memory_provider):
        """Test provider registration."""
        manager.register_provider("memory", memory_provider)

        assert "memory" in manager._providers
        assert manager._providers["memory"] == memory_provider

    def test_register_duplicate_provider(self, manager, memory_provider):
        """Test registering duplicate provider."""
        manager.register_provider("memory", memory_provider)

        with pytest.raises(ResourceError) as exc:
            manager.register_provider("memory", memory_provider)
        assert exc.value.code == "RES002"

    @pytest.mark.asyncio
    async def test_allocate_resource(self, manager, memory_provider):
        """Test resource allocation."""
        manager.register_provider("memory", memory_provider)

        resource = await manager.allocate(
            "memory",
            size=1000,
            tags={"purpose": "test"},
        )

        assert resource.data == 1000
        assert resource.state == "allocated"
        assert resource.metadata.tags["purpose"] == "test"
        assert resource.id in manager._resources

    @pytest.mark.asyncio
    async def test_allocate_nonexistent_provider(self, manager):
        """Test allocating with non-existent provider."""
        with pytest.raises(ResourceError) as exc:
            await manager.allocate("nonexistent")
        assert exc.value.code == "RES003"

    @pytest.mark.asyncio
    async def test_release_resource(self, manager, memory_provider):
        """Test resource release."""
        manager.register_provider("memory", memory_provider)
        resource = await manager.allocate("memory", size=1000)

        await manager.release(resource.id)
        assert resource.id not in manager._resources

    @pytest.mark.asyncio
    async def test_release_nonexistent_resource(self, manager):
        """Test releasing non-existent resource."""
        with pytest.raises(ResourceError) as exc:
            await manager.release("nonexistent")
        assert exc.value.code == "RES005"

    @pytest.mark.asyncio
    async def test_cleanup(self, manager, memory_provider):
        """Test manager cleanup."""
        manager.register_provider("memory", memory_provider)
        await manager.allocate("memory", size=1000)

        await manager.cleanup()
        assert not memory_provider._allocated


class TestResourceMonitor:
    """Tests for the resource monitor."""

    @pytest.mark.asyncio
    async def test_record_allocation(self, monitor):
        """Test recording allocation operation."""
        await monitor.record_allocation(
            "memory",
            success=True,
            size=1000,
        )

    @pytest.mark.asyncio
    async def test_record_failed_allocation(self, monitor):
        """Test recording failed allocation operation."""
        await monitor.record_allocation(
            "memory",
            success=False,
            error="Out of memory",
        )

    @pytest.mark.asyncio
    async def test_record_release(self, monitor):
        """Test recording release operation."""
        await monitor.record_release(
            "memory",
            success=True,
            resource_id="test-id",
        )

    @pytest.mark.asyncio
    async def test_record_failed_release(self, monitor):
        """Test recording failed release operation."""
        await monitor.record_release(
            "memory",
            success=False,
            error="Resource not found",
        )
