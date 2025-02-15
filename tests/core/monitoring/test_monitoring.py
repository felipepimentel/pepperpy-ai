"""Tests for the monitoring system."""

import logging
from typing import Dict

import pytest
import structlog
from structlog.testing import LogCapture

from pepperpy.core.monitoring.logging import (
    LoggerManager,
    get_logger,
    setup_logging,
)
from pepperpy.core.monitoring.metrics import (
    Metric,
    MetricExporter,
    MetricType,
    metrics_manager,
    record_metric,
)
from pepperpy.core.monitoring.tracing import (
    SpanKind,
    trace_span,
    tracing_manager,
)


class TestMetricExporter(MetricExporter):
    """Test implementation of a metric exporter."""

    def __init__(self) -> None:
        self.exported_metrics: Dict[str, Metric] = {}
        self.flush_called = False

    async def export(self, metric: Metric) -> None:
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
async def test_logger_manager():
    """Test logger manager functionality."""
    manager = LoggerManager()
    await manager.initialize()

    # Test getting logger
    logger = manager.get_logger("test")
    assert logger is not None

    # Test context binding
    context_logger = manager.get_logger("test", {"key": "value"})
    assert context_logger is not None

    # Test global context
    manager.add_global_context(env="test")
    new_logger = manager.get_logger("test2")
    assert new_logger is not None

    # Test cleanup
    await manager.cleanup()


@pytest.mark.asyncio
async def test_logging_output(log_capture: LogCapture):
    """Test logging output capture."""
    logger = get_logger("test")
    logger.info("Test message", key="value")

    # Verify log output
    assert len(log_capture.entries) > 0
    entry = log_capture.entries[0]
    assert entry["event"] == "Test message"
    assert entry["key"] == "value"
    assert entry["logger"] == "test"


@pytest.mark.asyncio
async def test_metrics_manager():
    """Test metrics manager functionality."""
    await metrics_manager.initialize()

    # Add test exporter
    exporter = TestMetricExporter()
    metrics_manager.add_exporter(exporter)

    # Record metric
    await metrics_manager.record(
        "test_counter",
        1.0,
        MetricType.COUNTER,
        {"label": "test"},
        "Test metric",
    )

    # Verify metric was recorded and exported
    metric = metrics_manager.get_metric("test_counter")
    assert metric is not None
    assert metric.value == 1.0
    assert metric.type == MetricType.COUNTER
    assert metric.labels == {"label": "test"}
    assert metric.description == "Test metric"

    # Verify export
    assert "test_counter" in exporter.exported_metrics
    exported = exporter.exported_metrics["test_counter"]
    assert exported.value == 1.0

    # Test cleanup
    await metrics_manager.cleanup()
    assert exporter.flush_called


@pytest.mark.asyncio
async def test_metrics_convenience_function():
    """Test metrics convenience function."""
    exporter = TestMetricExporter()
    metrics_manager.add_exporter(exporter)

    await record_metric(
        "test_gauge",
        42.0,
        MetricType.GAUGE,
        {"service": "test"},
    )

    assert "test_gauge" in exporter.exported_metrics
    metric = exporter.exported_metrics["test_gauge"]
    assert metric.value == 42.0
    assert metric.type == MetricType.GAUGE
    assert metric.labels == {"service": "test"}


@pytest.mark.asyncio
async def test_tracing_manager():
    """Test tracing manager functionality."""
    await tracing_manager.initialize()

    # Test span creation
    async with tracing_manager.span(
        "test_operation",
        kind=SpanKind.INTERNAL,
        attributes={"service": "test"},
    ) as span:
        assert span is not None
        span.set_attribute("key", "value")

    # Test context injection/extraction
    carrier: Dict[str, str] = {}
    tracing_manager.inject_context(carrier)
    assert carrier  # Context should be injected

    context = tracing_manager.extract_context(carrier)
    assert context is not None

    await tracing_manager.cleanup()


@pytest.mark.asyncio
async def test_tracing_convenience_function():
    """Test tracing convenience function."""
    async with trace_span(
        "test_span",
        attributes={"test": "value"},
    ) as span:
        assert span is not None
        span.set_attribute("key", "value")


@pytest.mark.asyncio
async def test_tracing_error_handling():
    """Test tracing error handling."""
    with pytest.raises(ValueError):
        async with tracing_manager.span("error_span") as span:
            assert span is not None
            raise ValueError("Test error")


@pytest.mark.asyncio
async def test_logging_setup():
    """Test logging setup function."""
    # Test default setup
    setup_logging()
    root_logger = logging.getLogger()
    assert root_logger.level == logging.INFO

    # Test custom level
    setup_logging(level="DEBUG")
    assert root_logger.level == logging.DEBUG

    # Test JSON formatting
    setup_logging(enable_json=True)
    # JSON formatter should be configured
