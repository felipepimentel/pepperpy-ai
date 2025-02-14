"""Tests for resource dependencies."""

from typing import List, Type

import pytest

from pepperpy.core.resources import (
    Resource,
    ResourceConfig,
    ResourceManager,
    ResourceState,
)


class DependentResource(Resource):
    """Resource with dependencies."""

    def __init__(
        self,
        name: str,
        config: ResourceConfig,
        *,
        dependencies: List[str],
        resource_manager: ResourceManager,
    ):
        """Initialize the resource.

        Args:
            name: Resource name
            config: Resource configuration
            dependencies: List of dependency names
            resource_manager: Resource manager instance

        """
        super().__init__(name, config)
        self.dependencies = dependencies
        self.resource_manager = resource_manager
        self.initialize_called = False
        self.cleanup_called = False

    async def _initialize(self) -> None:
        """Initialize the resource and validate dependencies."""
        # Check dependencies exist
        for dep_name in self.dependencies:
            dep = await self.resource_manager.get(dep_name)
            if not dep:
                raise ValueError(f"Dependency {dep_name} not found")
            if dep.state != ResourceState.READY:
                raise ValueError(f"Dependency {dep_name} not ready")
        self.initialize_called = True

    async def _cleanup(self) -> None:
        """Clean up the resource."""
        self.cleanup_called = True


def create_dependent_resource(
    dependencies: List[str], resource_manager: ResourceManager
) -> Type[Resource]:
    """Create a dependent resource class.

    Args:
        dependencies: List of dependency names
        resource_manager: Resource manager instance

    Returns:
        Resource class with dependencies

    """

    class _DependentResource(DependentResource):
        def __init__(self, name: str, config: ResourceConfig):
            super().__init__(
                name,
                config,
                dependencies=dependencies,
                resource_manager=resource_manager,
            )

    return _DependentResource


@pytest.mark.asyncio
async def test_resource_dependency_initialization(
    resource_manager: ResourceManager, test_config: ResourceConfig
):
    """Test resource dependency initialization."""
    # Register dependency first
    await resource_manager.register("dependency", test_config)

    # Register dependent resource
    resource_class = create_dependent_resource(["dependency"], resource_manager)
    dependent = await resource_manager.register(
        "dependent",
        test_config,
        resource_class=resource_class,
    )

    # Verify initialization
    assert dependent.state == ResourceState.READY
    assert isinstance(dependent, DependentResource) and dependent.initialize_called


@pytest.mark.asyncio
async def test_resource_missing_dependency(
    resource_manager: ResourceManager, test_config: ResourceConfig
):
    """Test handling of missing dependencies."""
    # Try to register resource with missing dependency
    resource_class = create_dependent_resource(["missing"], resource_manager)
    with pytest.raises(ValueError) as exc:
        await resource_manager.register(
            "dependent",
            test_config,
            resource_class=resource_class,
        )
    assert str(exc.value) == "Dependency missing not found"


@pytest.mark.asyncio
async def test_resource_unready_dependency(
    resource_manager: ResourceManager, test_config: ResourceConfig
):
    """Test handling of unready dependencies."""

    # Create an unready dependency
    class UnreadyResource(Resource):
        async def _initialize(self) -> None:
            self._state = ResourceState.ERROR

        async def _cleanup(self) -> None:
            pass

    await resource_manager.register(
        "dependency",
        test_config,
        resource_class=UnreadyResource,
    )

    # Try to register dependent resource
    resource_class = create_dependent_resource(["dependency"], resource_manager)
    with pytest.raises(ValueError) as exc:
        await resource_manager.register(
            "dependent",
            test_config,
            resource_class=resource_class,
        )
    assert str(exc.value) == "Dependency dependency not ready"


@pytest.mark.asyncio
async def test_resource_multiple_dependencies(
    resource_manager: ResourceManager, test_config: ResourceConfig
):
    """Test handling of multiple dependencies."""
    # Register multiple dependencies
    for i in range(3):
        await resource_manager.register(f"dependency{i}", test_config)

    # Register resource with multiple dependencies
    resource_class = create_dependent_resource(
        [f"dependency{i}" for i in range(3)],
        resource_manager,
    )
    dependent = await resource_manager.register(
        "dependent",
        test_config,
        resource_class=resource_class,
    )

    # Verify initialization
    assert dependent.state == ResourceState.READY
    assert isinstance(dependent, DependentResource) and dependent.initialize_called


@pytest.mark.asyncio
async def test_resource_dependency_cleanup_order(
    resource_manager: ResourceManager, test_config: ResourceConfig
):
    """Test cleanup order of dependent resources."""
    # Register dependency and dependent resource
    await resource_manager.register("dependency", test_config)
    resource_class = create_dependent_resource(["dependency"], resource_manager)
    dependent = await resource_manager.register(
        "dependent",
        test_config,
        resource_class=resource_class,
    )

    # Clean up resources
    await resource_manager.cleanup()

    # Verify cleanup
    assert dependent.state == ResourceState.TERMINATED
    assert isinstance(dependent, DependentResource) and dependent.cleanup_called
