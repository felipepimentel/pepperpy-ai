"""Shared test fixtures and configuration.

This module provides shared fixtures and configuration for all tests.
It includes:
- Test configuration
- Common fixtures
- Helper functions
"""

import asyncio
from collections.abc import AsyncGenerator, Generator
from typing import Any

import pytest
import pytest_asyncio

from pepperpy.core.metrics import MetricsManager
from pepperpy.security import SecurityContext, SecurityLevel


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
