"""Anomaly detection for AI Gateway metrics."""

import statistics
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any


@dataclass
class AnomalyConfig:
    """Configuration for anomaly detection."""

    z_score_threshold: float = 3.0  # Number of std devs for z-score anomalies
    change_threshold: float = 0.5  # 50% change for sudden spikes
    min_data_points: int = 30  # Minimum points for statistical analysis
    seasonality_window: timedelta = timedelta(hours=24)  # For daily patterns
    forecast_window: timedelta = timedelta(minutes=30)  # Prediction window


@dataclass
class AnomalyResult:
    """Result of anomaly detection."""

    timestamp: datetime
    metric_name: str
    current_value: float
    expected_value: float
    deviation_score: float
    is_anomaly: bool
    anomaly_type: str
    details: dict[str, Any]


class AnomalyDetector:
    """Detects anomalies in metrics data."""

    def __init__(self, config: AnomalyConfig | None = None):
        self.config = config or AnomalyConfig()
        self._metric_history: dict[str, list[tuple[datetime, float]]] = defaultdict(
            list
        )
        self._seasonal_patterns: dict[str, dict[int, list[float]]] = defaultdict(
            lambda: defaultdict(list)
        )
        self._predictions: dict[str, list[tuple[datetime, float, float]]] = defaultdict(
            list
        )  # (timestamp, value, confidence)

    def add_metric(
        self, metric_name: str, value: float, timestamp: datetime | None = None
    ) -> None:
        """Add a metric data point."""
        ts = timestamp or datetime.now()
        self._metric_history[metric_name].append((ts, value))

        # Update seasonal patterns
        hour = ts.hour
        self._seasonal_patterns[metric_name][hour].append(value)

        # Cleanup old data
        self._cleanup_old_data(metric_name)

    def detect_anomalies(self, metric_name: str) -> list[AnomalyResult]:
        """Detect anomalies in a metric."""
        if not self._has_sufficient_data(metric_name):
            return []

        anomalies = []
        recent_data = self._get_recent_data(metric_name)

        # Statistical anomalies (z-score based)
        stats_anomalies = self._detect_statistical_anomalies(metric_name, recent_data)
        anomalies.extend(stats_anomalies)

        # Sudden change anomalies
        change_anomalies = self._detect_sudden_changes(metric_name, recent_data)
        anomalies.extend(change_anomalies)

        # Seasonal anomalies
        seasonal_anomalies = self._detect_seasonal_anomalies(metric_name, recent_data)
        anomalies.extend(seasonal_anomalies)

        return anomalies

    def predict_metrics(self, metric_name: str) -> list[tuple[datetime, float, float]]:
        """Predict future metric values with confidence intervals."""
        if not self._has_sufficient_data(metric_name):
            return []

        predictions = []
        current_time = datetime.now()

        # Get recent trends
        recent_values = [v for _, v in self._get_recent_data(metric_name)]
        if not recent_values:
            return []

        # Calculate trend
        trend = self._calculate_trend(recent_values)

        # Get seasonal pattern
        seasonal_pattern = self._get_seasonal_pattern(metric_name)

        # Generate predictions
        for i in range(30):  # 30-minute forecast
            future_time = current_time + timedelta(minutes=i)

            # Base prediction on trend
            base_prediction = recent_values[-1] + trend * i

            # Adjust for seasonality
            seasonal_factor = seasonal_pattern.get(future_time.hour, 1.0)
            prediction = base_prediction * seasonal_factor

            # Calculate confidence based on historical variance
            confidence = self._calculate_confidence(metric_name, prediction)

            predictions.append((future_time, prediction, confidence))

        self._predictions[metric_name] = predictions
        return predictions

    def _detect_statistical_anomalies(
        self, metric_name: str, data: list[tuple[datetime, float]]
    ) -> list[AnomalyResult]:
        """Detect anomalies using statistical methods."""
        values = [v for _, v in data]
        if not values:
            return []

        mean = statistics.mean(values)
        try:
            std_dev = statistics.stdev(values)
        except statistics.StatisticsError:
            return []

        anomalies = []

        for ts, value in data:
            if std_dev > 0:
                z_score = abs(value - mean) / std_dev
                if z_score > self.config.z_score_threshold:
                    anomalies.append(
                        AnomalyResult(
                            timestamp=ts,
                            metric_name=metric_name,
                            current_value=value,
                            expected_value=mean,
                            deviation_score=z_score,
                            is_anomaly=True,
                            anomaly_type="statistical",
                            details={
                                "z_score": z_score,
                                "mean": mean,
                                "std_dev": std_dev,
                            },
                        )
                    )

        return anomalies

    def _detect_sudden_changes(
        self, metric_name: str, data: list[tuple[datetime, float]]
    ) -> list[AnomalyResult]:
        """Detect sudden changes in metrics."""
        if len(data) < 2:
            return []

        anomalies = []

        for i in range(1, len(data)):
            prev_ts, prev_value = data[i - 1]
            curr_ts, curr_value = data[i]

            if prev_value > 0:
                change_ratio = abs(curr_value - prev_value) / prev_value
                if change_ratio > self.config.change_threshold:
                    anomalies.append(
                        AnomalyResult(
                            timestamp=curr_ts,
                            metric_name=metric_name,
                            current_value=curr_value,
                            expected_value=prev_value,
                            deviation_score=change_ratio,
                            is_anomaly=True,
                            anomaly_type="sudden_change",
                            details={
                                "change_ratio": change_ratio,
                                "previous_value": prev_value,
                            },
                        )
                    )

        return anomalies

    def _detect_seasonal_anomalies(
        self, metric_name: str, data: list[tuple[datetime, float]]
    ) -> list[AnomalyResult]:
        """Detect anomalies in seasonal patterns."""
        anomalies = []

        for ts, value in data:
            hour = ts.hour
            seasonal_values = self._seasonal_patterns[metric_name][hour]

            if len(seasonal_values) >= self.config.min_data_points:
                mean = statistics.mean(seasonal_values)
                try:
                    std_dev = statistics.stdev(seasonal_values)
                    if std_dev > 0:
                        z_score = abs(value - mean) / std_dev
                        if z_score > self.config.z_score_threshold:
                            anomalies.append(
                                AnomalyResult(
                                    timestamp=ts,
                                    metric_name=metric_name,
                                    current_value=value,
                                    expected_value=mean,
                                    deviation_score=z_score,
                                    is_anomaly=True,
                                    anomaly_type="seasonal",
                                    details={
                                        "hour": hour,
                                        "seasonal_mean": mean,
                                        "seasonal_std_dev": std_dev,
                                    },
                                )
                            )
                except statistics.StatisticsError:
                    continue

        return anomalies

    def _calculate_trend(self, values: list[float]) -> float:
        """Calculate the trend from recent values."""
        if len(values) < 2:
            return 0.0

        diffs = [values[i] - values[i - 1] for i in range(1, len(values))]
        return statistics.mean(diffs) if diffs else 0.0

    def _get_seasonal_pattern(self, metric_name: str) -> dict[int, float]:
        """Get the seasonal pattern for each hour."""
        pattern = {}

        for hour, values in self._seasonal_patterns[metric_name].items():
            if values:
                pattern[hour] = statistics.mean(values)

        return pattern

    def _calculate_confidence(self, metric_name: str, predicted_value: float) -> float:
        """Calculate confidence interval for prediction."""
        recent_values = [v for _, v in self._get_recent_data(metric_name)]
        if len(recent_values) < self.config.min_data_points:
            return 0.5  # Default 50% confidence

        try:
            std_dev = statistics.stdev(recent_values)
            mean = statistics.mean(recent_values)
            if mean > 0:
                cv = std_dev / mean  # Coefficient of variation
                # Convert CV to confidence (higher variation = lower confidence)
                confidence = max(0.1, min(0.9, 1.0 - cv))
                return confidence
        except statistics.StatisticsError:
            pass

        return 0.5

    def _has_sufficient_data(self, metric_name: str) -> bool:
        """Check if we have enough data for analysis."""
        return len(self._metric_history[metric_name]) >= self.config.min_data_points

    def _get_recent_data(self, metric_name: str) -> list[tuple[datetime, float]]:
        """Get recent data points within seasonality window."""
        cutoff = datetime.now() - self.config.seasonality_window
        return [
            (ts, val) for ts, val in self._metric_history[metric_name] if ts > cutoff
        ]

    def _cleanup_old_data(self, metric_name: str) -> None:
        """Remove data points outside the seasonality window."""
        cutoff = datetime.now() - self.config.seasonality_window
        self._metric_history[metric_name] = [
            (ts, val) for ts, val in self._metric_history[metric_name] if ts > cutoff
        ]
