"""Metrics collection for the Pepperpy framework.

This module provides metrics collection functionality using a protocol-based
approach, supporting various metric types and collection methods.
"""

from datetime import datetime
from typing import Any

from pepperpy.core.protocols import MetricsCollector, MetricType, MetricValue


class DefaultMetricsCollector(MetricsCollector):
    """Default implementation of metrics collector."""

    def __init__(self) -> None:
        """Initialize the metrics collector."""
        self._metrics: dict[str, MetricValue] = {}

    def record_metric(
        self,
        name: str,
        value: float,
        type: MetricType,
        labels: dict[str, str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> MetricValue:
        """Record a metric.

        Args:
            name: Metric name
            value: Metric value
            type: Metric type
            labels: Optional metric labels
            metadata: Optional metric metadata

        Returns:
            Recorded metric value

        Raises:
            ValueError: If metric name or value is invalid
        """
        if not name:
            raise ValueError("Metric name cannot be empty")

        metric = MetricValue(
            name=name,
            type=type,
            value=value,
            timestamp=datetime.utcnow(),
            labels=labels or {},
            metadata=metadata or {},
        )
        self._metrics[name] = metric
        return metric

    def get_metric(
        self,
        name: str,
        labels: dict[str, str] | None = None,
    ) -> MetricValue | None:
        """Get a metric value.

        Args:
            name: Metric name
            labels: Optional metric labels

        Returns:
            Metric value if found, None otherwise
        """
        metric = self._metrics.get(name)
        if not metric:
            return None

        if labels and metric.labels != labels:
            return None

        return metric

    def list_metrics(
        self,
        pattern: str | None = None,
        type: MetricType | None = None,
        labels: dict[str, str] | None = None,
    ) -> list[MetricValue]:
        """List metrics.

        Args:
            pattern: Optional name pattern filter
            type: Optional type filter
            labels: Optional metric labels

        Returns:
            List of matching metrics
        """
        metrics = []
        for metric in self._metrics.values():
            if pattern and pattern not in metric.name:
                continue
            if type and metric.type != type:
                continue
            if labels and metric.labels != labels:
                continue
            metrics.append(metric)
        return metrics

    def clear_metrics(
        self,
        pattern: str | None = None,
        type: MetricType | None = None,
        labels: dict[str, str] | None = None,
    ) -> int:
        """Clear metrics.

        Args:
            pattern: Optional name pattern filter
            type: Optional type filter
            labels: Optional metric labels

        Returns:
            Number of metrics cleared
        """
        to_remove = []
        for name, metric in self._metrics.items():
            if pattern and pattern not in name:
                continue
            if type and metric.type != type:
                continue
            if labels and metric.labels != labels:
                continue
            to_remove.append(name)

        for name in to_remove:
            del self._metrics[name]

        return len(to_remove)

    async def export_metrics(
        self,
        format: str = "prometheus",
        pattern: str | None = None,
    ) -> str:
        """Export metrics in specified format.

        Args:
            format: Output format (prometheus, json, etc.)
            pattern: Optional name pattern filter

        Returns:
            Formatted metrics string
        """
        metrics = self.list_metrics(pattern=pattern)
        if format == "prometheus":
            return self._format_prometheus(metrics)
        return self._format_json(metrics)

    def _format_prometheus(self, metrics: list[MetricValue]) -> str:
        """Format metrics in Prometheus format."""
        lines = []
        for metric in metrics:
            labels_str = ",".join(f'{k}="{v}"' for k, v in metric.labels.items())
            if labels_str:
                labels_str = f"{{{labels_str}}}"
            lines.append(
                f"{metric.name}{labels_str} {metric.value} "
                f"{int(metric.timestamp.timestamp() * 1000)}"
            )
        return "\n".join(lines)

    def _format_json(self, metrics: list[MetricValue]) -> str:
        """Format metrics in JSON format."""
        import json

        return json.dumps([metric.dict() for metric in metrics])

    def counter(
        self,
        name: str,
        value: float = 1.0,
        labels: dict[str, str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> MetricValue:
        """Record a counter metric.

        Args:
            name: Metric name
            value: Value to add to counter
            labels: Optional metric labels
            metadata: Optional metric metadata

        Returns:
            Recorded metric value
        """
        return self.record_metric(
            name,
            value,
            MetricType.COUNTER,
            labels,
            metadata,
        )

    def gauge(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> MetricValue:
        """Record a gauge metric.

        Args:
            name: Metric name
            value: Current value
            labels: Optional metric labels
            metadata: Optional metric metadata

        Returns:
            Recorded metric value
        """
        return self.record_metric(
            name,
            value,
            MetricType.GAUGE,
            labels,
            metadata,
        )

    def histogram(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> MetricValue:
        """Record a histogram metric.

        Args:
            name: Metric name
            value: Value to add to histogram
            labels: Optional metric labels
            metadata: Optional metric metadata

        Returns:
            Recorded metric value
        """
        return self.record_metric(
            name,
            value,
            MetricType.HISTOGRAM,
            labels,
            metadata,
        )

    def summary(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> MetricValue:
        """Record a summary metric.

        Args:
            name: Metric name
            value: Value to add to summary
            labels: Optional metric labels
            metadata: Optional metric metadata

        Returns:
            Recorded metric value
        """
        return self.record_metric(
            name,
            value,
            MetricType.SUMMARY,
            labels,
            metadata,
        )

    def timer(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> MetricValue:
        """Record a timer metric.

        Args:
            name: Metric name
            value: Duration in seconds
            labels: Optional metric labels
            metadata: Optional metric metadata

        Returns:
            Recorded metric value
        """
        return self.record_metric(
            name,
            value,
            MetricType.TIMER,
            labels,
            metadata,
        )


# Create default metrics collector instance
metrics = DefaultMetricsCollector()
