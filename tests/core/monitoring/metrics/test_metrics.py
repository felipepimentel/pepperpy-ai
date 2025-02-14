"""Tests for metrics functionality."""

import pytest

from pepperpy.core.monitoring.metrics import (
    Counter,
    Gauge,
    Histogram,
    MetricsManager,
)


@pytest.mark.asyncio
async def test_counter_basic(test_counter: Counter):
    """Test basic counter functionality."""
    test_counter.inc()
    assert test_counter.value == 1
    test_counter.inc(2)
    assert test_counter.value == 3


@pytest.mark.asyncio
async def test_gauge_basic(test_gauge: Gauge):
    """Test basic gauge functionality."""
    test_gauge.set(5)
    assert test_gauge.value == 5
    test_gauge.inc(2)
    assert test_gauge.value == 7
    test_gauge.dec(3)
    assert test_gauge.value == 4


@pytest.mark.asyncio
async def test_histogram_basic(test_histogram: Histogram):
    """Test basic histogram functionality."""
    values = [0.2, 0.7, 1.5, 3.0, 4.0]
    for value in values:
        test_histogram.observe(value)

    assert test_histogram.count == 5
    assert test_histogram.sum == sum(values)


@pytest.mark.asyncio
async def test_metrics_manager(metrics_manager: MetricsManager):
    """Test metrics manager functionality."""
    # Create metrics
    counter = await metrics_manager.create_counter(
        "test_counter",
        "Test counter",
    )
    gauge = await metrics_manager.create_gauge(
        "test_gauge",
        "Test gauge",
    )
    histogram = await metrics_manager.create_histogram(
        "test_histogram",
        "Test histogram",
        buckets=[0.1, 1.0, 10.0],
    )

    # Test metric registration
    assert metrics_manager.get_metric("test_counter") is counter
    assert metrics_manager.get_metric("test_gauge") is gauge
    assert metrics_manager.get_metric("test_histogram") is histogram

    # Test metric updates
    counter.inc()
    gauge.set(5)
    histogram.observe(2.0)

    # Verify values
    assert counter.value == 1
    assert gauge.value == 5
    assert histogram.count == 1
    assert histogram.sum == 2.0


@pytest.mark.asyncio
async def test_metrics_cleanup(metrics_manager: MetricsManager):
    """Test metrics cleanup."""
    # Create some metrics
    counter1 = await metrics_manager.create_counter("counter1", "Counter 1")
    counter2 = await metrics_manager.create_counter("counter2", "Counter 2")

    # Update metrics
    counter1.inc()
    counter2.inc(2)

    # Clean up
    await metrics_manager.cleanup()

    # Create new metrics with same names
    new_counter1 = await metrics_manager.create_counter("counter1", "Counter 1")
    new_counter2 = await metrics_manager.create_counter("counter2", "Counter 2")

    # Verify they are different instances
    assert new_counter1 is not counter1
    assert new_counter2 is not counter2
    assert new_counter1.value == 0
    assert new_counter2.value == 0


@pytest.mark.asyncio
async def test_metric_validation(metrics_manager: MetricsManager):
    """Test metric validation."""
    # Test duplicate metric names
    await metrics_manager.create_counter("test", "First counter")
    with pytest.raises(ValueError):
        await metrics_manager.create_counter("test", "Second counter")

    # Test invalid histogram buckets
    with pytest.raises(ValueError):
        await metrics_manager.create_histogram(
            "invalid",
            "Invalid buckets",
            buckets=[2, 1],  # Buckets must be in ascending order
        )


@pytest.mark.asyncio
async def test_metric_labels(metrics_manager: MetricsManager):
    """Test metric labeling."""
    counter = await metrics_manager.create_counter(
        "test_counter",
        "Test counter",
        labels={"service": "test", "env": "testing"},
    )

    assert counter.labels == {"service": "test", "env": "testing"}
