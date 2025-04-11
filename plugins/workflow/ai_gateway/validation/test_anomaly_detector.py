"""Tests for anomaly detection."""

from datetime import datetime, timedelta

from .anomaly_detector import AnomalyConfig, AnomalyDetector


def test_statistical_anomalies():
    """Test detection of statistical anomalies."""
    config = AnomalyConfig(
        z_score_threshold=2.0, min_data_points=10, seasonality_window=timedelta(hours=1)
    )
    detector = AnomalyDetector(config)

    # Add normal values
    base_time = datetime.now()
    for i in range(20):
        detector.add_metric(
            "test_metric",
            value=100.0 + i,  # Slight upward trend
            timestamp=base_time + timedelta(minutes=i),
        )

    # Add an anomaly
    detector.add_metric(
        "test_metric",
        value=1000.0,  # Significant deviation
        timestamp=base_time + timedelta(minutes=21),
    )

    anomalies = detector.detect_anomalies("test_metric")
    assert len(anomalies) == 1
    assert anomalies[0].anomaly_type == "statistical"
    assert anomalies[0].current_value == 1000.0


def test_sudden_changes():
    """Test detection of sudden changes."""
    config = AnomalyConfig(
        change_threshold=0.3,  # 30% change threshold
        min_data_points=5,
        seasonality_window=timedelta(minutes=30),
    )
    detector = AnomalyDetector(config)

    # Add stable values
    base_time = datetime.now()
    for i in range(10):
        detector.add_metric(
            "test_metric", value=100.0, timestamp=base_time + timedelta(minutes=i)
        )

    # Add sudden change
    detector.add_metric(
        "test_metric",
        value=200.0,  # 100% increase
        timestamp=base_time + timedelta(minutes=11),
    )

    anomalies = detector.detect_anomalies("test_metric")
    assert len(anomalies) == 1
    assert anomalies[0].anomaly_type == "sudden_change"
    assert anomalies[0].details["change_ratio"] > 0.3


def test_seasonal_anomalies():
    """Test detection of seasonal anomalies."""
    config = AnomalyConfig(
        z_score_threshold=2.0, min_data_points=5, seasonality_window=timedelta(hours=24)
    )
    detector = AnomalyDetector(config)

    # Add normal seasonal pattern
    base_time = datetime.now().replace(minute=0, second=0, microsecond=0)
    for day in range(3):  # 3 days of data
        for hour in range(24):
            # Normal daily pattern: higher during day, lower at night
            expected_value = 100.0 + 50.0 * (1 + abs(hour - 12) / 12)
            timestamp = base_time + timedelta(days=day, hours=hour)
            detector.add_metric(
                "test_metric", value=expected_value, timestamp=timestamp
            )

    # Add seasonal anomaly
    anomaly_time = base_time + timedelta(days=3, hours=12)  # Noon on day 4
    detector.add_metric(
        "test_metric",
        value=300.0,  # Much higher than normal for this hour
        timestamp=anomaly_time,
    )

    anomalies = detector.detect_anomalies("test_metric")
    seasonal_anomalies = [a for a in anomalies if a.anomaly_type == "seasonal"]
    assert len(seasonal_anomalies) > 0
    assert seasonal_anomalies[0].details["hour"] == 12


def test_metric_predictions():
    """Test metric value predictions."""
    detector = AnomalyDetector()

    # Add data with clear trend
    base_time = datetime.now()
    for i in range(50):
        detector.add_metric(
            "test_metric",
            value=100.0 + i * 2,  # Linear increase
            timestamp=base_time + timedelta(minutes=i),
        )

    predictions = detector.predict_metrics("test_metric")
    assert len(predictions) == 30  # 30-minute forecast

    # Check prediction trend
    first_pred = predictions[0][1]
    last_pred = predictions[-1][1]
    assert last_pred > first_pred  # Should follow increasing trend


def test_confidence_calculation():
    """Test confidence calculation for predictions."""
    detector = AnomalyDetector()

    # Add stable data
    base_time = datetime.now()
    for i in range(30):
        detector.add_metric(
            "stable_metric",
            value=100.0,  # Very stable
            timestamp=base_time + timedelta(minutes=i),
        )

    # Add volatile data
    for i in range(30):
        detector.add_metric(
            "volatile_metric",
            value=100.0 + (i % 2) * 50,  # Alternating values
            timestamp=base_time + timedelta(minutes=i),
        )

    stable_predictions = detector.predict_metrics("stable_metric")
    volatile_predictions = detector.predict_metrics("volatile_metric")

    # Stable data should have higher confidence
    assert stable_predictions[0][2] > volatile_predictions[0][2]


def test_insufficient_data():
    """Test behavior with insufficient data."""
    config = AnomalyConfig(min_data_points=10)
    detector = AnomalyDetector(config)

    # Add just a few points
    base_time = datetime.now()
    for i in range(5):
        detector.add_metric(
            "test_metric", value=100.0, timestamp=base_time + timedelta(minutes=i)
        )

    # Should return empty results
    assert len(detector.detect_anomalies("test_metric")) == 0
    assert len(detector.predict_metrics("test_metric")) == 0


def test_data_cleanup():
    """Test cleanup of old data points."""
    config = AnomalyConfig(min_data_points=5, seasonality_window=timedelta(minutes=10))
    detector = AnomalyDetector(config)

    # Add old data
    old_time = datetime.now() - timedelta(minutes=20)
    for i in range(5):
        detector.add_metric(
            "test_metric", value=100.0, timestamp=old_time + timedelta(minutes=i)
        )

    # Add recent data
    recent_time = datetime.now()
    for i in range(5):
        detector.add_metric(
            "test_metric", value=100.0, timestamp=recent_time + timedelta(minutes=i)
        )

    # Get recent data
    recent_data = detector._get_recent_data("test_metric")
    assert len(recent_data) == 5  # Only recent points should remain


def test_multiple_metrics():
    """Test handling of multiple metrics."""
    detector = AnomalyDetector()

    # Add data for two metrics
    base_time = datetime.now()
    for i in range(30):
        detector.add_metric(
            "metric1", value=100.0 + i, timestamp=base_time + timedelta(minutes=i)
        )
        detector.add_metric(
            "metric2", value=200.0 - i, timestamp=base_time + timedelta(minutes=i)
        )

    # Each metric should be handled independently
    metric1_predictions = detector.predict_metrics("metric1")
    metric2_predictions = detector.predict_metrics("metric2")

    assert metric1_predictions[-1][1] > metric1_predictions[0][1]  # Increasing trend
    assert metric2_predictions[-1][1] < metric2_predictions[0][1]  # Decreasing trend
