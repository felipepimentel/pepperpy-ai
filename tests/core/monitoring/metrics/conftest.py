"""Test fixtures for metrics testing."""

from typing import AsyncGenerator

import pytest

from pepperpy.core.monitoring.metrics import (
    Counter,
    Gauge,
    Histogram,
    MetricsManager,
)


@pytest.fixture
async def metrics_manager() -> AsyncGenerator[MetricsManager, None]:
    """Provide a metrics manager instance."""
    manager = MetricsManager()
    yield manager
    await manager.cleanup()


@pytest.fixture
async def test_counter(metrics_manager: MetricsManager) -> Counter:
    """Provide a test counter metric."""
    counter = await metrics_manager.create_counter(
        name="test_counter",
        description="Test counter metric",
    )
    return counter


@pytest.fixture
async def test_gauge(metrics_manager: MetricsManager) -> Gauge:
    """Provide a test gauge metric."""
    gauge = await metrics_manager.create_gauge(
        name="test_gauge",
        description="Test gauge metric",
    )
    return gauge


@pytest.fixture
async def test_histogram(metrics_manager: MetricsManager) -> Histogram:
    """Provide a test histogram metric."""
    histogram = await metrics_manager.create_histogram(
        name="test_histogram",
        description="Test histogram metric",
        buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10],
    )
    return histogram
