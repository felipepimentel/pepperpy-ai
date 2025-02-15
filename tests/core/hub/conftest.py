"""Test configuration for hub tests."""

from pathlib import Path
from typing import AsyncGenerator, Dict

import pytest

from pepperpy.core.hub import Hub, HubConfig, HubType


@pytest.fixture
def test_metadata() -> Dict[str, str]:
    """Create test metadata."""
    return {
        "env": "test",
        "version": "1.0.0",
        "description": "Test hub",
    }


@pytest.fixture
def test_resources() -> list[str]:
    """Create test resource list."""
    return [
        "test_resource_1",
        "test_resource_2",
        "test_resource_3",
    ]


@pytest.fixture
def test_workflows() -> list[str]:
    """Create test workflow list."""
    return [
        "test_workflow_1",
        "test_workflow_2",
        "test_workflow_3",
    ]


@pytest.fixture
def local_hub_config(
    test_metadata: Dict[str, str],
    test_resources: list[str],
    test_workflows: list[str],
    tmp_path: Path,
) -> HubConfig:
    """Create a local hub configuration."""
    return HubConfig(
        type=HubType.LOCAL,
        resources=test_resources,
        workflows=test_workflows,
        metadata=test_metadata,
        root_dir=tmp_path,
    )


@pytest.fixture
def remote_hub_config(
    test_metadata: Dict[str, str],
    test_resources: list[str],
    test_workflows: list[str],
) -> HubConfig:
    """Create a remote hub configuration."""
    return HubConfig(
        type=HubType.REMOTE,
        resources=test_resources,
        workflows=test_workflows,
        metadata=test_metadata,
    )


@pytest.fixture
async def local_hub(local_hub_config: HubConfig) -> AsyncGenerator[Hub, None]:
    """Create a local hub instance."""
    hub = Hub("test_local_hub", local_hub_config)
    await hub.initialize()
    yield hub
    await hub.cleanup()


@pytest.fixture
async def remote_hub(remote_hub_config: HubConfig) -> AsyncGenerator[Hub, None]:
    """Create a remote hub instance."""
    hub = Hub("test_remote_hub", remote_hub_config)
    await hub.initialize()
    yield hub
    await hub.cleanup()
