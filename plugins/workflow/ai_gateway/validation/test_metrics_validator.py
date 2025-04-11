"""Tests for metrics validation."""

import time
from datetime import timedelta

from .metrics_validator import MetricsValidator, MetricsWindow


def test_request_recording():
    """Test basic request recording."""
    validator = MetricsValidator(MetricsWindow(timedelta(minutes=1)))

    # Record some requests
    validator.record_request("/chat", 100, "success")
    validator.record_request("/rag", 200, "success")
    validator.record_request("/chat", 300, "error", "API Error")

    summary = validator.get_metrics_summary()
    assert summary["total_requests"] == 3
    assert len(summary["endpoints"]) == 2
    assert summary["endpoints"]["/chat"]["requests"] == 2
    assert summary["endpoints"]["/chat"]["errors"] == 1


def test_error_rate_calculation():
    """Test error rate calculations."""
    validator = MetricsValidator(MetricsWindow(timedelta(minutes=1)))

    # Add mix of successful and failed requests
    for _ in range(8):
        validator.record_request("/test", 100, "success")
    for _ in range(2):
        validator.record_request("/test", 100, "error", "Test Error")

    assert validator.get_error_rate() == 0.2  # 20% error rate
    assert validator.get_error_rate("/test") == 0.2


def test_latency_calculation():
    """Test P95 latency calculations."""
    validator = MetricsValidator(MetricsWindow(timedelta(minutes=1)))

    # Add requests with various latencies
    latencies = [100, 150, 200, 250, 300, 350, 400, 450, 500, 1000]
    for ms in latencies:
        validator.record_request("/test", ms, "success")

    # P95 should be 1000ms (the highest value)
    assert validator.get_p95_latency() == 1000
    assert validator.get_p95_latency("/test") == 1000


def test_request_rate_calculation():
    """Test request rate calculations."""
    validator = MetricsValidator(MetricsWindow(timedelta(seconds=10)))

    # Add requests and check rate
    for _ in range(5):
        validator.record_request("/test", 100, "success")

    rate = validator.get_request_rate()
    assert 0 < rate <= 5  # Rate should be positive but not exceed total requests


def test_metrics_validation():
    """Test metrics validation against thresholds."""
    window = MetricsWindow(
        window_size=timedelta(minutes=1),
        max_requests=10,
        error_rate_threshold=0.2,
        p95_latency_threshold_ms=500,
    )
    validator = MetricsValidator(window)

    # Add requests that exceed thresholds
    for _ in range(8):
        validator.record_request("/test", 100, "success")
    for _ in range(4):
        validator.record_request("/test", 1000, "error", "Test Error")

    issues = validator.validate_metrics()
    assert len(issues) > 0

    # Check for specific issues
    issue_types = {issue["type"] for issue in issues}
    assert "high_error_rate" in issue_types
    assert "endpoint_errors" in issue_types
    assert "endpoint_latency" in issue_types


def test_metrics_cleanup():
    """Test cleanup of old metrics."""
    validator = MetricsValidator(MetricsWindow(timedelta(seconds=1)))

    # Add initial requests
    validator.record_request("/test", 100, "success")
    validator.record_request("/test", 200, "success")

    # Wait for window to pass
    time.sleep(1.1)

    # Add new request and trigger cleanup
    validator.record_request("/test", 300, "success")

    summary = validator.get_metrics_summary()
    assert summary["total_requests"] == 1  # Only the latest request should remain


def test_endpoint_metrics():
    """Test per-endpoint metrics tracking."""
    validator = MetricsValidator(MetricsWindow(timedelta(minutes=1)))

    # Add requests to different endpoints
    validator.record_request("/chat", 100, "success")
    validator.record_request("/chat", 200, "error", "Error 1")
    validator.record_request("/rag", 150, "success")
    validator.record_request("/rag", 250, "success")

    summary = validator.get_metrics_summary()

    # Check chat endpoint metrics
    chat_metrics = summary["endpoints"]["/chat"]
    assert chat_metrics["requests"] == 2
    assert chat_metrics["errors"] == 1
    assert chat_metrics["error_rate"] == 0.5

    # Check RAG endpoint metrics
    rag_metrics = summary["endpoints"]["/rag"]
    assert rag_metrics["requests"] == 2
    assert rag_metrics["errors"] == 0
    assert rag_metrics["error_rate"] == 0


def test_empty_metrics():
    """Test behavior with no metrics recorded."""
    validator = MetricsValidator()

    summary = validator.get_metrics_summary()
    assert summary["total_requests"] == 0
    assert summary["request_rate"] == 0
    assert summary["error_rate"] == 0
    assert summary["p95_latency"] == 0
    assert len(summary["endpoints"]) == 0

    issues = validator.validate_metrics()
    assert len(issues) == 0


def test_metrics_with_details():
    """Test request recording with additional details."""
    validator = MetricsValidator()

    # Record request with custom details
    validator.record_request(
        "/chat", 100, "success", None, model="gpt-4", tokens=150, user_id="test123"
    )

    # Get the recorded metric
    metrics = validator._metrics
    assert len(metrics) == 1
    assert metrics[0].details == {"model": "gpt-4", "tokens": 150, "user_id": "test123"}
