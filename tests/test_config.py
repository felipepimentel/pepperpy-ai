"""Tests for configuration."""

import pytest

from tests.conftest import CapabilityConfig


def test_capability_config():
    """Test capability configuration."""
    # Test with custom values
    config = CapabilityConfig(
        name="test_capability",
        description="Test capability description",
        version="2.0.0",
        metadata={"key": "value"},
    )
    assert config.name == "test_capability"
    assert config.description == "Test capability description"
    assert config.version == "2.0.0"
    assert config.metadata == {"key": "value"}
    
    # Test with default values
    config = CapabilityConfig(
        name="test_capability",
        description="Test capability description",
    )
    assert config.name == "test_capability"
    assert config.description == "Test capability description"
    assert config.version == "1.0.0"
    assert config.metadata is None 