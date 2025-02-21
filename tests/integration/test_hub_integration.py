"""Integration tests for the Hub system."""

import asyncio
import json
import os
from pathlib import Path
from typing import Any, Dict, List, AsyncGenerator
from uuid import UUID

import pytest
from pepperpy.core.base import Lifecycle
from pepperpy.core.types import ComponentState
from pepperpy.hub.base import Hub, HubConfig, HubType
from pepperpy.hub.errors import HubError, HubValidationError
from pepperpy.hub.manager import HubManager
from pepperpy.hub.marketplace import MarketplaceConfig, MarketplaceManager
from pepperpy.hub.publishing import Publisher, PublishConfig
from pepperpy.hub.security import SecurityConfig, SecurityManager
from pepperpy.hub.storage import StorageMetadata
from pepperpy.hub.storage.local import LocalStorageBackend


@pytest.fixture
async def storage_backend(tmp_path: Path) -> AsyncGenerator[LocalStorageBackend, None]:
    """Create a storage backend for testing."""
    backend = LocalStorageBackend(root_dir=str(tmp_path))
    await backend.initialize()
    yield backend
    await backend.close()


@pytest.fixture
async def security_manager(tmp_path: Path) -> AsyncGenerator[SecurityManager, None]:
    """Create a security manager for testing."""
    config = SecurityConfig(sandbox_enabled=True, verify_signatures=True)
    manager = SecurityManager(config)
    # Initialize through the Lifecycle protocol
    await Lifecycle.initialize(manager)  # type: ignore
    yield manager
    await Lifecycle.cleanup(manager)  # type: ignore


@pytest.fixture
async def marketplace_manager(
    storage_backend: LocalStorageBackend,
    security_manager: SecurityManager
) -> AsyncGenerator[MarketplaceManager, None]:
    """Create a marketplace manager for testing."""
    config = MarketplaceConfig(
        api_url="http://localhost:8000",
        timeout=5,
        max_retries=1
    )
    manager = MarketplaceManager(
        config=config,
        storage=storage_backend,
        security=security_manager
    )
    # Initialize through the Lifecycle protocol
    await Lifecycle.initialize(manager)  # type: ignore
    yield manager
    await Lifecycle.cleanup(manager)  # type: ignore


@pytest.fixture
async def hub_manager(
    tmp_path: Path,
    storage_backend: LocalStorageBackend,
    security_manager: SecurityManager,
    marketplace_manager: MarketplaceManager
) -> AsyncGenerator[HubManager, None]:
    """Create a hub manager for testing."""
    manager = HubManager(root_dir=tmp_path)
    # Set up dependencies through constructor
    manager.storage_backend = storage_backend
    manager.security_manager = security_manager
    manager.marketplace_manager = marketplace_manager
    await manager.initialize()
    yield manager
    await manager.cleanup()


@pytest.fixture
def test_artifact() -> Dict[str, Any]:
    """Create a test artifact."""
    return {
        "name": "test_artifact",
        "version": "1.0.0",
        "type": "agent",
        "description": "Test artifact for integration testing",
        "author": "Test Author",
        "license": "MIT",
        "metadata": {
            "tags": ["test", "integration"],
            "category": "testing"
        },
        "content": {
            "configuration": {
                "model": "gpt-4",
                "temperature": 0.7
            },
            "prompts": [
                {
                    "role": "system",
                    "content": "You are a test agent."
                }
            ]
        }
    }


@pytest.mark.asyncio
async def test_hub_lifecycle(hub_manager: HubManager, tmp_path: Path) -> None:
    """Test complete hub lifecycle."""
    # Create hub configuration
    config = HubConfig(
        type=HubType.LOCAL,
        resources=["test_resource"],
        workflows=["test_workflow"],
        root_dir=tmp_path
    )
    
    # Register hub
    hub = await hub_manager.register("test_hub", config)
    assert hub.name == "test_hub"
    assert hub._state == ComponentState.INITIALIZED
    
    # Verify hub retrieval
    retrieved_hub = await hub_manager.get("test_hub")
    assert retrieved_hub == hub
    
    # Test hub cleanup
    await hub_manager.unregister("test_hub")
    with pytest.raises(HubError):
        await hub_manager.get("test_hub")


@pytest.mark.asyncio
async def test_artifact_publishing(
    hub_manager: HubManager,
    test_artifact: Dict[str, Any],
    tmp_path: Path
) -> None:
    """Test artifact publishing workflow."""
    # Setup
    config = HubConfig(
        type=HubType.LOCAL,
        resources=[],
        workflows=[],
        root_dir=tmp_path
    )
    hub = await hub_manager.register("test_hub", config)
    
    # Create publisher
    publish_config = PublishConfig()
    publisher = Publisher(
        storage=hub_manager.storage_backend,
        security=hub_manager.security_manager,
        marketplace=hub_manager.marketplace_manager,
        config=publish_config
    )
    
    # Create artifact metadata
    metadata = StorageMetadata(
        id=UUID('12345678-1234-5678-1234-567812345678'),  # Fixed UUID for testing
        name=test_artifact["name"],
        version=test_artifact["version"],
        type=test_artifact["type"],
        size=len(json.dumps(test_artifact)),
        hash="sha256:test",  # Mock hash for testing
        metadata={
            "description": test_artifact["description"],
            "author": test_artifact["author"],
            "tags": test_artifact["metadata"]["tags"],
            "content": test_artifact["content"]
        }
    )
    
    # Publish artifact
    artifact_path = tmp_path / "test_artifact.json"
    with open(artifact_path, "w") as f:
        json.dump(test_artifact, f)
    
    artifact_id = await publisher.publish_artifact(
        artifact_id=str(metadata.id),
        artifact_type=metadata.type,
        content=test_artifact["content"],
        metadata=metadata,
        visibility="public"
    )
    assert artifact_id is not None
    
    # Verify artifact was published
    published_path = tmp_path / "artifacts" / f"{artifact_id}.json"
    assert published_path.exists()
    
    # Verify artifact content
    with open(published_path) as f:
        published = json.load(f)
    assert published["name"] == test_artifact["name"]
    assert published["version"] == test_artifact["version"]


