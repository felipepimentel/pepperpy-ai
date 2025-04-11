"""Metrics validation for AI Gateway workflows."""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from .trend_analyzer import TrendAnalyzer, TrendConfig
from .validator import ValidationResult


@dataclass
class MetricsWindow:
    """Time window for metrics collection."""

    window_size: timedelta
    max_requests: int = 1000
    max_errors: int = 50
    max_latency_ms: int = 5000
    error_rate_threshold: float = 0.05  # 5%
    p95_latency_threshold_ms: int = 2000

    # Feature success thresholds
    min_daily_active_users: int = 100
    min_weekly_active_users: int = 500
    min_monthly_active_users: int = 2000
    min_retention_rate: float = 0.7  # 70%
    min_nps_score: float = 7.0
    min_csat_score: float = 4.0  # Out of 5

    # Market trend thresholds
    max_competitor_latency_ms: int = 3000
    min_market_share: float = 0.1  # 10%
    innovation_score_threshold: float = 0.8

    # Trend analysis thresholds
    trend_min_data_points: int = 30
    trend_significance: float = 0.05
    trend_forecast_days: int = 7


@dataclass
class RequestMetric:
    """Single request metric."""

    timestamp: datetime
    duration_ms: int
    status: str
    endpoint: str
    error: str | None = None
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class FeatureMetric:
    """Feature usage and success metrics."""

    feature_id: str
    timestamp: datetime
    daily_active_users: int = 0
    weekly_active_users: int = 0
    monthly_active_users: int = 0
    avg_daily_usage: float = 0.0
    retention_rate: float = 0.0
    nps_score: float = 0.0
    csat_score: float = 0.0
    details: dict[str, Any] = field(default_factory=dict)


