"""Tests for lifecycle management functionality."""

import pytest
from datetime import datetime

from pepperpy.core.lifecycle.manager import PepperpyLifecycleManager
from pepperpy.core.lifecycle.initializer import InitializationError
from pepperpy.core.lifecycle.terminator import TerminationError

@pytest.fixture
def lifecycle_manager():
    """Create a lifecycle manager instance."""
    return PepperpyLifecycleManager()

@pytest.mark.asyncio
async def test_initialization(lifecycle_manager):
    """Test component initialization."""
    # Initial state
    assert lifecycle_manager.get_state() == "uninitialized"
    
    # Initialize
    await lifecycle_manager.initialize()
    assert lifecycle_manager.get_state() == "initialized"
    
    # Check metadata
    metadata = lifecycle_manager.get_metadata()
    assert "created_at" in metadata
    assert "initialized_at" in metadata
    assert "error" not in metadata
    
    # Check initialization steps
    init_steps = lifecycle_manager.get_init_steps()
    assert init_steps["state"] == "initialized"
    assert len(init_steps["steps"]) >= 2  # start and complete steps
    assert init_steps["steps"][0]["step"] == "start"
    assert init_steps["steps"][-1]["step"] == "complete"
    assert init_steps["steps"][-1]["success"] is True

@pytest.mark.asyncio
async def test_double_initialization(lifecycle_manager):
    """Test that double initialization is handled gracefully."""
    await lifecycle_manager.initialize()
    await lifecycle_manager.initialize()  # Should log warning but not fail
    assert lifecycle_manager.get_state() == "initialized"

@pytest.mark.asyncio
async def test_termination(lifecycle_manager):
    """Test component termination."""
    # Initialize first
    await lifecycle_manager.initialize()
    assert lifecycle_manager.get_state() == "initialized"
    
    # Terminate
    await lifecycle_manager.terminate()
    assert lifecycle_manager.get_state() == "terminated"
    
    # Check metadata
    metadata = lifecycle_manager.get_metadata()
    assert "created_at" in metadata
    assert "initialized_at" in metadata
    assert "terminated_at" in metadata
    assert "error" not in metadata
    
    # Check termination steps
    term_steps = lifecycle_manager.get_term_steps()
    assert term_steps["state"] == "terminated"
    assert len(term_steps["steps"]) >= 2  # start and complete steps
    assert term_steps["steps"][0]["step"] == "start"
    assert term_steps["steps"][-1]["step"] == "complete"
    assert term_steps["steps"][-1]["success"] is True

@pytest.mark.asyncio
async def test_termination_without_initialization(lifecycle_manager):
    """Test that termination without initialization is handled gracefully."""
    await lifecycle_manager.terminate()  # Should log warning but not fail
    assert lifecycle_manager.get_state() == "uninitialized"

@pytest.mark.asyncio
async def test_double_termination(lifecycle_manager):
    """Test that double termination is handled gracefully."""
    await lifecycle_manager.initialize()
    await lifecycle_manager.terminate()
    await lifecycle_manager.terminate()  # Should log warning but not fail
    assert lifecycle_manager.get_state() == "terminated"

@pytest.mark.asyncio
async def test_metadata_timestamps(lifecycle_manager):
    """Test that metadata timestamps are properly set."""
    # Get initial timestamp
    created_at = datetime.fromisoformat(lifecycle_manager.get_metadata()["created_at"])
    
    # Initialize
    await lifecycle_manager.initialize()
    initialized_at = datetime.fromisoformat(
        lifecycle_manager.get_metadata()["initialized_at"]
    )
    assert initialized_at >= created_at
    
    # Terminate
    await lifecycle_manager.terminate()
    terminated_at = datetime.fromisoformat(
        lifecycle_manager.get_metadata()["terminated_at"]
    )
    assert terminated_at >= initialized_at 