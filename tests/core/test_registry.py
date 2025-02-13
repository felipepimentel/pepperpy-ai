"""Tests for the registry functionality."""

from typing import Any
from uuid import UUID

import pytest

from pepperpy.core.errors import NotFoundError, StateError
from pepperpy.core.registry import CapabilityRegistry, Registry


@pytest.fixture
def registry() -> Registry[Any]:
    """Create a test registry."""
    return Registry[Any](name="test_registry")


@pytest.fixture
def capability_registry() -> CapabilityRegistry:
    """Create a test capability registry."""
    return CapabilityRegistry()


@pytest.mark.asyncio
async def test_registry_initialization(registry: Registry[Any]):
    """Test registry initialization."""
    assert registry.name == "test_registry"
    assert not registry.is_active


@pytest.mark.asyncio
async def test_registry_lifecycle(registry: Registry[Any]):
    """Test registry lifecycle."""
    # Start registry
    await registry.start()
    assert registry.is_active

    # Stop registry
    await registry.stop()
    assert not registry.is_active


@pytest.mark.asyncio
async def test_registry_register(registry: Registry[Any]):
    """Test registering items in the registry."""
    await registry.start()

    # Register a test item
    class TestItem:
        pass

    item_id = await registry.register(
        key="test_key",
        item_type=TestItem,
        version="1.0.0",
        metadata={"name": "test"},
    )
    assert isinstance(item_id, UUID)

    # Get the registered item
    item = await registry.get("test_key", "1.0.0")
    assert item == TestItem

    # Get metadata
    metadata = await registry.get_metadata("test_key", "1.0.0")
    assert metadata["name"] == "test"


@pytest.mark.asyncio
async def test_registry_register_inactive(registry: Registry[Any]):
    """Test registering items in inactive registry."""

    class TestItem:
        pass

    with pytest.raises(StateError):
        await registry.register(
            key="test_key",
            item_type=TestItem,
            version="1.0.0",
        )


@pytest.mark.asyncio
async def test_registry_unregister(registry: Registry[Any]):
    """Test unregistering items from the registry."""
    await registry.start()

    # Register and then unregister
    class TestItem:
        pass

    await registry.register(
        key="test_key",
        item_type=TestItem,
        version="1.0.0",
    )

    # Unregister
    await registry.unregister("test_key", "1.0.0")

    # Verify item is gone
    with pytest.raises(NotFoundError) as exc_info:
        await registry.get("test_key", "1.0.0")
    assert "Item not found with key: test_key" in str(exc_info.value)


@pytest.mark.asyncio
async def test_registry_unregister_nonexistent(registry: Registry[Any]):
    """Test unregistering nonexistent items."""
    await registry.start()

    with pytest.raises(NotFoundError) as exc_info:
        await registry.unregister("nonexistent", "1.0.0")
    assert "Item not found with key: nonexistent" in str(exc_info.value)


@pytest.mark.asyncio
async def test_registry_clear(registry: Registry[Any]):
    """Test clearing the registry."""
    await registry.start()

    # Register multiple items
    class TestItem1:
        pass

    class TestItem2:
        pass

    await registry.register(
        key="key1",
        item_type=TestItem1,
        version="1.0.0",
    )
    await registry.register(
        key="key2",
        item_type=TestItem2,
        version="1.0.0",
    )

    # Clear registry
    await registry.clear()

    # Verify items are gone
    items = registry.list_items()
    assert len(items) == 0


@pytest.mark.asyncio
async def test_capability_registry_register(capability_registry: CapabilityRegistry):
    """Test registering capabilities."""
    await capability_registry.start()

    # Register a capability
    agent_id = UUID("12345678-1234-5678-1234-567812345678")
    capability_id = await capability_registry.register_capability(
        agent_id=agent_id,
        capability_name="test_capability",
        version="1.0.0",
        framework="test_framework",
        requirements=["test_requirement"],
        metadata={"description": "Test capability"},
    )

    assert isinstance(capability_id, UUID)

    # Get the registered capability
    capabilities = capability_registry.get_agent_capabilities(agent_id)
    assert "test_capability" in capabilities
    assert capabilities["test_capability"]["1.0.0"].framework == "test_framework"
    assert capabilities["test_capability"]["1.0.0"].requirements == ["test_requirement"]


@pytest.mark.asyncio
async def test_capability_registry_unregister(capability_registry: CapabilityRegistry):
    """Test unregistering capabilities."""
    await capability_registry.start()

    # Register and then unregister
    agent_id = UUID("12345678-1234-5678-1234-567812345678")
    await capability_registry.register_capability(
        agent_id=agent_id,
        capability_name="test_capability",
        version="1.0.0",
        framework="test_framework",
    )

    # Unregister
    await capability_registry.unregister_capability(
        agent_id=agent_id,
        capability_name="test_capability",
        version="1.0.0",
    )

    # Verify capability is gone
    capabilities = capability_registry.get_agent_capabilities(agent_id)
    assert "test_capability" not in capabilities