@pytest.mark.asyncio
async def test_marketplace_integration(
    hub_manager: HubManager,
    test_artifact: Dict[str, Any],
    tmp_path: Path
) -> None:
    """Test marketplace integration."""
    # Setup
    config = HubConfig(
        type=HubType.LOCAL,
        resources=[],
        workflows=[],
        root_dir=tmp_path
    )
    hub = await hub_manager.register("test_hub", config)
    
    # Create artifact metadata
    metadata = StorageMetadata(
        id=UUID('12345678-1234-5678-1234-567812345678'),  # Fixed UUID for testing
        name=test_artifact["name"],
        version=test_artifact["version"],
        type=test_artifact["type"],
        size=len(json.dumps(test_artifact)),
        hash="sha256:test",  # Mock hash for testing
        metadata={
            "description": test_artifact["description"],
            "author": test_artifact["author"],
            "tags": test_artifact["metadata"]["tags"],
            "content": test_artifact["content"]
        }
    )
    
    # Publish artifact to marketplace
    artifact_path = tmp_path / "test_artifact.json"
    with open(artifact_path, "w") as f:
        json.dump(test_artifact, f)
    
    marketplace = hub_manager.marketplace_manager
    artifact_id = await marketplace.publish_artifact(
        artifact_id=str(metadata.id),
        artifact_type=metadata.type,
        content=test_artifact["content"],
        metadata=metadata,
        visibility="public"
    )
    assert artifact_id is not None
    
    # Search for artifact
    results = await marketplace.search("test_artifact")
    assert len(results) > 0
    assert any(r.id == artifact_id for r in results)
    
    # Install artifact
    install_path = await marketplace.install(artifact_id)
    assert install_path.exists()
    
    # Verify installed artifact
    with open(install_path) as f:
        installed = json.load(f)
    assert installed["name"] == test_artifact["name"]
    assert installed["version"] == test_artifact["version"]


@pytest.mark.asyncio
async def test_security_validation(
    hub_manager: HubManager,
    test_artifact: Dict[str, Any],
    tmp_path: Path
) -> None:
    """Test security validation of artifacts."""
    # Setup
    config = HubConfig(
        type=HubType.LOCAL,
        resources=[],
        workflows=[],
        root_dir=tmp_path
    )
    hub = await hub_manager.register("test_hub", config)
    
    # Create artifact metadata
    metadata = StorageMetadata(
        id=UUID('12345678-1234-5678-1234-567812345678'),  # Fixed UUID for testing
        name=test_artifact["name"],
        version=test_artifact["version"],
        type=test_artifact["type"],
        size=len(json.dumps(test_artifact)),
        hash="sha256:test",  # Mock hash for testing
        metadata={
            "description": test_artifact["description"],
            "author": test_artifact["author"],
            "tags": test_artifact["metadata"]["tags"],
            "content": test_artifact["content"]
        }
    )
    
    # Test valid artifact
    artifact_path = tmp_path / "test_artifact.json"
    with open(artifact_path, "w") as f:
        json.dump(test_artifact, f)
    
    # Validate artifact
    security = hub_manager.security_manager
    validation_result = await security.validate_artifact(
        artifact_type=metadata.type,
        content=test_artifact["content"],
        metadata=metadata.dict()
    )
    assert validation_result.is_valid
    assert not validation_result.errors
    
    # Test invalid artifact
    invalid_artifact = test_artifact.copy()
    del invalid_artifact["version"]  # Remove required field
    
    invalid_path = tmp_path / "invalid_artifact.json"
    with open(invalid_path, "w") as f:
        json.dump(invalid_artifact, f)
    
    # Create invalid metadata
    invalid_metadata = metadata.copy()
    invalid_metadata.version = ""  # Invalid version
    
    # Validate invalid artifact
    validation_result = await security.validate_artifact(
        artifact_type=invalid_metadata.type,
        content=invalid_artifact["content"],
        metadata=invalid_metadata.dict()
    )
    assert not validation_result.is_valid
    assert validation_result.errors


@pytest.mark.asyncio
async def test_hub_file_watching(hub_manager: HubManager, tmp_path: Path) -> None:
    """Test hub file watching capabilities."""
    # Setup
    config = HubConfig(
        type=HubType.LOCAL,
        resources=[],
        workflows=[],
        root_dir=tmp_path
    )
    hub = await hub_manager.register("test_hub", config)
    
    # Create test file
    test_file = tmp_path / "test.txt"
    with open(test_file, "w") as f:
        f.write("initial content")
    
    # Setup watching
    changes: List[str] = []
    
    async def on_change(path: str) -> None:
        changes.append(path)
    
    await hub_manager.watch("test_hub", str(test_file), on_change)
    
    # Modify file
    with open(test_file, "w") as f:
        f.write("modified content")
    
    # Wait for change to be detected
    await asyncio.sleep(1)
    assert len(changes) > 0
    assert str(test_file) in changes[0]
