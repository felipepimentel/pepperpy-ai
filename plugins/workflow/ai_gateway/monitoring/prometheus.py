"""Prometheus integration for AI Gateway metrics."""

from typing import Any

from prometheus_client import Counter, Gauge, Histogram, start_http_server

# Request metrics
REQUEST_LATENCY = Histogram(
    "ai_gateway_request_latency_seconds",
    "Request latency in seconds",
    ["endpoint", "status"],
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

REQUEST_COUNT = Counter(
    "ai_gateway_requests_total",
    "Total requests processed",
    ["endpoint", "status"],
)

ERROR_COUNT = Counter(
    "ai_gateway_errors_total",
    "Total error count",
    ["endpoint", "error_type"],
)

# Feature metrics
FEATURE_USERS = Gauge(
    "ai_gateway_feature_users",
    "Feature usage statistics",
    ["feature_id", "period"],  # period: daily, weekly, monthly
)

FEATURE_RETENTION = Gauge(
    "ai_gateway_feature_retention",
    "Feature retention rate",
    ["feature_id"],
)

FEATURE_SATISFACTION = Gauge(
    "ai_gateway_feature_satisfaction",
    "Feature satisfaction scores",
    ["feature_id", "metric_type"],  # metric_type: nps, csat
)

# System metrics
SYSTEM_STATUS = Gauge(
    "ai_gateway_system_status",
    "System operational status",
    ["component"],
)


class PrometheusExporter:
    """Exports AI Gateway metrics to Prometheus."""

    def __init__(self, port: int = 9090):
        """Initialize the exporter.

        Args:
            port: Port to expose metrics on
        """
        self.port = port
        self._started = False

    def start(self) -> None:
        """Start the Prometheus metrics server."""
        if not self._started:
            start_http_server(self.port)
            self._started = True
            SYSTEM_STATUS.labels(component="prometheus").set(1)

    def record_request(
        self,
        endpoint: str,
        duration_seconds: float,
        status: str,
        error_type: str | None = None,
    ) -> None:
        """Record a request metric.

        Args:
            endpoint: API endpoint
            duration_seconds: Request duration in seconds
            status: Request status (success/error)
            error_type: Type of error if status is error
        """
        REQUEST_LATENCY.labels(endpoint=endpoint, status=status).observe(
            duration_seconds
        )
        REQUEST_COUNT.labels(endpoint=endpoint, status=status).inc()

        if error_type:
            ERROR_COUNT.labels(endpoint=endpoint, error_type=error_type).inc()

    def record_feature_metrics(
        self,
        feature_id: str,
        daily_users: int,
        weekly_users: int,
        monthly_users: int,
        retention_rate: float,
        nps_score: float | None = None,
        csat_score: float | None = None,
    ) -> None:
        """Record feature usage metrics.

        Args:
            feature_id: Feature identifier
            daily_users: Daily active users
            weekly_users: Weekly active users
            monthly_users: Monthly active users
            retention_rate: User retention rate
            nps_score: Net Promoter Score
            csat_score: Customer Satisfaction Score
        """
        FEATURE_USERS.labels(feature_id=feature_id, period="daily").set(daily_users)
        FEATURE_USERS.labels(feature_id=feature_id, period="weekly").set(weekly_users)
        FEATURE_USERS.labels(feature_id=feature_id, period="monthly").set(monthly_users)

        FEATURE_RETENTION.labels(feature_id=feature_id).set(retention_rate)

        if nps_score is not None:
            FEATURE_SATISFACTION.labels(feature_id=feature_id, metric_type="nps").set(
                nps_score
            )

        if csat_score is not None:
            FEATURE_SATISFACTION.labels(feature_id=feature_id, metric_type="csat").set(
                csat_score
            )

    def set_component_status(self, component: str, status: int) -> None:
        """Set component operational status.

        Args:
            component: Component name
            status: Status value (0=down, 1=up)
        """
        SYSTEM_STATUS.labels(component=component).set(status)

    def export_metrics_summary(self, metrics: dict[str, Any]) -> None:
        """Export metrics summary.

        Args:
            metrics: Metrics summary dictionary
        """
        # Export overall metrics
        REQUEST_LATENCY.labels(endpoint="all", status="all").observe(
            metrics["p95_latency"] / 1000.0  # Convert to seconds
        )

        # Export per-endpoint metrics
        for endpoint, endpoint_metrics in metrics["endpoints"].items():
            REQUEST_COUNT.labels(endpoint=endpoint, status="success").inc(
                endpoint_metrics["requests"] - endpoint_metrics["errors"]
            )

            REQUEST_COUNT.labels(endpoint=endpoint, status="error").inc(
                endpoint_metrics["errors"]
            )

            if endpoint_metrics["p95_latency"] > 0:
                REQUEST_LATENCY.labels(endpoint=endpoint, status="all").observe(
                    endpoint_metrics["p95_latency"] / 1000.0
                )
