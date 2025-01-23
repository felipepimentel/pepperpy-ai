"""Tests for the lifecycle management system."""

import asyncio
import pytest
from typing import List, Set

from pepperpy.interfaces import Provider
from pepperpy.core.lifecycle import ComponentLifecycleManager

class MockProvider(Provider):
    """Mock provider for testing."""
    
    def __init__(self):
        """Initialize the mock provider."""
        self.initialized = False
        self.cleaned_up = False
        self.init_order: List[str] = []
    
    async def initialize(self) -> None:
        """Initialize the provider."""
        self.initialized = True
        self.init_order.append("initialize")
    
    async def cleanup(self) -> None:
        """Clean up the provider."""
        self.cleaned_up = True
        self.init_order.append("cleanup")

@pytest.fixture
def lifecycle_manager():
    """Create a lifecycle manager for testing."""
    return ComponentLifecycleManager()

@pytest.fixture
def mock_provider():
    """Create a mock provider for testing."""
    return MockProvider()

@pytest.mark.asyncio
async def test_single_component_lifecycle(lifecycle_manager, mock_provider):
    """Test lifecycle management of a single component."""
    # Register component
    lifecycle_manager.register("test", mock_provider)
    
    # Initialize
    await lifecycle_manager.initialize()
    assert mock_provider.initialized
    assert not mock_provider.cleaned_up
    assert lifecycle_manager.get_state() == "initialized"
    
    # Terminate
    await lifecycle_manager.terminate()
    assert mock_provider.cleaned_up
    assert lifecycle_manager.get_state() == "terminated"

@pytest.mark.asyncio
async def test_dependency_order():
    """Test components are initialized in correct dependency order."""
    manager = ComponentLifecycleManager()
    
    # Create providers
    a = MockProvider()
    b = MockProvider()
    c = MockProvider()
    
    # Register with dependencies: C -> B -> A
    manager.register("a", a)
    manager.register("b", b, dependencies=["a"])
    manager.register("c", c, dependencies=["b"])
    
    # Initialize
    await manager.initialize()
    
    # Verify order
    assert len(a.init_order) == 1
    assert len(b.init_order) == 1
    assert len(c.init_order) == 1
    
    # Verify termination order
    await manager.terminate()
    assert c.init_order[-1] == "cleanup"
    assert b.init_order[-1] == "cleanup"
    assert a.init_order[-1] == "cleanup"

@pytest.mark.asyncio
async def test_parallel_initialization():
    """Test components are initialized in parallel when possible."""
    manager = ComponentLifecycleManager()
    
    # Create independent providers
    a = MockProvider()
    b = MockProvider()
    
    # Register without dependencies
    manager.register("a", a)
    manager.register("b", b)
    
    # Initialize with delay to test parallelism
    async def delayed_init():
        await asyncio.sleep(0.1)
        await manager.initialize()
    
    # Both should initialize at the same time
    await delayed_init()
    assert a.initialized and b.initialized

@pytest.mark.asyncio
async def test_circular_dependency_detection():
    """Test circular dependency detection."""
    manager = ComponentLifecycleManager()
    
    # Create providers
    a = MockProvider()
    b = MockProvider()
    
    # Create circular dependency: A -> B -> A
    manager.register("a", a, dependencies=["b"])
    manager.register("b", b, dependencies=["a"])
    
    # Should raise ValueError
    with pytest.raises(ValueError, match="Circular dependency detected"):
        await manager.initialize()

@pytest.mark.asyncio
async def test_cleanup_on_initialization_failure():
    """Test cleanup is called when initialization fails."""
    class FailingProvider(MockProvider):
        async def initialize(self) -> None:
            self.initialized = True
            raise ValueError("Initialization failed")
    
    manager = ComponentLifecycleManager()
    provider = FailingProvider()
    
    # Register provider
    manager.register("test", provider)
    
    # Should raise ValueError and clean up
    with pytest.raises(ValueError, match="Initialization failed"):
        await manager.initialize()
    
    assert provider.cleaned_up

@pytest.mark.asyncio
async def test_multiple_initialization():
    """Test multiple initialization calls are idempotent."""
    manager = ComponentLifecycleManager()
    provider = MockProvider()
    
    # Register provider
    manager.register("test", provider)
    
    # Initialize multiple times
    await manager.initialize()
    await manager.initialize()
    await manager.initialize()
    
    # Should only initialize once
    assert len(provider.init_order) == 1

@pytest.mark.asyncio
async def test_multiple_termination():
    """Test multiple termination calls are idempotent."""
    manager = ComponentLifecycleManager()
    provider = MockProvider()
    
    # Register and initialize
    manager.register("test", provider)
    await manager.initialize()
    
    # Terminate multiple times
    await manager.terminate()
    await manager.terminate()
    await manager.terminate()
    
    # Should only clean up once
    cleanup_count = sum(1 for op in provider.init_order if op == "cleanup")
    assert cleanup_count == 1 