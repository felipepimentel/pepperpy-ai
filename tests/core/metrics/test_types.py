"""Tests for metrics types."""

from pepperpy.core.metrics.types import (
    MetricBase,
    MetricCounter,
    MetricGauge,
    MetricHistogram,
    MetricSummary,
    MetricType,
)


def test_metric_base():
    """Test MetricBase class."""
    metric = MetricBase("test", "Test metric", MetricType.COUNTER, None)
    assert metric.name == "test"
    assert metric.description == "Test metric"
    assert metric.type == MetricType.COUNTER
    assert metric.labels == {}


def test_metric_counter():
    """Test MetricCounter class."""
    counter = MetricCounter("requests", "Total requests", MetricType.COUNTER, None, 0)
    assert counter.name == "requests"
    assert counter.description == "Total requests"
    assert counter.type == MetricType.COUNTER
    assert counter.labels == {}
    assert counter.value == 0


def test_metric_gauge():
    """Test MetricGauge class."""
    gauge = MetricGauge("memory", "Memory usage", MetricType.GAUGE, None, 0.0)
    assert gauge.name == "memory"
    assert gauge.description == "Memory usage"
    assert gauge.type == MetricType.GAUGE
    assert gauge.labels == {}
    assert gauge.value == 0.0


def test_metric_histogram():
    """Test MetricHistogram class."""
    buckets = [0.1, 0.5, 1.0]
    histogram = MetricHistogram(
        "latency",
        "Request latency",
        MetricType.HISTOGRAM,
        None,
        buckets,
        None,
    )
    assert histogram.name == "latency"
    assert histogram.description == "Request latency"
    assert histogram.type == MetricType.HISTOGRAM
    assert histogram.labels == {}
    assert histogram.buckets == buckets
    assert histogram.values == []


def test_metric_summary():
    """Test MetricSummary class."""
    quantiles = [0.5, 0.9, 0.99]
    summary = MetricSummary(
        "size",
        "Request size",
        MetricType.SUMMARY,
        None,
        quantiles,
        None,
    )
    assert summary.name == "size"
    assert summary.description == "Request size"
    assert summary.type == MetricType.SUMMARY
    assert summary.labels == {}
    assert summary.quantiles == quantiles
    assert summary.values == []


def test_metric_with_labels():
    """Test metrics with labels."""
    labels = {"method": "GET", "path": "/api"}
    counter = MetricCounter("requests", "Total requests", MetricType.COUNTER, labels, 0)
    assert counter.labels == labels


def test_metric_type_enum():
    """Test MetricType enum."""
    assert MetricType.COUNTER == "counter"
    assert MetricType.GAUGE == "gauge"
    assert MetricType.HISTOGRAM == "histogram"
    assert MetricType.SUMMARY == "summary"
    assert len(MetricType) == 4
