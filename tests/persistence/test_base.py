"""Test base persistence functionality."""

import pytest
from unittest.mock import AsyncMock, patch

from pepperpy.persistence.base import BasePersistence, PersistenceError


class MockPersistence(BasePersistence):
    """Mock persistence implementation for testing."""
    
    async def _initialize_impl(self) -> None:
        pass
        
    async def _cleanup_impl(self) -> None:
        pass
        
    def _validate_impl(self) -> None:
        pass
        
    async def store(self, key: str, value: str) -> None:
        pass
        
    async def retrieve(self, key: str) -> str:
        return "test_value"
        
    async def delete(self, key: str) -> None:
        pass
        
    async def clear(self) -> None:
        pass
        
    async def list_keys(self) -> list[str]:
        return ["key1", "key2"]
        
    async def get_stats(self) -> dict:
        return {"total_keys": 2}


@pytest.fixture
def persistence():
    """Create a mock persistence instance."""
    return MockPersistence("test_persistence")


async def test_initialization(persistence):
    """Test persistence initialization."""
    assert not persistence.is_initialized
    await persistence.initialize()
    assert persistence.is_initialized


async def test_cleanup(persistence):
    """Test persistence cleanup."""
    await persistence.initialize()
    assert persistence.is_initialized
    await persistence.cleanup()
    assert not persistence.is_initialized


def test_validation(persistence):
    """Test persistence validation."""
    persistence.validate()  # Should not raise


def test_name_property(persistence):
    """Test name property."""
    assert persistence.name == "test_persistence"


def test_config_property(persistence):
    """Test config property."""
    assert persistence.config == {}


def test_empty_name():
    """Test empty name validation."""
    with pytest.raises(ValueError):
        MockPersistence("")


@pytest.mark.parametrize("method", [
    "store",
    "retrieve",
    "delete",
    "clear",
    "list_keys",
    "get_stats"
])
async def test_uninitialized_operations(persistence, method):
    """Test operations on uninitialized persistence."""
    with pytest.raises(PersistenceError):
        await getattr(persistence, method)("test_key")


async def test_registration():
    """Test persistence registration."""
    @BasePersistence.register("test_provider")
    class TestPersistence(BasePersistence):
        async def _initialize_impl(self) -> None:
            pass
            
        async def _cleanup_impl(self) -> None:
            pass
            
        def _validate_impl(self) -> None:
            pass
            
        async def store(self, key: str, value: str) -> None:
            pass
            
        async def retrieve(self, key: str) -> str:
            return "test_value"
            
        async def delete(self, key: str) -> None:
            pass
            
        async def clear(self) -> None:
            pass
            
        async def list_keys(self) -> list[str]:
            return ["key1", "key2"]
            
        async def get_stats(self) -> dict:
            return {"total_keys": 2}
    
    assert BasePersistence.get_persistence("test_provider") == TestPersistence 