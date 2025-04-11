"""Tests for trend analysis functionality."""

from datetime import datetime, timedelta

import numpy as np
import pytest

from .trend_analyzer import TrendAnalyzer, TrendConfig


@pytest.fixture
def analyzer():
    """Create trend analyzer with test configuration."""
    config = TrendConfig(
        min_data_points=10,  # Smaller for testing
        forecast_window=timedelta(hours=24),
        seasonality_period=24,
        z_score_threshold=2.0,
        trend_significance=0.05,
    )
    return TrendAnalyzer(config)


def test_anomaly_detection(analyzer):
    """Test anomaly detection with synthetic data."""
    base_time = datetime.now()

    # Generate normal distribution with outliers
    np.random.seed(42)
    normal_values = np.random.normal(100, 10, 50)
    outliers = [150, 50, 200]  # Clear outliers

    # Add normal values
    for i, value in enumerate(normal_values):
        analyzer.add_metric("test_metric", value, base_time + timedelta(minutes=i))

    # Add outliers
    for i, value in enumerate(outliers):
        analyzer.add_metric(
            "test_metric", value, base_time + timedelta(minutes=len(normal_values) + i)
        )

    anomalies = analyzer.detect_anomalies("test_metric")
    assert len(anomalies) == len(outliers)

    # Verify anomaly types
    high_anomalies = [a for a in anomalies if a["type"] == "high"]
    low_anomalies = [a for a in anomalies if a["type"] == "low"]
    assert len(high_anomalies) >= 1
    assert len(low_anomalies) >= 1


def test_trend_prediction(analyzer):
    """Test trend prediction with linear increasing data."""
    base_time = datetime.now()

    # Generate linearly increasing values
    for i in range(20):
        value = 100 + i * 10  # Clear upward trend
        analyzer.add_metric("trend_metric", value, base_time + timedelta(minutes=i))

    trend = analyzer.predict_trend("trend_metric")
    assert trend["trend"] == "up"
    assert trend["significant"]
    assert trend["slope"] > 0
    assert trend["r_squared"] > 0.9  # Strong linear fit

    # Check forecast
    assert len(trend["forecast"]) == 24  # 24-hour forecast
    first_forecast = trend["forecast"][0]["value"]
    last_forecast = trend["forecast"][-1]["value"]
    assert last_forecast > first_forecast  # Continuing upward trend


def test_seasonal_pattern_detection(analyzer):
    """Test seasonal pattern detection with synthetic daily pattern."""
    base_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    # Generate 3 days of data with clear daily pattern
    for day in range(3):
        for hour in range(24):
            # More activity during business hours (8-18)
            if 8 <= hour <= 18:
                value = 100 + np.random.normal(50, 10)
            else:
                value = 50 + np.random.normal(20, 5)

            timestamp = base_time + timedelta(days=day, hours=hour)
            analyzer.add_metric("seasonal_metric", value, timestamp)

    pattern = analyzer.get_seasonal_patterns("seasonal_metric")
    assert pattern["has_seasonality"]
    assert 8 <= pattern["peak_hour"] <= 18  # Peak during business hours
    assert pattern["peak_hour"] != pattern["trough_hour"]

    # Verify hourly pattern
    hourly_pattern = pattern["hourly_pattern"]
    assert len(hourly_pattern) == 24
    assert all(isinstance(v, (int, float)) for v in hourly_pattern.values())


def test_insufficient_data_handling(analyzer):
    """Test behavior with insufficient data points."""
    base_time = datetime.now()

    # Add fewer points than min_data_points
    for i in range(5):
        analyzer.add_metric("sparse_metric", 100 + i, base_time + timedelta(minutes=i))

    # Check each analysis type
    anomalies = analyzer.detect_anomalies("sparse_metric")
    assert len(anomalies) == 0

    trend = analyzer.predict_trend("sparse_metric")
    assert trend["trend"] == "insufficient_data"
    assert len(trend["forecast"]) == 0

    pattern = analyzer.get_seasonal_patterns("sparse_metric")
    assert not pattern["has_seasonality"]


def test_nonexistent_metric(analyzer):
    """Test behavior with nonexistent metric."""
    assert len(analyzer.detect_anomalies("nonexistent")) == 0
    assert analyzer.predict_trend("nonexistent")["trend"] == "unknown"
    assert not analyzer.get_seasonal_patterns("nonexistent")["has_seasonality"]


def test_trend_significance(analyzer):
    """Test trend significance detection with noisy data."""
    base_time = datetime.now()

    # Generate noisy data with weak trend
    np.random.seed(42)
    for i in range(20):
        # Small trend component + large noise
        value = 100 + i * 0.1 + np.random.normal(0, 10)
        analyzer.add_metric("noisy_metric", value, base_time + timedelta(minutes=i))

    trend = analyzer.predict_trend("noisy_metric")
    assert not trend["significant"]  # Trend should not be significant due to noise


def test_multiple_metrics_isolation(analyzer):
    """Test that metrics are properly isolated."""
    base_time = datetime.now()

    # Add data to two different metrics
    for i in range(20):
        analyzer.add_metric(
            "metric1",
            100 + i * 10,  # Increasing
            base_time + timedelta(minutes=i),
        )
        analyzer.add_metric(
            "metric2",
            200 - i * 5,  # Decreasing
            base_time + timedelta(minutes=i),
        )

    trend1 = analyzer.predict_trend("metric1")
    trend2 = analyzer.predict_trend("metric2")

    assert trend1["trend"] == "up"
    assert trend2["trend"] == "down"
    assert trend1["slope"] > 0
    assert trend2["slope"] < 0
