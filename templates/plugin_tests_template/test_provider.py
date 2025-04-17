"""Tests for the domain provider plugin."""

import os

import pytest

from pepperpy.domain import create_provider


@pytest.mark.asyncio
async def test_initialization():
    """Test provider initialization."""
    # Create provider instance
    provider = create_provider("provider_name", option1="test_value")

    # Verify not initialized initially
    assert not provider.initialized

    # Initialize
    await provider.initialize()

    # Verify initialized
    assert provider.initialized

    # Clean up
    await provider.cleanup()

    # Verify not initialized after cleanup
    assert not provider.initialized


@pytest.mark.asyncio
async def test_process_basic():
    """Test basic processing functionality."""
    # Create provider instance with test config
    provider = create_provider("provider_name", option1="test_value")

    # Use async context manager
    async with provider:
        # Test process method
        result = await provider.process("test input")

        # Verify result
        assert result is not None
        assert isinstance(result, str)
        assert "test input" in result


@pytest.mark.asyncio
async def test_execute_tasks():
    """Test execute method with different tasks."""
    # Create provider instance
    provider = create_provider("provider_name")

    async with provider:
        # Test default task
        result = await provider.execute({"task": "process", "text": "test input"})

        # Verify success response format
        assert result["status"] == "success"
        assert "result" in result

        # Test invalid task
        result = await provider.execute({"task": "invalid_task"})

        # Verify error response format
        assert result["status"] == "error"
        assert "error" in result


@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling in the provider."""
    # Create provider instance
    provider = create_provider("provider_name")

    async with provider:
        # Test with missing parameters
        result = await provider.execute({"task": "process"})

        # Verify appropriate error response
        assert result["status"] == "error"
        assert "error" in result


@pytest.mark.asyncio
async def test_provider_direct():
    """Test provider directly (for development/debugging only)."""
    # Import directly - only for testing
    from plugins.domain.category.provider import ProviderClass

    # Create direct instance
    provider = ProviderClass(option1="test_value")

    # Initialize
    await provider.initialize()

    try:
        # Test capability access
        capabilities = provider.capabilities
        assert isinstance(capabilities, dict)

        # Test direct execution
        result = await provider.execute({"task": "process", "text": "test direct"})
        assert result["status"] == "success"
    finally:
        # Always clean up
        await provider.cleanup()


def test_provider_yaml():
    """Test plugin.yaml configuration."""
    import yaml

    # Get the plugin directory
    provider_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Read plugin.yaml
    yaml_path = os.path.join(provider_dir, "plugin.yaml")
    with open(yaml_path) as f:
        plugin_data = yaml.safe_load(f)

    # Verify required fields
    assert "name" in plugin_data
    assert "version" in plugin_data
    assert "description" in plugin_data
    assert "plugin_type" in plugin_data
    assert "category" in plugin_data
    assert "provider_name" in plugin_data
    assert "entry_point" in plugin_data

    # Verify config schema
    assert "config_schema" in plugin_data
    assert "properties" in plugin_data["config_schema"]

    # Verify examples
    assert "examples" in plugin_data
    assert len(plugin_data["examples"]) > 0

    # Verify first example format
    example = plugin_data["examples"][0]
    assert "name" in example
    assert "input" in example
    assert "expected_output" in example
