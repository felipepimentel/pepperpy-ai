"""Tests for resource validation."""

from typing import Dict, Type

import pytest

from pepperpy.core.resources import (
    Resource,
    ResourceConfig,
    ResourceManager,
    ResourceState,
)


class ValidatedResource(Resource):
    """Test resource with validation."""

    def __init__(
        self,
        name: str,
        config: ResourceConfig,
        *,
        required_settings: Dict[str, Type],
        optional_settings: Dict[str, Type] = {},
    ):
        """Initialize the validated resource.

        Args:
            name: The name of the resource.
            config: The resource configuration.
            required_settings: Required settings and their types.
            optional_settings: Optional settings and their types.

        """
        super().__init__(name, config)
        self.required_settings = required_settings
        self.optional_settings = optional_settings

    def validate_settings(self) -> None:
        """Validate resource settings.

        Raises:
            ValueError: If validation fails.

        """
        # Check required settings
        for key, expected_type in self.required_settings.items():
            if key not in self.config.settings:
                raise ValueError(f"Missing required setting: {key}")
            value = self.config.settings[key]
            if not isinstance(value, expected_type):
                raise ValueError(
                    f"Invalid type for setting {key}: "
                    f"expected {expected_type.__name__}, got {type(value).__name__}"
                )

        # Check optional settings
        for key, expected_type in self.optional_settings.items():
            if key in self.config.settings:
                value = self.config.settings[key]
                if not isinstance(value, expected_type):
                    raise ValueError(
                        f"Invalid type for setting {key}: "
                        f"expected {expected_type.__name__}, got {type(value).__name__}"
                    )

    async def _initialize(self) -> None:
        """Initialize the validated resource."""
        self.validate_settings()
        self._metadata["initialized"] = True

    async def _cleanup(self) -> None:
        """Clean up the validated resource."""
        self._metadata["cleaned_up"] = True


def create_validated_resource(
    *, required_settings: Dict[str, Type], optional_settings: Dict[str, Type] = {}
) -> Type[Resource]:
    """Create a validated resource class.

    Args:
        required_settings: Required settings and their types.
        optional_settings: Optional settings and their types.

    Returns:
        A resource class with validation.

    """

    class _ValidatedResource(ValidatedResource):
        def __init__(self, name: str, config: ResourceConfig):
            super().__init__(
                name,
                config,
                required_settings=required_settings,
                optional_settings=optional_settings,
            )

    return _ValidatedResource


@pytest.mark.asyncio
async def test_resource_required_settings(
    resource_manager: ResourceManager, test_config: ResourceConfig
):
    """Test resource with required settings."""
    # Create resource class with required settings
    resource_class = create_validated_resource(
        required_settings={"path": str, "mode": int}
    )

    # Test with valid settings
    test_config.settings = {"path": "/tmp/test", "mode": 0o644}
    resource = await resource_manager.register(
        "test", test_config, resource_class=resource_class
    )
    assert resource.state == ResourceState.READY

    # Test with missing setting
    test_config.settings = {"path": "/tmp/test"}
    with pytest.raises(ValueError) as exc:
        await resource_manager.register(
            "test2", test_config, resource_class=resource_class
        )
    assert "Missing required setting: mode" in str(exc.value)

    # Test with wrong type
    test_config.settings = {"path": "/tmp/test", "mode": "0644"}
    with pytest.raises(ValueError) as exc:
        await resource_manager.register(
            "test3", test_config, resource_class=resource_class
        )
    assert "Invalid type for setting mode: expected int, got str" in str(exc.value)


@pytest.mark.asyncio
async def test_resource_optional_settings(
    resource_manager: ResourceManager, test_config: ResourceConfig
):
    """Test resource with optional settings."""
    # Create resource class with optional settings
    resource_class = create_validated_resource(
        required_settings={"path": str},
        optional_settings={"mode": int, "owner": str},
    )

    # Test with only required settings
    test_config.settings = {"path": "/tmp/test"}
    resource = await resource_manager.register(
        "test", test_config, resource_class=resource_class
    )
    assert resource.state == ResourceState.READY

    # Test with optional settings
    test_config.settings = {"path": "/tmp/test", "mode": 0o644, "owner": "user"}
    resource = await resource_manager.register(
        "test2", test_config, resource_class=resource_class
    )
    assert resource.state == ResourceState.READY

    # Test with wrong type for optional setting
    test_config.settings = {"path": "/tmp/test", "mode": "0644"}
    with pytest.raises(ValueError) as exc:
        await resource_manager.register(
            "test3", test_config, resource_class=resource_class
        )
    assert "Invalid type for setting mode: expected int, got str" in str(exc.value)


@pytest.mark.asyncio
async def test_resource_metadata_validation(
    resource_manager: ResourceManager, test_config: ResourceConfig
):
    """Test resource metadata validation."""
    # Create resource class with metadata validation
    resource_class = create_validated_resource(
        required_settings={"path": str},
        optional_settings={"metadata_key": str},
    )

    # Test with valid metadata
    test_config.settings = {"path": "/tmp/test"}
    test_config.metadata = {"env": "test", "version": "1.0"}
    resource = await resource_manager.register(
        "test", test_config, resource_class=resource_class
    )
    assert resource.state == ResourceState.READY
    assert resource.metadata["initialized"] is True

    # Test with invalid metadata type
    test_config.metadata = "invalid"  # type: ignore
    with pytest.raises(ValueError) as exc:
        await resource_manager.register(
            "test2", test_config, resource_class=resource_class
        )
    assert "metadata must be a dictionary" in str(exc.value)


@pytest.mark.asyncio
async def test_resource_settings_update(
    resource_manager: ResourceManager, test_config: ResourceConfig
):
    """Test resource settings update validation."""
    # Create resource class with settings validation
    resource_class = create_validated_resource(
        required_settings={"path": str},
        optional_settings={"mode": int},
    )

    # Create resource with initial settings
    test_config.settings = {"path": "/tmp/test", "mode": 0o644}
    resource = await resource_manager.register(
        "test", test_config, resource_class=resource_class
    )
    assert resource.state == ResourceState.READY

    # Update settings with valid values
    resource.config.settings["mode"] = 0o755
    assert resource.config.settings["mode"] == 0o755

    # Update settings with invalid type
    with pytest.raises(ValueError):
        resource.config.settings["mode"] = "0755"  # type: ignore
