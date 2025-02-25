"""Tests for metrics module."""

import pytest

from pepperpy.core.metrics import (
    Counter,
    Gauge,
    Histogram,
    Summary,
    MetricType,
    MetricsManager,
)


def test_counter():
    """Test Counter class."""
    counter = Counter("requests", "Total requests")
    assert counter.name == "requests"
    assert counter.description == "Total requests"
    assert counter.type == MetricType.COUNTER
    assert counter.get() == 0.0

    # Test increment
    counter.inc()
    assert counter.get() == 1.0
    counter.inc(2.5)
    assert counter.get() == 3.5

    # Test with labels
    counter.inc(1.0, {"method": "GET"})
    assert counter.get({"method": "GET"}) == 1.0
    assert counter.get() == 3.5  # No labels


def test_gauge():
    """Test Gauge class."""
    gauge = Gauge("memory", "Memory usage")
    assert gauge.name == "memory"
    assert gauge.description == "Memory usage"
    assert gauge.type == MetricType.GAUGE
    assert gauge.get() == 0.0

    # Test set
    gauge.set(100.0)
    assert gauge.get() == 100.0

    # Test increment/decrement
    gauge.inc(50.0)
    assert gauge.get() == 150.0
    gauge.dec(25.0)
    assert gauge.get() == 125.0

    # Test with labels
    gauge.set(200.0, {"instance": "server1"})
    assert gauge.get({"instance": "server1"}) == 200.0
    assert gauge.get() == 125.0  # No labels


def test_histogram():
    """Test Histogram class."""
    buckets = [0.1, 0.5, 1.0]
    histogram = Histogram("latency", "Request latency", buckets=buckets)
    assert histogram.name == "latency"
    assert histogram.description == "Request latency"
    assert histogram.type == MetricType.HISTOGRAM

    # Test observations
    histogram.observe(0.75)
    buckets_data = histogram.get_buckets()
    assert buckets_data[0.1] == 0
    assert buckets_data[0.5] == 0
    assert buckets_data[1.0] == 1

    # Test with labels
    histogram.observe(0.2, {"path": "/api"})
    buckets_data = histogram.get_buckets({"path": "/api"})
    assert buckets_data[0.1] == 0
    assert buckets_data[0.5] == 1
    assert buckets_data[1.0] == 1


def test_summary():
    """Test Summary class."""
    quantiles = [0.5, 0.9, 0.99]
    summary = Summary("size", "Request size", quantiles=quantiles)
    assert summary.name == "size"
    assert summary.description == "Request size"
    assert summary.type == MetricType.SUMMARY

    # Test observations
    values = [10.0, 20.0, 30.0, 40.0, 50.0]
    for v in values:
        summary.observe(v)

    quantiles_data = summary.get_quantiles()
    assert quantiles_data[0.5] == 30.0  # Median
    assert quantiles_data[0.9] == 50.0  # 90th percentile
    assert quantiles_data[0.99] == 50.0  # 99th percentile

    # Test with labels
    summary.observe(100.0, {"method": "POST"})
    quantiles_data = summary.get_quantiles({"method": "POST"})
    assert quantiles_data[0.5] == 100.0
    assert quantiles_data[0.9] == 100.0
    assert quantiles_data[0.99] == 100.0


def test_metrics_manager():
    """Test MetricsManager class."""
    manager = MetricsManager()

    # Test counter creation
    counter = manager.counter("requests", "Total requests")
    assert isinstance(counter, Counter)
    assert counter.name == "requests"
    assert counter.description == "Total requests"
    assert counter.type == MetricType.COUNTER

    # Test gauge creation
    gauge = manager.gauge("memory", "Memory usage")
    assert isinstance(gauge, Gauge)
    assert gauge.name == "memory"
    assert gauge.description == "Memory usage"
    assert gauge.type == MetricType.GAUGE

    # Test histogram creation
    buckets = [0.1, 0.5, 1.0]
    histogram = manager.histogram("latency", "Request latency", buckets=buckets)
    assert isinstance(histogram, Histogram)
    assert histogram.name == "latency"
    assert histogram.description == "Request latency"
    assert histogram.type == MetricType.HISTOGRAM

    # Test summary creation
    quantiles = [0.5, 0.9, 0.99]
    summary = manager.summary("size", "Request size", quantiles=quantiles)
    assert isinstance(summary, Summary)
    assert summary.name == "size"
    assert summary.description == "Request size"
    assert summary.type == MetricType.SUMMARY

    # Test get_metric
    assert manager.get_metric("requests") is counter
    assert manager.get_metric("memory") is gauge
    assert manager.get_metric("latency") is histogram
    assert manager.get_metric("size") is summary

    # Test get_all_metrics
    all_metrics = manager.get_all_metrics()
    assert len(all_metrics) == 4
    assert all_metrics["requests"] is counter
    assert all_metrics["memory"] is gauge
    assert all_metrics["latency"] is histogram
    assert all_metrics["size"] is summary

    # Test non-existent metric
    with pytest.raises(KeyError):
        manager.get_metric("nonexistent")


def test_metric_type_enum():
    """Test MetricType enum."""
    assert MetricType.COUNTER == "counter"
    assert MetricType.GAUGE == "gauge"
    assert MetricType.HISTOGRAM == "histogram"
    assert MetricType.SUMMARY == "summary"
    assert len(MetricType) == 4
