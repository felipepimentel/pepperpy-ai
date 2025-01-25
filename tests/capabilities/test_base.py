"""Test base capability functionality."""

import pytest
from unittest.mock import AsyncMock, patch
from typing import Any, Dict

from pepperpy.capabilities.base.capability import BaseCapability


class MockCapability(BaseCapability):
    """Mock capability implementation for testing."""
    
    async def _initialize_impl(self) -> None:
        pass
        
    async def _cleanup_impl(self) -> None:
        pass
        
    def _validate_impl(self) -> None:
        pass
        
    async def execute(self, **kwargs) -> dict:
        return {"result": "test_result"}
        
    def validate_inputs(self, **kwargs) -> None:
        pass
        
    def get_metadata(self) -> dict:
        return {
            "name": "mock_capability",
            "description": "Mock capability for testing",
            "version": "1.0.0"
        }
        
    def get_dependencies(self) -> list[str]:
        return []
        
    def get_required_providers(self) -> list[str]:
        return []
        
    def get_required_capabilities(self) -> list[str]:
        return []
        
    def get_required_tools(self) -> list[str]:
        return []
        
    def get_supported_inputs(self) -> Dict[str, Any]:
        return {
            "input1": str,
            "input2": int
        }
        
    def get_supported_outputs(self) -> Dict[str, Any]:
        return {
            "result": str
        }


@pytest.fixture
def capability():
    """Create a mock capability instance."""
    return MockCapability("test_capability")


async def test_initialization(capability):
    """Test capability initialization."""
    assert not capability.is_initialized
    await capability.initialize()
    assert capability.is_initialized


async def test_cleanup(capability):
    """Test capability cleanup."""
    await capability.initialize()
    assert capability.is_initialized
    await capability.cleanup()
    assert not capability.is_initialized


def test_validation(capability):
    """Test capability validation."""
    capability.validate()  # Should not raise


def test_name_property(capability):
    """Test name property."""
    assert capability.name == "test_capability"


def test_config_property(capability):
    """Test config property."""
    assert capability.config == {}


def test_empty_name():
    """Test empty name validation."""
    with pytest.raises(ValueError):
        MockCapability("")


async def test_uninitialized_execution(capability):
    """Test execution on uninitialized capability."""
    with pytest.raises(RuntimeError):
        await capability.execute()


def test_metadata():
    """Test metadata retrieval."""
    capability = MockCapability("test_capability")
    metadata = capability.get_metadata()
    assert metadata["name"] == "mock_capability"
    assert metadata["description"] == "Mock capability for testing"
    assert metadata["version"] == "1.0.0"


async def test_registration():
    """Test capability registration."""
    @BaseCapability.register("test_capability")
    class TestCapability(BaseCapability):
        async def _initialize_impl(self) -> None:
            pass
            
        async def _cleanup_impl(self) -> None:
            pass
            
        def _validate_impl(self) -> None:
            pass
            
        async def execute(self, **kwargs) -> dict:
            return {"result": "test_result"}
            
        def validate_inputs(self, **kwargs) -> None:
            pass
            
        def get_metadata(self) -> dict:
            return {
                "name": "test_capability",
                "description": "Test capability",
                "version": "1.0.0"
            }
    
    assert BaseCapability.get_capability("test_capability") == TestCapability 