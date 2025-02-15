"""Tests for the hub management system."""

from pathlib import Path
from typing import AsyncGenerator

import pytest

from pepperpy.core.hub import (
    HubConfig,
    HubError,
    HubManager,
    HubNotFoundError,
    HubType,
    HubValidationError,
)


@pytest.fixture
def hub_config() -> HubConfig:
    """Create a test hub configuration."""
    return HubConfig(
        type=HubType.LOCAL,
        resources=["test_resource"],
        workflows=["test_workflow"],
        metadata={"env": "test"},
    )


@pytest.fixture
async def hub_manager(tmp_path: Path) -> AsyncGenerator[HubManager, None]:
    """Create a hub manager instance."""
    manager = HubManager(root_dir=tmp_path)
    await manager.initialize()
    yield manager
    await manager.cleanup()


@pytest.mark.asyncio
async def test_hub_registration(hub_manager: HubManager, hub_config: HubConfig):
    """Test hub registration."""
    # Test successful registration
    hub = await hub_manager.register("test_hub", hub_config)
    assert hub.name == "test_hub"
    assert hub.config == hub_config

    # Test duplicate registration
    with pytest.raises(HubValidationError):
        await hub_manager.register("test_hub", hub_config)

    # Test invalid config
    invalid_config = HubConfig(
        type=HubType.LOCAL,
        resources=[],
        workflows=[],
    )
    with pytest.raises(HubValidationError):
        await hub_manager.register("invalid_hub", invalid_config)


@pytest.mark.asyncio
async def test_hub_retrieval(hub_manager: HubManager, hub_config: HubConfig):
    """Test hub retrieval."""
    # Register a hub
    await hub_manager.register("test_hub", hub_config)

    # Test successful retrieval
    hub = await hub_manager.get("test_hub")
    assert hub.name == "test_hub"
    assert hub.config == hub_config

    # Test non-existent hub
    with pytest.raises(HubNotFoundError):
        await hub_manager.get("non_existent")


@pytest.mark.asyncio
async def test_hub_unregistration(hub_manager: HubManager, hub_config: HubConfig):
    """Test hub unregistration."""
    # Register a hub
    await hub_manager.register("test_hub", hub_config)

    # Test successful unregistration
    await hub_manager.unregister("test_hub")
    with pytest.raises(HubNotFoundError):
        await hub_manager.get("test_hub")

    # Test non-existent hub
    with pytest.raises(HubNotFoundError):
        await hub_manager.unregister("non_existent")


@pytest.mark.asyncio
async def test_hub_file_watching(
    hub_manager: HubManager, hub_config: HubConfig, tmp_path: Path
):
    """Test hub file watching."""
    # Set up test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("initial content")

    # Update config with root dir
    hub_config.root_dir = tmp_path

    # Register hub
    hub = await hub_manager.register("test_hub", hub_config)

    # Set up callback
    callback_called = False
    callback_path = None

    async def callback(path: str):
        nonlocal callback_called, callback_path
        callback_called = True
        callback_path = path

    # Start watching
    await hub_manager.watch("test_hub", str(test_file), callback)

    # Test non-existent hub
    with pytest.raises(HubNotFoundError):
        await hub_manager.watch("non_existent", str(test_file), callback)

    # Test hub without root dir
    no_root_config = HubConfig(
        type=HubType.REMOTE,
        resources=[],
        workflows=[],
    )
    no_root_hub = await hub_manager.register("no_root_hub", no_root_config)
    with pytest.raises(HubError):
        await hub_manager.watch("no_root_hub", str(test_file), callback)


@pytest.mark.asyncio
async def test_hub_cleanup(hub_manager: HubManager, hub_config: HubConfig):
    """Test hub cleanup."""
    # Register multiple hubs
    hub1 = await hub_manager.register("hub1", hub_config)
    hub2 = await hub_manager.register("hub2", hub_config)

    # Set up watchers
    async def callback(path: str):
        pass

    if hub_config.root_dir:
        await hub_manager.watch("hub1", "test.txt", callback)
        await hub_manager.watch("hub2", "test.txt", callback)

    # Clean up manager
    await hub_manager.cleanup()

    # Verify all hubs are cleaned up
    assert not hub_manager._hubs
    assert not hub_manager._watchers


@pytest.mark.asyncio
async def test_hub_initialization(tmp_path: Path):
    """Test hub manager initialization."""
    # Test with non-existent root dir
    invalid_dir = tmp_path / "non_existent"
    manager = HubManager(root_dir=invalid_dir)
    with pytest.raises(HubValidationError):
        await manager.initialize()

    # Test with valid root dir
    valid_dir = tmp_path / "valid"
    valid_dir.mkdir()
    manager = HubManager(root_dir=valid_dir)
    await manager.initialize()
    await manager.cleanup()


@pytest.mark.asyncio
async def test_hub_error_handling(hub_manager: HubManager, hub_config: HubConfig):
    """Test hub error handling."""
    # Test registration with invalid config
    with pytest.raises(HubValidationError):
        await hub_manager.register("test_hub", None)  # type: ignore

    # Register a hub
    hub = await hub_manager.register("test_hub", hub_config)

    # Test cleanup with error
    async def failing_cleanup():
        raise Exception("Cleanup failed")

    hub.cleanup = failing_cleanup  # type: ignore
    with pytest.raises(HubError):
        await hub_manager.unregister("test_hub")
