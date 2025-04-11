"""Tests for metrics and anomaly detection integration."""

from datetime import datetime, timedelta
from http import HTTPStatus

from .anomaly_detector import AnomalyConfig, AnomalyDetector
from .metrics_validator import MetricsValidator


def test_latency_anomalies():
    """Test detection of latency anomalies."""
    metrics = MetricsValidator()
    detector = AnomalyDetector(
        AnomalyConfig(
            z_score_threshold=2.0,
            min_data_points=5,
            seasonality_window=timedelta(minutes=30),
        )
    )

    base_time = datetime.now()

    # Record normal latencies
    for i in range(20):
        metrics.record_request(
            endpoint="/api/chat",
            duration_ms=500,  # 500ms
            status=str(HTTPStatus.OK.value),
            timestamp=base_time + timedelta(minutes=i),
        )
        # Feed metrics to anomaly detector
        detector.add_metric(
            "latency_/api/chat", value=0.5, timestamp=base_time + timedelta(minutes=i)
        )

    # Record anomalous latency
    metrics.record_request(
        endpoint="/api/chat",
        duration_ms=5000,  # 5s - much higher
        status=str(HTTPStatus.OK.value),
        timestamp=base_time + timedelta(minutes=21),
    )
    detector.add_metric(
        "latency_/api/chat", value=5.0, timestamp=base_time + timedelta(minutes=21)
    )

    # Check metrics validation
    validation_result = metrics.validate_metrics()
    assert not validation_result.is_valid
    assert any("latency" in issue for issue in validation_result.issues)

    # Check anomaly detection
    anomalies = detector.detect_anomalies("latency_/api/chat")
    assert len(anomalies) == 1
    assert anomalies[0].anomaly_type == "statistical"
    assert anomalies[0].current_value == 5.0


def test_error_rate_anomalies():
    """Test detection of error rate anomalies."""
    metrics = MetricsValidator()
    detector = AnomalyDetector(
        AnomalyConfig(
            z_score_threshold=2.0,
            min_data_points=5,
            seasonality_window=timedelta(minutes=30),
        )
    )

    base_time = datetime.now()

    # Record normal error rate (10%)
    for i in range(20):
        for _ in range(9):  # 9 successes
            metrics.record_request(
                endpoint="/api/chat",
                duration_ms=100,
                status=str(HTTPStatus.OK.value),
                timestamp=base_time + timedelta(minutes=i),
            )
        metrics.record_request(  # 1 error
            endpoint="/api/chat",
            duration_ms=100,
            status=str(HTTPStatus.INTERNAL_SERVER_ERROR.value),
            timestamp=base_time + timedelta(minutes=i),
        )

        error_rate = metrics.get_error_rate("/api/chat")
        detector.add_metric(
            "error_rate_/api/chat",
            value=error_rate,
            timestamp=base_time + timedelta(minutes=i),
        )

    # Record high error rate (90%)
    for _ in range(1):  # 1 success
        metrics.record_request(
            endpoint="/api/chat",
            duration_ms=100,
            status=str(HTTPStatus.OK.value),
            timestamp=base_time + timedelta(minutes=21),
        )
    for _ in range(9):  # 9 errors
        metrics.record_request(
            endpoint="/api/chat",
            duration_ms=100,
            status=str(HTTPStatus.INTERNAL_SERVER_ERROR.value),
            timestamp=base_time + timedelta(minutes=21),
        )

    error_rate = metrics.get_error_rate("/api/chat")
    detector.add_metric(
        "error_rate_/api/chat",
        value=error_rate,
        timestamp=base_time + timedelta(minutes=21),
    )

    # Check metrics validation
    validation_result = metrics.validate_metrics()
    assert not validation_result.is_valid
    assert any("error rate" in issue for issue in validation_result.issues)

    # Check anomaly detection
    anomalies = detector.detect_anomalies("error_rate_/api/chat")
    assert len(anomalies) == 1
    assert anomalies[0].anomaly_type == "statistical"
    assert anomalies[0].current_value > 0.8  # ~90% error rate


def test_request_rate_anomalies():
    """Test detection of request rate anomalies."""
    metrics = MetricsValidator()
    detector = AnomalyDetector(
        AnomalyConfig(
            z_score_threshold=2.0,
            min_data_points=5,
            seasonality_window=timedelta(hours=24),
        )
    )

    base_time = datetime.now().replace(minute=0, second=0, microsecond=0)

    # Record normal request pattern
    for hour in range(24):
        # More requests during business hours
        num_requests = 50 + 30 * (1 + abs(hour - 12) / 12)
        for _ in range(int(num_requests)):
            metrics.record_request(
                endpoint="/api/chat",
                duration_ms=100,
                status=str(HTTPStatus.OK.value),
                timestamp=base_time + timedelta(hours=hour),
            )

        request_rate = metrics.get_request_rate("/api/chat")
        detector.add_metric(
            "request_rate_/api/chat",
            value=request_rate,
            timestamp=base_time + timedelta(hours=hour),
        )

    # Record anomalous spike
    for _ in range(200):  # Much higher than normal
        metrics.record_request(
            endpoint="/api/chat",
            duration_ms=100,
            status=str(HTTPStatus.OK.value),
            timestamp=base_time + timedelta(hours=25),
        )

    request_rate = metrics.get_request_rate("/api/chat")
    detector.add_metric(
        "request_rate_/api/chat",
        value=request_rate,
        timestamp=base_time + timedelta(hours=25),
    )

    # Check metrics validation
    validation_result = metrics.validate_metrics()
    assert not validation_result.is_valid
    assert any("request rate" in issue for issue in validation_result.issues)

    # Check anomaly detection
    anomalies = detector.detect_anomalies("request_rate_/api/chat")
    assert len(anomalies) == 1
    assert anomalies[0].anomaly_type == "statistical"
    assert anomalies[0].current_value > 150  # Much higher than normal


def test_predictive_alerts():
    """Test predictive alerts based on metric trends."""
    metrics = MetricsValidator()
    detector = AnomalyDetector(
        AnomalyConfig(
            z_score_threshold=2.0,
            min_data_points=10,
            seasonality_window=timedelta(hours=1),
        )
    )

    base_time = datetime.now()

    # Record increasing latency trend
    for i in range(30):
        latency = 100 + (i * 100)  # Linear increase in ms
        metrics.record_request(
            endpoint="/api/chat",
            duration_ms=latency,
            status=str(HTTPStatus.OK.value),
            timestamp=base_time + timedelta(minutes=i),
        )
        detector.add_metric(
            "latency_/api/chat",
            value=latency / 1000,  # Convert to seconds for detector
            timestamp=base_time + timedelta(minutes=i),
        )

    # Get predictions
    predictions = detector.predict_metrics("latency_/api/chat")

    # Should predict continued increase
    assert len(predictions) > 0
    assert predictions[-1][1] > predictions[0][1]

    # Check if predicted values would trigger alerts
    future_latency = int(predictions[-1][1] * 1000)  # Convert back to ms
    metrics.record_request(
        endpoint="/api/chat",
        duration_ms=future_latency,
        status=str(HTTPStatus.OK.value),
        timestamp=base_time + timedelta(minutes=60),
    )

    validation_result = metrics.validate_metrics()
    assert not validation_result.is_valid
    assert any("latency" in issue for issue in validation_result.issues)
