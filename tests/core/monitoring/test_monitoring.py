"""Tests for the monitoring system."""

import logging

import pytest
import structlog
from structlog.testing import LogCapture

from pepperpy.monitoring import configure_logging
from pepperpy.monitoring.metrics import (
    BaseMetric,
    MetricExporter,
    MetricsManager,
    MetricUnit,
)


class TestMetricExporter(MetricExporter):
    """Test implementation of a metric exporter."""

    def __init__(self) -> None:
        self.exported_metrics: dict[str, BaseMetric] = {}
        self.flush_called = False

    async def export(self, metric: BaseMetric) -> None:
        """Export a test metric."""
        self.exported_metrics[metric.name] = metric

    async def flush(self) -> None:
        """Flush test metrics."""
        self.flush_called = True


@pytest.fixture
def log_capture() -> LogCapture:
    """Fixture for capturing log output."""
    log_capture = LogCapture()
    structlog.configure(processors=[log_capture])
    return log_capture


@pytest.mark.asyncio
async def test_logging_output(log_capture: LogCapture):
    """Test logging output capture."""
    logger = logging.getLogger("test")
    logger.info("Test message", extra={"key": "value"})

    # Verify log output
    assert len(log_capture.entries) > 0
    entry = log_capture.entries[0]
    assert entry["event"] == "Test message"
    assert entry["key"] == "value"
    assert entry["logger"] == "test"


@pytest.mark.asyncio
async def test_metrics_manager():
    """Test metrics manager functionality."""
    metrics = MetricsManager.get_instance()
    await metrics.initialize()

    # Add test exporter
    exporter = TestMetricExporter()
    metrics.add_exporter(exporter)

    # Create and record metrics
    counter = await metrics.create_counter(
        "test_counter",
        "Test counter",
        labels={"label": "test"},
    )
    counter.record(1.0)

    # Verify metric was recorded
    assert counter.get_points()[-1].value == 1.0
    assert counter.get_points()[-1].labels == {"label": "test"}

    # Create and record gauge
    gauge = await metrics.create_gauge(
        "test_gauge",
        "Test gauge",
        unit=MetricUnit.PERCENT,
    )
    gauge.record(42.0)

    # Verify gauge was recorded
    assert gauge.get_points()[-1].value == 42.0
    assert gauge.unit == MetricUnit.PERCENT

    # Create and record histogram
    histogram = await metrics.create_histogram(
        "test_histogram",
        "Test histogram",
        buckets=[0.1, 1.0, 10.0],
    )
    histogram.record(2.0)

    # Verify histogram was recorded
    assert histogram.count == 1
    assert histogram.sum == 2.0
    assert histogram.buckets == [0.1, 1.0, 10.0]

    # Test cleanup
    await metrics.cleanup()
    assert exporter.flush_called


@pytest.mark.asyncio
async def test_logging_setup():
    """Test logging setup function."""
    # Test default setup
    configure_logging()
    root_logger = logging.getLogger()
    assert root_logger.level == logging.INFO

    # Test custom level
    configure_logging(level="DEBUG")
    assert root_logger.level == logging.DEBUG

    # Test file logging
    import os
    import tempfile

    with tempfile.NamedTemporaryFile(delete=False) as f:
        log_file = f.name
        configure_logging(log_file=log_file)
        root_logger.info("Test log message")

        # Verify log file was written
        with open(log_file) as f:
            log_content = f.read()
            assert "Test log message" in log_content

        # Clean up
        os.unlink(log_file)
