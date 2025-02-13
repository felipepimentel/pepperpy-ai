"""Tests for the component watcher."""

import asyncio
import logging
from pathlib import Path
from typing import Any, AsyncGenerator, Dict

import pytest
import yaml

from pepperpy.hub.watcher import ComponentWatcher, watch_component


@pytest.fixture(autouse=True)
def setup_logging():
    """Enable debug logging for tests."""
    logging.basicConfig(level=logging.DEBUG)


@pytest.fixture
async def watcher(tmp_path: Path) -> AsyncGenerator[ComponentWatcher, None]:
    """Create a test watcher."""
    watcher = ComponentWatcher(tmp_path)
    await watcher.start()
    yield watcher
    await watcher.stop()


@pytest.fixture
def mock_config() -> Dict[str, Any]:
    """Create a mock configuration."""
    return {
        "name": "test-agent",
        "version": "0.1.0",
        "description": "Test agent",
        "metadata": {
            "author": "Test Author",
            "tags": ["test", "example"],
        },
    }


@pytest.mark.asyncio
async def test_watch_agent(
    watcher: ComponentWatcher, tmp_path: Path, mock_config: Dict[str, Any]
):
    """Test watching an agent configuration."""
    # Create test config file
    config_path = tmp_path / "agents" / "test-agent.yaml"
    config_path.parent.mkdir(parents=True)

    # Write initial config
    with open(config_path, "w") as f:
        yaml.dump(mock_config, f)

    # Track callback calls
    callback_calls = []

    async def callback(config: Dict[str, Any]):
        callback_calls.append(config.copy())

    # Start watching
    await watcher.watch_agent("test-agent", callback)

    # Wait for initial callback
    await asyncio.sleep(0.1)

    # Verify initial callback
    assert len(callback_calls) == 1
    assert callback_calls[0]["version"] == "0.1.0"

    # Modify config
    modified_config = mock_config.copy()
    modified_config["version"] = "0.2.0"

    # Write modified config
    with open(config_path, "w") as f:
        yaml.dump(modified_config, f)

    # Wait for file system events to propagate
    await asyncio.sleep(0.5)

    # Verify callback was called with updated config
    assert len(callback_calls) == 2
    assert callback_calls[1]["version"] == "0.2.0"


@pytest.mark.asyncio
async def test_watch_workflow(
    watcher: ComponentWatcher, tmp_path: Path, mock_config: Dict[str, Any]
):
    """Test watching a workflow configuration."""
    # Create test config file
    config_path = tmp_path / "workflows" / "test-workflow.yaml"
    config_path.parent.mkdir(parents=True)

    # Write initial config
    with open(config_path, "w") as f:
        yaml.dump(mock_config, f)

    # Track callback calls
    callback_calls = []

    async def callback(config: Dict[str, Any]):
        callback_calls.append(config.copy())

    # Start watching
    await watcher.watch_workflow("test-workflow", callback)

    # Wait for initial callback
    await asyncio.sleep(0.1)

    # Verify initial callback
    assert len(callback_calls) == 1
    assert callback_calls[0]["version"] == "0.1.0"

    # Modify config
    modified_config = mock_config.copy()
    modified_config["version"] = "0.2.0"

    # Write modified config
    with open(config_path, "w") as f:
        yaml.dump(modified_config, f)

    # Wait for file system events to propagate
    await asyncio.sleep(0.5)

    # Verify callback was called with updated config
    assert len(callback_calls) == 2
    assert callback_calls[1]["version"] == "0.2.0"


@pytest.mark.asyncio
async def test_watch_team(
    watcher: ComponentWatcher, tmp_path: Path, mock_config: Dict[str, Any]
):
    """Test watching a team configuration."""
    # Create test config file
    config_path = tmp_path / "teams" / "test-team.yaml"
    config_path.parent.mkdir(parents=True)

    # Write initial config
    with open(config_path, "w") as f:
        yaml.dump(mock_config, f)

    # Track callback calls
    callback_calls = []

    async def callback(config: Dict[str, Any]):
        callback_calls.append(config.copy())

    # Start watching
    await watcher.watch_team("test-team", callback)

    # Wait for initial callback
    await asyncio.sleep(0.1)

    # Verify initial callback
    assert len(callback_calls) == 1
    assert callback_calls[0]["version"] == "0.1.0"

    # Modify config
    modified_config = mock_config.copy()
    modified_config["version"] = "0.2.0"

    # Write modified config
    with open(config_path, "w") as f:
        yaml.dump(modified_config, f)

    # Wait for file system events to propagate
    await asyncio.sleep(0.5)

    # Verify callback was called with updated config
    assert len(callback_calls) == 2
    assert callback_calls[1]["version"] == "0.2.0"


@pytest.mark.asyncio
async def test_watch_component_decorator(tmp_path: Path, mock_config: Dict[str, Any]):
    """Test the @watch_component decorator."""
    # Create test config file
    config_path = tmp_path / "test.yaml"
    with open(config_path, "w") as f:
        yaml.dump(mock_config, f)

    # Track function calls
    function_calls = []

    @watch_component(str(config_path))
    async def test_function():
        function_calls.append(True)

    # Run function
    await test_function()

    # Verify function was called once
    assert len(function_calls) == 1


@pytest.mark.asyncio
async def test_stop_watcher(watcher: ComponentWatcher, tmp_path: Path):
    """Test stopping the watcher."""
    # Create test config file
    config_path = tmp_path / "test.yaml"
    with open(config_path, "w") as f:
        yaml.dump({"test": "data"}, f)

    # Track callback calls
    callback_calls = []

    async def callback(config: Dict[str, Any]):
        callback_calls.append(config)

    # Start watching
    await watcher._watch_component(config_path, callback)

    # Stop watcher
    await watcher.stop()

    # Verify watcher is stopped
    assert not watcher.watchers
    assert not watcher.observer.is_alive()
