"""Trend analysis for AI Gateway metrics."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import numpy as np
from scipy import stats
from sklearn.linear_model import LinearRegression


@dataclass
class TrendConfig:
    """Configuration for trend analysis."""

    min_data_points: int = 30
    forecast_window: timedelta = timedelta(days=7)
    seasonality_period: int = 24  # hours
    z_score_threshold: float = 2.0
    trend_significance: float = 0.05


class TrendAnalyzer:
    """Analyzes metric trends and predicts future values."""

    def __init__(self, config: TrendConfig | None = None):
        self.config = config or TrendConfig()
        self._metric_history: dict[str, list[tuple[datetime, float]]] = {}

    def add_metric(self, name: str, value: float, timestamp: datetime) -> None:
        """Add a metric data point."""
        if name not in self._metric_history:
            self._metric_history[name] = []
        self._metric_history[name].append((timestamp, value))

    def detect_anomalies(self, metric_name: str) -> list[dict[str, Any]]:
        """Detect anomalies in metric values."""
        if metric_name not in self._metric_history:
            return []

        values = [v for _, v in self._metric_history[metric_name]]
        if len(values) < self.config.min_data_points:
            return []

        # Calculate z-scores
        z_scores = stats.zscore(values)

        # Find anomalies
        anomalies = []
        for i, (timestamp, value) in enumerate(self._metric_history[metric_name]):
            if abs(z_scores[i]) > self.config.z_score_threshold:
                anomalies.append({
                    "timestamp": timestamp,
                    "value": value,
                    "z_score": z_scores[i],
                    "type": "high" if z_scores[i] > 0 else "low",
                })

        return anomalies

    def predict_trend(self, metric_name: str) -> dict[str, Any]:
        """Predict future trend for a metric."""
        if metric_name not in self._metric_history:
            return {"trend": "unknown", "forecast": []}

        data = self._metric_history[metric_name]
        if len(data) < self.config.min_data_points:
            return {"trend": "insufficient_data", "forecast": []}

        # Prepare data for regression
        X = np.array([(t - data[0][0]).total_seconds() for t, _ in data]).reshape(-1, 1)
        y = np.array([v for _, v in data])

        # Fit linear regression
        model = LinearRegression()
        model.fit(X, y)

        # Calculate trend significance
        slope = model.coef_[0]
        _, _, r_value, p_value, _ = stats.linregress(X.flatten(), y)
        r_squared = r_value**2

        # Generate forecast
        future_times = [
            data[-1][0] + timedelta(hours=i)
            for i in range(24)  # 24-hour forecast
        ]

        X_future = np.array([
            (t - data[0][0]).total_seconds() for t in future_times
        ]).reshape(-1, 1)

        forecast = model.predict(X_future)

        return {
            "trend": "up" if slope > 0 else "down",
            "slope": slope,
            "r_squared": r_squared,
            "p_value": p_value,
            "significant": p_value < self.config.trend_significance,
            "forecast": [
                {"timestamp": t, "value": v}
                for t, v in zip(future_times, forecast, strict=False)
            ],
        }

    def get_seasonal_patterns(self, metric_name: str) -> dict[str, Any]:
        """Detect seasonal patterns in metric."""
        if metric_name not in self._metric_history:
            return {"has_seasonality": False}

        data = self._metric_history[metric_name]
        if len(data) < self.config.seasonality_period * 2:
            return {"has_seasonality": False}

        # Group by hour of day
        hourly_values = defaultdict(list)
        for timestamp, value in data:
            hourly_values[timestamp.hour].append(value)

        # Calculate hourly averages
        hourly_averages = {
            hour: sum(values) / len(values) for hour, values in hourly_values.items()
        }

        # Detect if there's significant variation
        values = list(hourly_averages.values())
        variation = np.std(values) / np.mean(values)

        return {
            "has_seasonality": variation > 0.1,  # 10% variation threshold
            "hourly_pattern": hourly_averages,
            "peak_hour": max(hourly_averages.items(), key=lambda x: x[1])[0],
            "trough_hour": min(hourly_averages.items(), key=lambda x: x[1])[0],
        }
