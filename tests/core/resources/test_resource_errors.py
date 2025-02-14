"""Tests for resource error handling."""

from typing import Type

import pytest

from pepperpy.core.resources import (
    Resource,
    ResourceConfig,
    ResourceManager,
    ResourceState,
)


class ErrorResource(Resource):
    """Test resource that raises errors."""

    def __init__(
        self,
        name: str,
        config: ResourceConfig,
        *,
        raise_on_initialize: bool = False,
        raise_on_cleanup: bool = False,
    ):
        """Initialize the error resource.

        Args:
            name: The name of the resource.
            config: The resource configuration.
            raise_on_initialize: Whether to raise an error during initialization.
            raise_on_cleanup: Whether to raise an error during cleanup.

        """
        super().__init__(name, config)
        self.raise_on_initialize = raise_on_initialize
        self.raise_on_cleanup = raise_on_cleanup

    async def _initialize(self) -> None:
        """Initialize the error resource."""
        if self.raise_on_initialize:
            raise ValueError("Initialization error")
        self._metadata["initialized"] = True

    async def _cleanup(self) -> None:
        """Clean up the error resource."""
        if self.raise_on_cleanup:
            raise ValueError("Cleanup error")
        self._metadata["cleaned_up"] = True


def create_error_resource(
    *, raise_on_initialize: bool = False, raise_on_cleanup: bool = False
) -> Type[Resource]:
    """Create an error resource class.

    Args:
        raise_on_initialize: Whether to raise an error during initialization.
        raise_on_cleanup: Whether to raise an error during cleanup.

    Returns:
        A resource class that raises errors as specified.

    """

    class _ErrorResource(ErrorResource):
        def __init__(self, name: str, config: ResourceConfig):
            super().__init__(
                name,
                config,
                raise_on_initialize=raise_on_initialize,
                raise_on_cleanup=raise_on_cleanup,
            )

    return _ErrorResource


@pytest.mark.asyncio
async def test_resource_initialization_error(
    resource_manager: ResourceManager, test_config: ResourceConfig
):
    """Test resource initialization error handling."""
    # Create resource that fails initialization
    with pytest.raises(ValueError) as exc:
        await resource_manager.register(
            "error",
            test_config,
            resource_class=create_error_resource(raise_on_initialize=True),
        )
    assert str(exc.value) == "Initialization error"

    # Verify resource is not registered
    assert await resource_manager.get("error") is None


@pytest.mark.asyncio
async def test_resource_cleanup_error(
    resource_manager: ResourceManager, test_config: ResourceConfig
):
    """Test resource cleanup error handling."""
    # Register resource that fails cleanup
    resource = await resource_manager.register(
        "error",
        test_config,
        resource_class=create_error_resource(raise_on_cleanup=True),
    )

    # Verify resource is initialized
    assert resource.state == ResourceState.READY
    assert resource.metadata["initialized"] is True

    # Attempt cleanup
    with pytest.raises(ValueError) as exc:
        await resource_manager.unregister("error")
    assert str(exc.value) == "Cleanup error"

    # Verify resource is removed despite cleanup error
    assert await resource_manager.get("error") is None


@pytest.mark.asyncio
async def test_resource_error_state(
    resource_manager: ResourceManager, test_config: ResourceConfig
):
    """Test resource error state handling."""
    # Register normal resource
    resource = await resource_manager.register(
        "test",
        test_config,
        resource_class=ErrorResource,
    )

    # Set error on resource
    error_message = "Test error"
    error_type = "TestError"
    error_details = {"detail": "test"}

    resource.set_error(error_message, error_type, error_details)

    # Verify error state
    assert resource.state == ResourceState.ERROR
    assert resource.error is not None
    assert resource.error.message == error_message
    assert resource.error.error_type == error_type
    assert resource.error.details == error_details

    # Clear error
    resource.clear_error()
    assert resource.error is None


@pytest.mark.asyncio
async def test_resource_error_filtering(
    resource_manager: ResourceManager, test_config: ResourceConfig
):
    """Test filtering resources by error state."""
    # Register multiple resources
    resources = []
    for i in range(3):
        resource = await resource_manager.register(
            f"test{i}",
            test_config,
            resource_class=ErrorResource,
        )
        resources.append(resource)

    # Set error on one resource
    resources[1].set_error("Test error", "TestError")

    # Get resources in error state
    error_resources = resource_manager.get_resources_by_state(ResourceState.ERROR)
    assert len(error_resources) == 1
    assert error_resources[0].name == "test1"

    # Get resources in ready state
    ready_resources = resource_manager.get_resources_by_state(ResourceState.READY)
    assert len(ready_resources) == 2
    assert all(r.state == ResourceState.READY for r in ready_resources)
