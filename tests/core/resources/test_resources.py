"""Tests for the resource management system."""

from typing import Dict

import pytest

from pepperpy.core.resources.base import (
    Resource,
    ResourceConfig,
    ResourceError,
    ResourceProvider,
    ResourceType,
)
from pepperpy.core.resources.manager import ResourceManager


class TestResource(Resource):
    """Test implementation of a resource."""

    def __init__(
        self,
        name: str,
        config: ResourceConfig,
        fail_init: bool = False,
        fail_cleanup: bool = False,
    ) -> None:
        super().__init__(name, config)
        self.fail_init = fail_init
        self.fail_cleanup = fail_cleanup
        self.initialize_called = False
        self.cleanup_called = False
        self.validate_called = False

    async def initialize(self) -> None:
        """Test initialization implementation."""
        self.initialize_called = True
        if self.fail_init:
            raise ResourceError(
                "Test initialization error",
                self.config.type,
                self.name,
            )

    async def cleanup(self) -> None:
        """Test cleanup implementation."""
        self.cleanup_called = True
        if self.fail_cleanup:
            raise ResourceError(
                "Test cleanup error",
                self.config.type,
                self.name,
            )

    async def validate(self) -> None:
        """Test validation implementation."""
        self.validate_called = True
        await super().validate()


class TestProvider(ResourceProvider):
    """Test implementation of a resource provider."""

    def __init__(self, fail_create: bool = False, fail_delete: bool = False) -> None:
        self.fail_create = fail_create
        self.fail_delete = fail_delete
        self.created_resources: Dict[str, TestResource] = {}

    async def create_resource(
        self,
        name: str,
        config: ResourceConfig,
    ) -> Resource:
        """Create a test resource."""
        if self.fail_create:
            raise ResourceError(
                "Test creation error",
                config.type,
                name,
            )

        resource = TestResource(name, config)
        self.created_resources[name] = resource
        return resource

    async def delete_resource(
        self,
        resource: Resource,
    ) -> None:
        """Delete a test resource."""
        if self.fail_delete:
            raise ResourceError(
                "Test deletion error",
                resource.config.type,
                resource.name,
            )

        if resource.name in self.created_resources:
            del self.created_resources[resource.name]


@pytest.fixture
def resource_manager() -> ResourceManager:
    """Provide a resource manager instance."""
    return ResourceManager()


@pytest.fixture
def test_config() -> ResourceConfig:
    """Provide a test resource configuration."""
    return ResourceConfig(
        type=ResourceType.STORAGE,
        settings={"path": "/test"},
        metadata={"env": "test"},
    )


@pytest.mark.asyncio
async def test_resource_lifecycle(
    resource_manager: ResourceManager, test_config: ResourceConfig
):
    """Test basic resource lifecycle."""
    # Initialize manager
    await resource_manager.initialize()

    # Register provider
    provider = TestProvider()
    resource_manager.register_provider(ResourceType.STORAGE.value, provider)

    # Create resource
    resource = await resource_manager.create_resource("test_resource", test_config)
    assert isinstance(resource, TestResource)
    assert resource.name == "test_resource"
    assert resource.config == test_config
    assert resource.initialize_called
    assert resource.validate_called

    # Get resource
    retrieved = resource_manager.get_resource("test_resource")
    assert retrieved == resource

    # Delete resource
    await resource_manager.delete_resource("test_resource")
    assert resource.cleanup_called
    assert "test_resource" not in provider.created_resources

    # Clean up manager
    await resource_manager.cleanup()


@pytest.mark.asyncio
async def test_resource_dependencies(
    resource_manager: ResourceManager, test_config: ResourceConfig
):
    """Test resource dependency management."""
    await resource_manager.initialize()
    provider = TestProvider()
    resource_manager.register_provider(ResourceType.STORAGE.value, provider)

    # Create dependency
    dep_config = ResourceConfig(
        type=ResourceType.STORAGE,
        settings={"path": "/dep"},
    )
    dependency = await resource_manager.create_resource("dependency", dep_config)
    assert isinstance(dependency, TestResource)

    # Create dependent resource
    resource = await resource_manager.create_resource(
        "dependent",
        test_config,
        dependencies=["dependency"],
    )
    assert isinstance(resource, TestResource)

    # Try to delete dependency (should fail)
    with pytest.raises(ValueError) as exc:
        await resource_manager.delete_resource("dependency")
    assert "Cannot delete resource with dependents" in str(exc.value)

    # Delete dependent first
    await resource_manager.delete_resource("dependent")
    assert resource.cleanup_called

    # Now can delete dependency
    await resource_manager.delete_resource("dependency")
    assert dependency.cleanup_called

    await resource_manager.cleanup()


@pytest.mark.asyncio
async def test_resource_error_handling(
    resource_manager: ResourceManager, test_config: ResourceConfig
):
    """Test resource error handling."""
    await resource_manager.initialize()

    # Test creation failure
    provider = TestProvider(fail_create=True)
    resource_manager.register_provider(ResourceType.STORAGE.value, provider)

    with pytest.raises(ResourceError) as exc:
        await resource_manager.create_resource("test", test_config)
    assert "Test creation error" in str(exc.value)

    # Test initialization failure
    provider = TestProvider()
    resource_manager.register_provider(ResourceType.STORAGE.value, provider)

    config = ResourceConfig(
        type=ResourceType.STORAGE,
        settings={"fail_init": True},
    )

    with pytest.raises(ResourceError) as exc:
        await resource_manager.create_resource("test", config)
    assert "Test initialization error" in str(exc.value)

    # Test deletion failure
    provider = TestProvider(fail_delete=True)
    resource_manager.register_provider(ResourceType.STORAGE.value, provider)

    resource = await resource_manager.create_resource("test", test_config)
    with pytest.raises(ResourceError) as exc:
        await resource_manager.delete_resource("test")
    assert "Test deletion error" in str(exc.value)

    await resource_manager.cleanup()


@pytest.mark.asyncio
async def test_resource_validation(resource_manager: ResourceManager):
    """Test resource validation."""
    await resource_manager.initialize()
    provider = TestProvider()
    resource_manager.register_provider(ResourceType.STORAGE.value, provider)

    # Test with missing config
    config = ResourceConfig(type=ResourceType.STORAGE)
    resource = await resource_manager.create_resource("test", config)
    assert resource.validate_called

    await resource_manager.cleanup()


@pytest.mark.asyncio
async def test_provider_management(resource_manager: ResourceManager):
    """Test provider registration and management."""
    await resource_manager.initialize()

    # Register provider
    provider = TestProvider()
    resource_manager.register_provider(ResourceType.STORAGE.value, provider)

    # Try to register duplicate provider
    with pytest.raises(ValueError) as exc:
        resource_manager.register_provider(ResourceType.STORAGE.value, TestProvider())
    assert "already registered" in str(exc.value)

    # Try to create resource with no provider
    config = ResourceConfig(type=ResourceType.COMPUTE)
    with pytest.raises(ResourceError) as exc:
        await resource_manager.create_resource("test", config)
    assert "No provider registered" in str(exc.value)

    await resource_manager.cleanup()
