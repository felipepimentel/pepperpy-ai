"""Shared test fixtures and configuration.

This module provides shared fixtures and configuration for all tests.
It includes:
- Test configuration
- Common fixtures
- Helper functions
"""

import asyncio
import sys
from collections.abc import AsyncGenerator, Generator
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio

from pepperpy.core.common.metrics import MetricsManager
from pepperpy.security import SecurityContext, SecurityLevel

# Add the project root directory to the Python path
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)


# Configure pytest
def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers",
        "asyncio: mark test as requiring asyncio",
    )


# Create fixtures that can be used across tests
@pytest.fixture
def test_data_dir():
    """Return the path to the test data directory."""
    return Path(__file__).parent / "data"


@pytest.fixture
def sample_documents():
    """Return a list of sample documents for testing."""
    return [
        "This is the first test document.",
        "This is the second test document.",
        "This is the third test document.",
        "This is a different document about testing.",
        "This document is about something else entirely.",
    ]


@pytest.fixture
def sample_queries():
    """Return a list of sample queries for testing."""
    return [
        "test document",
        "different document",
        "something else",
    ]


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for tests.

    Returns:
        Event loop instance
    """
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def test_config() -> dict[str, Any]:
    """Provide test configuration.

    Returns:
        Test configuration dictionary
    """
    return {
        "test_mode": True,
        "log_level": "DEBUG",
        "encryption_key": "test_key_123",
    }


@pytest_asyncio.fixture
async def test_security_context() -> AsyncGenerator[SecurityContext, None]:
    """Provide test security context.

    Yields:
        Security context for testing
    """
    context = SecurityContext(
        level=SecurityLevel.HIGH,
        roles={"admin", "user"},
        permissions={"read", "write", "execute"},
        metadata={"test": True},
    )
    yield context


@pytest.fixture
def metrics_manager():
    """Create a new metrics manager for each test."""
    return MetricsManager()