class MetricsValidator:
    """Validates and tracks metrics for workflow operations."""

    def __init__(self, window: MetricsWindow | None = None):
        self.window = window or MetricsWindow(timedelta(minutes=5))
        self._metrics: list[RequestMetric] = []
        self._feature_metrics: dict[str, list[FeatureMetric]] = defaultdict(list)
        self._endpoints: set[str] = set()
        self._error_counts: dict[str, int] = defaultdict(int)
        self._latency_by_endpoint: dict[str, list[int]] = defaultdict(list)

        # Initialize trend analyzer
        self._trend_analyzer = TrendAnalyzer(
            TrendConfig(
                min_data_points=self.window.trend_min_data_points,
                forecast_window=timedelta(days=self.window.trend_forecast_days),
                trend_significance=self.window.trend_significance,
            )
        )

    def record_request(
        self,
        endpoint: str,
        duration_ms: int,
        status: str,
        error: str | None = None,
        **details: Any,
    ) -> None:
        """Record a new request metric."""
        metric = RequestMetric(
            timestamp=datetime.now(),
            duration_ms=duration_ms,
            status=status,
            endpoint=endpoint,
            error=error,
            details=details,
        )

        self._metrics.append(metric)
        self._endpoints.add(endpoint)

        if error:
            self._error_counts[endpoint] += 1

        self._latency_by_endpoint[endpoint].append(duration_ms)
        self._cleanup_old_metrics()

        # Record for trend analysis
        self._trend_analyzer.add_metric(
            f"latency_{endpoint}",
            duration_ms / 1000.0,  # Convert to seconds
            datetime.now(),
        )

        if error:
            self._trend_analyzer.add_metric(f"errors_{endpoint}", 1.0, datetime.now())

    def record_feature_metric(
        self,
        feature_id: str,
        daily_active_users: int = 0,
        weekly_active_users: int = 0,
        monthly_active_users: int = 0,
        avg_daily_usage: float = 0.0,
        retention_rate: float = 0.0,
        nps_score: float = 0.0,
        csat_score: float = 0.0,
        **details: Any,
    ) -> None:
        """Record feature success metrics."""
        metric = FeatureMetric(
            feature_id=feature_id,
            timestamp=datetime.now(),
            daily_active_users=daily_active_users,
            weekly_active_users=weekly_active_users,
            monthly_active_users=monthly_active_users,
            avg_daily_usage=avg_daily_usage,
            retention_rate=retention_rate,
            nps_score=nps_score,
            csat_score=csat_score,
            details=details,
        )
        self._feature_metrics[feature_id].append(metric)
        self._cleanup_old_metrics()

    def get_error_rate(self, endpoint: str | None = None) -> float:
        """Get error rate for endpoint or overall."""
        if endpoint:
            total = len([m for m in self._metrics if m.endpoint == endpoint])
            return self._error_counts[endpoint] / total if total > 0 else 0

        total = len(self._metrics)
        return sum(self._error_counts.values()) / total if total > 0 else 0

    def get_p95_latency(self, endpoint: str | None = None) -> int:
        """Get P95 latency for endpoint or overall."""
        if endpoint:
            latencies = sorted(self._latency_by_endpoint[endpoint])
        else:
            latencies = sorted(m.duration_ms for m in self._metrics)

        if not latencies:
            return 0

        idx = int(len(latencies) * 0.95)
        return latencies[idx]

    def get_request_rate(self, endpoint: str | None = None) -> float:
        """Get requests per second for endpoint or overall."""
        if not self._metrics:
            return 0.0

        window_start = datetime.now() - self.window.window_size
        if endpoint:
            count = len([
                m
                for m in self._metrics
                if m.endpoint == endpoint and m.timestamp > window_start
            ])
        else:
            count = len([m for m in self._metrics if m.timestamp > window_start])

        return count / self.window.window_size.total_seconds()

    def validate_metrics(self) -> ValidationResult:
        """Validate current metrics against thresholds."""
        result = ValidationResult()

        # Existing performance validation
        self._validate_performance_metrics(result)

        # Feature success validation
        self._validate_feature_metrics(result)

        # Market trend validation
        self._validate_market_trends(result)

        return result

    def _validate_performance_metrics(self, result: ValidationResult) -> None:
        """Validate performance metrics."""
        # Check overall metrics
        total_rate = self.get_request_rate()
        if (
            total_rate * self.window.window_size.total_seconds()
            > self.window.max_requests
        ):
            result.add_issue(
                "high_request_rate",
                f"Total request rate ({total_rate:.1f}/s) exceeds capacity",
                details={
                    "current_rate": total_rate,
                    "window_size_sec": self.window.window_size.total_seconds(),
                },
            )

        error_rate = self.get_error_rate()
        if error_rate > self.window.error_rate_threshold:
            result.add_issue(
                "high_error_rate",
                f"Overall error rate ({error_rate:.1%}) above threshold",
                details={
                    "current_rate": error_rate,
                    "threshold": self.window.error_rate_threshold,
                },
            )

        p95_latency = self.get_p95_latency()
        if p95_latency > self.window.p95_latency_threshold_ms:
            result.add_issue(
                "high_latency",
                f"P95 latency ({p95_latency}ms) above threshold",
                details={
                    "current_p95": p95_latency,
                    "threshold": self.window.p95_latency_threshold_ms,
                },
            )

        # Check per-endpoint metrics
        for endpoint in self._endpoints:
            endpoint_rate = self.get_request_rate(endpoint)
            endpoint_errors = self.get_error_rate(endpoint)
            endpoint_latency = self.get_p95_latency(endpoint)

            if endpoint_errors > self.window.error_rate_threshold:
                result.add_issue(
                    "endpoint_errors",
                    f"High error rate ({endpoint_errors:.1%}) for {endpoint}",
                    step_id=endpoint,
                    details={
                        "error_rate": endpoint_errors,
                        "threshold": self.window.error_rate_threshold,
                    },
                )

            if endpoint_latency > self.window.p95_latency_threshold_ms:
                result.add_issue(
                    "endpoint_latency",
                    f"High latency ({endpoint_latency}ms) for {endpoint}",
                    step_id=endpoint,
                    details={
                        "p95_latency": endpoint_latency,
                        "threshold": self.window.p95_latency_threshold_ms,
                    },
                )

    def _validate_feature_metrics(self, result: ValidationResult) -> None:
        """Validate feature success metrics."""
        for feature_id, metrics in self._feature_metrics.items():
            if not metrics:
                continue

            latest = metrics[-1]

            if latest.daily_active_users < self.window.min_daily_active_users:
                result.add_issue(
                    "low_daily_users",
                    f"Low daily active users ({latest.daily_active_users}) for {feature_id}",
                    step_id=feature_id,
                    details={
                        "current": latest.daily_active_users,
                        "threshold": self.window.min_daily_active_users,
                    },
                )

            if latest.retention_rate < self.window.min_retention_rate:
                result.add_issue(
                    "low_retention",
                    f"Low retention rate ({latest.retention_rate:.1%}) for {feature_id}",
                    step_id=feature_id,
                    details={
                        "current": latest.retention_rate,
                        "threshold": self.window.min_retention_rate,
                    },
                )

            if latest.nps_score < self.window.min_nps_score:
                result.add_issue(
                    "low_nps",
                    f"Low NPS score ({latest.nps_score:.1f}) for {feature_id}",
                    step_id=feature_id,
                    details={
                        "current": latest.nps_score,
                        "threshold": self.window.min_nps_score,
                    },
                )

    def _validate_market_trends(self, result: ValidationResult) -> None:
        """Validate market trend metrics."""
        # Compare with competitor benchmarks
        for endpoint in self._endpoints:
            endpoint_latency = self.get_p95_latency(endpoint)
            if endpoint_latency > self.window.max_competitor_latency_ms:
                result.add_issue(
                    "competitive_gap",
                    f"Performance gap detected for {endpoint}",
                    step_id=endpoint,
                    details={
                        "current_latency": endpoint_latency,
                        "competitor_threshold": self.window.max_competitor_latency_ms,
                    },
                )

        # Analyze trends for each endpoint
        for endpoint in self._endpoints:
            # Analyze latency trends
            latency_trend = self._trend_analyzer.predict_trend(f"latency_{endpoint}")
            if latency_trend["significant"] and latency_trend["trend"] == "up":
                result.add_issue(
                    "increasing_latency",
                    f"Increasing latency trend detected for {endpoint}",
                    step_id=endpoint,
                    details={
                        "slope": latency_trend["slope"],
                        "r_squared": latency_trend["r_squared"],
                        "forecast": latency_trend["forecast"][
                            :5
                        ],  # First 5 predictions
                    },
                )

            # Analyze error trends
            error_trend = self._trend_analyzer.predict_trend(f"errors_{endpoint}")
            if error_trend["significant"] and error_trend["trend"] == "up":
                result.add_issue(
                    "increasing_errors",
                    f"Increasing error trend detected for {endpoint}",
                    step_id=endpoint,
                    details={
                        "slope": error_trend["slope"],
                        "r_squared": error_trend["r_squared"],
                        "forecast": error_trend["forecast"][:5],
                    },
                )

            # Check for seasonality
            seasonality = self._trend_analyzer.get_seasonal_patterns(
                f"latency_{endpoint}"
            )
            if seasonality["has_seasonality"]:
                result.add_issue(
                    "seasonal_pattern",
                    f"Seasonal latency pattern detected for {endpoint}",
                    step_id=endpoint,
                    details={
                        "peak_hour": seasonality["peak_hour"],
                        "trough_hour": seasonality["trough_hour"],
                        "pattern": seasonality["hourly_pattern"],
                    },
                )

    def get_metrics_summary(self) -> dict[str, Any]:
        """Get summary of current metrics."""
        return {
            "window_size_minutes": self.window.window_size.total_seconds() / 60,
            "total_requests": len(self._metrics),
            "request_rate": self.get_request_rate(),
            "error_rate": self.get_error_rate(),
            "p95_latency": self.get_p95_latency(),
            "endpoints": {
                endpoint: {
                    "requests": len([
                        m for m in self._metrics if m.endpoint == endpoint
                    ]),
                    "errors": self._error_counts[endpoint],
                    "request_rate": self.get_request_rate(endpoint),
                    "error_rate": self.get_error_rate(endpoint),
                    "p95_latency": self.get_p95_latency(endpoint),
                }
                for endpoint in self._endpoints
            },
        }

    def get_feature_metrics_summary(self) -> dict[str, Any]:
        """Get summary of feature metrics."""
        return {
            feature_id: {
                "daily_active_users": metrics[-1].daily_active_users if metrics else 0,
                "weekly_active_users": metrics[-1].weekly_active_users
                if metrics
                else 0,
                "monthly_active_users": metrics[-1].monthly_active_users
                if metrics
                else 0,
                "retention_rate": metrics[-1].retention_rate if metrics else 0.0,
                "nps_score": metrics[-1].nps_score if metrics else 0.0,
                "csat_score": metrics[-1].csat_score if metrics else 0.0,
            }
            for feature_id, metrics in self._feature_metrics.items()
        }

    def get_trend_analysis(self) -> dict[str, Any]:
        """Get comprehensive trend analysis."""
        return {
            endpoint: {
                "latency": {
                    "trend": self._trend_analyzer.predict_trend(f"latency_{endpoint}"),
                    "seasonality": self._trend_analyzer.get_seasonal_patterns(
                        f"latency_{endpoint}"
                    ),
                    "anomalies": self._trend_analyzer.detect_anomalies(
                        f"latency_{endpoint}"
                    ),
                },
                "errors": {
                    "trend": self._trend_analyzer.predict_trend(f"errors_{endpoint}"),
                    "anomalies": self._trend_analyzer.detect_anomalies(
                        f"errors_{endpoint}"
                    ),
                },
            }
            for endpoint in self._endpoints
        }

    def _cleanup_old_metrics(self) -> None:
        """Remove metrics outside the current window."""
        cutoff = datetime.now() - self.window.window_size
        self._metrics = [m for m in self._metrics if m.timestamp > cutoff]

        # Rebuild endpoint metrics
        self._error_counts.clear()
        self._latency_by_endpoint.clear()

        for metric in self._metrics:
            if metric.error:
                self._error_counts[metric.endpoint] += 1
            self._latency_by_endpoint[metric.endpoint].append(metric.duration_ms)
