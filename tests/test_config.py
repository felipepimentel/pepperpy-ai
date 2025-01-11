"""Tests for configuration."""

import pytest

from pepperpy_ai.capabilities.base import CapabilityConfig


def test_capability_config():
    """Test capability configuration."""
    # Test with custom values
    config = CapabilityConfig(
        name="test_capability",
        description="Test capability description",
    )
    assert config.name == "test_capability"
    assert config.description == "Test capability description"
    
    # Test with metadata
    config = CapabilityConfig(
        name="test_capability",
        description="Test capability description",
        metadata={"key": "value"},
    )
    assert config.name == "test_capability"
    assert config.description == "Test capability description"
    assert config.metadata == {"key": "value"} 