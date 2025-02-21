"""Unit tests for the layered architecture."""

import pytest
from typing import Dict, List, Type
from pydantic import BaseModel

from pepperpy.core.extensions import Extension, ExtensionPoint
from pepperpy.core.layers import (
    AgentLayer,
    CapabilityLayer,
    CoreLayer,
    Layer,
    LayerExtension,
    LayerManager,
    ProviderLayer,
    WorkflowLayer,
)


class TestConfig(BaseModel):
    """Test configuration."""

    name: str
    value: int


class TestExtension(LayerExtension[TestConfig]):
    """Test extension implementation."""

    def __init__(self, name: str, version: str, config: TestConfig) -> None:
        """Initialize test extension."""
        super().__init__(name, version, config)
        self.initialized = False
        self.cleaned_up = False

    async def get_capabilities(self) -> List[str]:
        """Get list of capabilities."""
        return ["test"]

    async def get_dependencies(self) -> List[str]:
        """Get list of dependencies."""
        return []

    async def _initialize(self) -> None:
        """Initialize extension."""
        self.initialized = True

    async def _cleanup(self) -> None:
        """Clean up extension."""
        self.cleaned_up = True


class TestLayer(Layer):
    """Test layer implementation."""

    def __init__(self) -> None:
        """Initialize test layer."""
        super().__init__("test")

    async def _get_extension_points(self) -> Dict[str, Type[Extension]]:
        """Get test layer extension points."""
        return {
            "test": TestExtension,
        }


@pytest.mark.asyncio
async def test_layer_lifecycle():
    """Test layer lifecycle."""
    # Create layer
    layer = TestLayer()

    # Check initial state
    assert not layer._initialized
    assert not layer._extension_points

    # Initialize layer
    await layer.initialize()
    assert layer._initialized
    assert len(layer._extension_points) == 1
    assert "test" in layer._extension_points

    # Clean up layer
    await layer.cleanup()
    assert not layer._initialized


@pytest.mark.asyncio
async def test_layer_extension_points():
    """Test layer extension points."""
    # Create layer
    layer = TestLayer()
    await layer.initialize()

    # Get extension point
    point = layer.get_extension_point("test")
    assert point is not None
    assert isinstance(point, ExtensionPoint)
    assert point.name == "test.test"

    # Create extension
    config = TestConfig(name="test", value=42)
    extension = TestExtension("test_ext", "1.0.0", config)

    # Register extension
    await point.register_extension(extension)
    assert len(point.get_extensions()) == 1
    assert point.get_extension("test_ext") == extension

    # Clean up
    await layer.cleanup()


@pytest.mark.asyncio
async def test_layer_manager():
    """Test layer manager."""
    # Create manager
    manager = LayerManager()

    # Check initial state
    assert not manager._initialized
    assert len(manager._layers) == 5
    assert isinstance(manager._layers["core"], CoreLayer)
    assert isinstance(manager._layers["provider"], ProviderLayer)
    assert isinstance(manager._layers["capability"], CapabilityLayer)
    assert isinstance(manager._layers["agent"], AgentLayer)
    assert isinstance(manager._layers["workflow"], WorkflowLayer)

    # Initialize manager
    await manager.initialize()
    assert manager._initialized
    assert all(layer._initialized for layer in manager._layers.values())

    # Get layer
    core_layer = manager.get_layer("core")
    assert core_layer is not None
    assert isinstance(core_layer, CoreLayer)

    # Get extension point
    metrics_point = manager.get_extension_point("core", "metrics")
    assert metrics_point is not None
    assert isinstance(metrics_point, ExtensionPoint)
    assert metrics_point.name == "core.metrics"

    # Clean up
    await manager.cleanup()
    assert not manager._initialized
    assert all(not layer._initialized for layer in manager._layers.values()) 