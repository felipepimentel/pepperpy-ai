"""Tests for hot-reload functionality."""

import asyncio
from typing import Any, Dict

import pytest
import yaml

from pepperpy.hub.watcher import ComponentWatcher, watch_component


@pytest.fixture
def watcher(tmp_path):
    """Create a test watcher with a temporary path."""
    return ComponentWatcher(hub_path=tmp_path)


@pytest.fixture
def mock_config():
    """Create a mock component configuration."""
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
async def test_watch_agent(watcher, tmp_path, mock_config):
    """Test watching an agent configuration."""
    # Create test config file
    config_path = tmp_path / "agents" / "test-agent.yaml"
    config_path.parent.mkdir(parents=True)

    with open(config_path, "w") as f:
        yaml.dump(mock_config, f)

    # Track callback calls
    callback_calls = []

    async def callback(config: Dict[str, Any]):
        callback_calls.append(config)

    # Start watching
    await watcher.watch_agent("test-agent", callback)

    # Modify config
    mock_config["version"] = "0.2.0"
    with open(config_path, "w") as f:
        yaml.dump(mock_config, f)

    # Wait for callback
    await asyncio.sleep(0.1)

    # Stop watcher
    await watcher.stop()

    # Verify callback was called with updated config
    assert len(callback_calls) > 0
    assert callback_calls[-1]["version"] == "0.2.0"


@pytest.mark.asyncio
async def test_watch_workflow(watcher, tmp_path, mock_config):
    """Test watching a workflow configuration."""
    # Create test config file
    config_path = tmp_path / "workflows" / "test-workflow.yaml"
    config_path.parent.mkdir(parents=True)

    with open(config_path, "w") as f:
        yaml.dump(mock_config, f)

    # Track callback calls
    callback_calls = []

    async def callback(config: Dict[str, Any]):
        callback_calls.append(config)

    # Start watching
    await watcher.watch_workflow("test-workflow", callback)

    # Modify config
    mock_config["version"] = "0.2.0"
    with open(config_path, "w") as f:
        yaml.dump(mock_config, f)

    # Wait for callback
    await asyncio.sleep(0.1)

    # Stop watcher
    await watcher.stop()

    # Verify callback was called with updated config
    assert len(callback_calls) > 0
    assert callback_calls[-1]["version"] == "0.2.0"


@pytest.mark.asyncio
async def test_watch_team(watcher, tmp_path, mock_config):
    """Test watching a team configuration."""
    # Create test config file
    config_path = tmp_path / "teams" / "test-team.yaml"
    config_path.parent.mkdir(parents=True)

    with open(config_path, "w") as f:
        yaml.dump(mock_config, f)

    # Track callback calls
    callback_calls = []

    async def callback(config: Dict[str, Any]):
        callback_calls.append(config)

    # Start watching
    await watcher.watch_team("test-team", callback)

    # Modify config
    mock_config["version"] = "0.2.0"
    with open(config_path, "w") as f:
        yaml.dump(mock_config, f)

    # Wait for callback
    await asyncio.sleep(0.1)

    # Stop watcher
    await watcher.stop()

    # Verify callback was called with updated config
    assert len(callback_calls) > 0
    assert callback_calls[-1]["version"] == "0.2.0"


@pytest.mark.asyncio
async def test_watch_component_decorator(tmp_path, mock_config):
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

    # Modify config
    mock_config["version"] = "0.2.0"
    with open(config_path, "w") as f:
        yaml.dump(mock_config, f)

    # Wait for reload
    await asyncio.sleep(0.1)

    # Verify function was called multiple times
    assert len(function_calls) > 1


@pytest.mark.asyncio
async def test_stop_watcher(watcher):
    """Test stopping the watcher."""
    # Start some watchers
    callback = lambda x: None
    await watcher.watch_agent("test-agent", callback)
    await watcher.watch_workflow("test-workflow", callback)
    await watcher.watch_team("test-team", callback)

    # Stop watcher
    await watcher.stop()

    # Verify all watchers are stopped
    assert len(watcher.watchers) == 0
