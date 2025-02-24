"""Test resource lifecycle module."""

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pepperpy.core.errors import ValidationError
from pepperpy.core.types import ComponentState
from pepperpy.resources.lifecycle import ResourceLifecycle
from pepperpy.resources.pool import ResourcePool
from pepperpy.resources.types import Resource


@pytest.fixture
def resource() -> MagicMock:
    """Create mock resource."""
    resource = MagicMock(spec=Resource)
    resource.id = "test-resource"
    return resource


@pytest.fixture
def pool() -> MagicMock:
    """Create mock pool."""
    pool = MagicMock(spec=ResourcePool)
    pool.name = "test-pool"
    pool.initialize = AsyncMock()
    pool.cleanup = AsyncMock()
    pool.acquire = AsyncMock()
    pool.release = AsyncMock()
    return pool


@pytest.fixture
async def lifecycle() -> AsyncGenerator[ResourceLifecycle, None]:
    """Create resource lifecycle."""
    lifecycle = ResourceLifecycle(
        cleanup_interval=1,
        monitor_interval=1,
        max_age=10,
        max_retries=1,
    )
    await lifecycle.initialize()
    yield lifecycle
    await lifecycle.cleanup()


async def test_lifecycle_initialization() -> None:
    """Test lifecycle initialization."""
    lifecycle = ResourceLifecycle()
    assert lifecycle._state == ComponentState.CREATED

    await lifecycle.initialize()
    assert lifecycle._state == ComponentState.READY

    await lifecycle.cleanup()
    assert lifecycle._state == ComponentState.CLEANED


async def test_lifecycle_initialization_error() -> None:
    """Test lifecycle initialization error."""
    lifecycle = ResourceLifecycle()
    with patch("pepperpy.resources.cleanup.ResourceCleaner.initialize") as mock_init:
        mock_init.side_effect = Exception("Test error")
        with pytest.raises(ValidationError, match="Failed to initialize lifecycle"):
            await lifecycle.initialize()
        assert lifecycle._state == ComponentState.ERROR


async def test_lifecycle_cleanup_error() -> None:
    """Test lifecycle cleanup error."""
    lifecycle = ResourceLifecycle()
    await lifecycle.initialize()
    with patch("pepperpy.resources.cleanup.ResourceCleaner.cleanup") as mock_cleanup:
        mock_cleanup.side_effect = Exception("Test error")
        with pytest.raises(ValidationError, match="Failed to clean up lifecycle"):
            await lifecycle.cleanup()
        assert lifecycle._state == ComponentState.ERROR


async def test_register_pool(lifecycle: ResourceLifecycle, pool: MagicMock) -> None:
    """Test register pool."""
    lifecycle.register_pool(pool)
    assert pool.name in lifecycle._pools

    with pytest.raises(ValidationError, match="Pool already exists"):
        lifecycle.register_pool(pool)


async def test_unregister_pool(lifecycle: ResourceLifecycle, pool: MagicMock) -> None:
    """Test unregister pool."""
    lifecycle.register_pool(pool)
    lifecycle.unregister_pool(pool.name)
    assert pool.name not in lifecycle._pools

    with pytest.raises(ValidationError, match="Pool not found"):
        lifecycle.unregister_pool(pool.name)


async def test_register_hook(lifecycle: ResourceLifecycle) -> None:
    """Test register hook."""
    hook = AsyncMock()
    lifecycle.register_hook("test", hook)
    assert "test" in lifecycle._hooks
    assert hook in lifecycle._hooks["test"]


async def test_unregister_hook(lifecycle: ResourceLifecycle) -> None:
    """Test unregister hook."""
    hook = AsyncMock()
    lifecycle.register_hook("test", hook)
    lifecycle.unregister_hook("test", hook)
    assert "test" not in lifecycle._hooks


async def test_register_resource(
    lifecycle: ResourceLifecycle,
    resource: MagicMock,
) -> None:
    """Test register resource."""
    await lifecycle.register_resource(resource)
    assert resource.id in lifecycle._resources


async def test_unregister_resource(
    lifecycle: ResourceLifecycle,
    resource: MagicMock,
) -> None:
    """Test unregister resource."""
    await lifecycle.register_resource(resource)
    await lifecycle.unregister_resource(resource.id)
    assert resource.id not in lifecycle._resources


async def test_acquire_resource(
    lifecycle: ResourceLifecycle,
    pool: MagicMock,
    resource: MagicMock,
) -> None:
    """Test acquire resource."""
    lifecycle.register_pool(pool)
    pool.acquire.return_value = resource

    result = await lifecycle.acquire_resource(pool.name, resource.id)
    assert result == resource
    pool.acquire.assert_called_once_with(resource.id)

    with pytest.raises(ValidationError, match="Pool not found"):
        await lifecycle.acquire_resource("invalid-pool", resource.id)


async def test_release_resource(
    lifecycle: ResourceLifecycle,
    pool: MagicMock,
    resource: MagicMock,
) -> None:
    """Test release resource."""
    lifecycle.register_pool(pool)
    await lifecycle.register_resource(resource)

    await lifecycle.release_resource(pool.name, resource.id)
    pool.release.assert_called_once_with(resource.id)

    with pytest.raises(ValidationError, match="Pool not found"):
        await lifecycle.release_resource("invalid-pool", resource.id)


async def test_notify_hooks(
    lifecycle: ResourceLifecycle,
    resource: MagicMock,
) -> None:
    """Test notify hooks."""
    hook1 = AsyncMock()
    hook2 = AsyncMock(side_effect=Exception("Test error"))
    lifecycle.register_hook("test", hook1)
    lifecycle.register_hook("test", hook2)

    await lifecycle._notify_hooks("test", resource)
    hook1.assert_called_once_with(resource)
    hook2.assert_called_once_with(resource)


async def test_get_metrics(
    lifecycle: ResourceLifecycle,
    pool: MagicMock,
) -> None:
    """Test get metrics."""
    lifecycle.register_pool(pool)
    pool._resources = {"test": MagicMock()}
    pool._available = {"test": MagicMock()}
    pool._in_use = {}

    metrics = lifecycle.get_metrics()
    assert "pool_stats" in metrics
    assert pool.name in metrics["pool_stats"]
    assert metrics["pool_stats"][pool.name]["total"] == 1
    assert metrics["pool_stats"][pool.name]["available"] == 1
    assert metrics["pool_stats"][pool.name]["in_use"] == 0
