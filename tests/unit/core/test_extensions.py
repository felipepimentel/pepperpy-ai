"""Unit tests for the extension system."""

from typing import Optional

import pytest
from pydantic import BaseModel

from pepperpy.core.errors import ExtensionError
from pepperpy.core.extensions import Extension, ExtensionPoint


class TestExtensionConfig(BaseModel):
    """Test extension configuration."""

    name: str
    value: int


class TestExtension(Extension[TestExtensionConfig]):
    """Test extension implementation."""

    def __init__(
        self, name: str, version: str, config: Optional[TestExtensionConfig] = None
    ) -> None:
        """Initialize test extension."""
        super().__init__(name, version, config)
        self.initialized = False
        self.cleaned_up = False

    async def _initialize(self) -> None:
        """Initialize test extension."""
        self.initialized = True

    async def _cleanup(self) -> None:
        """Clean up test extension."""
        self.cleaned_up = True


@pytest.mark.asyncio
async def test_extension_lifecycle():
    """Test extension lifecycle."""
    # Create extension
    config = TestExtensionConfig(name="test", value=42)
    extension = TestExtension("test_extension", "1.0.0", config)

    # Check initial state
    assert not extension.initialized
    assert not extension.cleaned_up
    assert extension.metadata.name == "test_extension"
    assert extension.metadata.version == "1.0.0"
    assert extension.config == config

    # Initialize extension
    await extension.initialize()
    assert extension.initialized
    assert not extension.cleaned_up

    # Clean up extension
    await extension.cleanup()
    assert extension.initialized
    assert extension.cleaned_up


@pytest.mark.asyncio
async def test_extension_point():
    """Test extension point functionality."""
    # Create extension point
    extension_point = ExtensionPoint[TestExtension]("test_point", TestExtension)

    # Create extensions
    extension1 = TestExtension("extension1", "1.0.0")
    extension2 = TestExtension("extension2", "1.0.0")

    # Register extensions
    await extension_point.register_extension(extension1)
    await extension_point.register_extension(extension2)

    # Check registered extensions
    assert len(extension_point.get_extensions()) == 2
    assert extension_point.get_extension("extension1") == extension1
    assert extension_point.get_extension("extension2") == extension2

    # Try to register duplicate extension
    with pytest.raises(ExtensionError):
        await extension_point.register_extension(extension1)

    # Unregister extension
    await extension_point.unregister_extension("extension1")
    assert len(extension_point.get_extensions()) == 1
    assert extension_point.get_extension("extension1") is None
    assert extension_point.get_extension("extension2") == extension2

    # Try to unregister non-existent extension
    with pytest.raises(ExtensionError):
        await extension_point.unregister_extension("non_existent")

    # Clean up extension point
    await extension_point.cleanup()
    assert len(extension_point.get_extensions()) == 0


@pytest.mark.asyncio
async def test_extension_error_handling():
    """Test extension error handling."""

    class ErrorExtension(TestExtension):
        """Extension that raises errors."""

        async def _initialize(self) -> None:
            """Raise error during initialization."""
            raise RuntimeError("Test error")

    # Create extension point
    extension_point = ExtensionPoint[ErrorExtension]("error_point", ErrorExtension)

    # Create extension
    extension = ErrorExtension("error_extension", "1.0.0")

    # Try to register extension that fails initialization
    with pytest.raises(ExtensionError) as exc_info:
        await extension_point.register_extension(extension)
    assert "Test error" in str(exc_info.value)

    # Check that extension was not registered
    assert len(extension_point.get_extensions()) == 0
