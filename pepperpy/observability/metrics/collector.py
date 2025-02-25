"""Metrics collection implementation.

This module provides a Prometheus-based metrics collector that implements
the metrics collection interface of the observability system.

Example:
    >>> collector = PrometheusMetricsCollector()
    >>> collector.record_metric(
    ...     "requests_total",
    ...     1,
    ...     MetricType.COUNTER,
    ...     {"endpoint": "/api"}
    ... )
    >>> metrics = collector.get_metrics()
    >>> assert len(metrics) > 0
"""

import time
from typing import Any

from prometheus_client import Counter, Gauge, Histogram, Summary

from ..errors import MetricsError
from ..types import Metric, MetricType, MetricValue, Tags


class PrometheusMetricsCollector:
    """Prometheus-based metrics collector.

    This class implements metrics collection using Prometheus client library.
    It provides methods for recording and retrieving metrics.

    Attributes:
        _metrics: Dictionary mapping metric names to their Prometheus objects

    Example:
        >>> collector = PrometheusMetricsCollector()
        >>> collector.record_metric(
        ...     "requests_total",
        ...     1,
        ...     MetricType.COUNTER,
        ...     {"endpoint": "/api"}
        ... )
        >>> metrics = collector.get_metrics()
        >>> assert len(metrics) > 0
    """

    def __init__(self) -> None:
        """Initialize metrics collector."""
        self._metrics: dict[str, dict[str, Any]] = {}

    def _get_or_create_metric(
        self,
        name: str,
        type: MetricType,
        description: str | None = None,
    ) -> Any:
        """Get or create a Prometheus metric.

        Args:
            name: Name of the metric
            type: Type of metric
            description: Optional metric description

        Returns:
            The Prometheus metric object

        Raises:
            MetricsError: If metric creation fails
        """
        if name not in self._metrics:
            try:
                metric_cls = {
                    MetricType.COUNTER: Counter,
                    MetricType.GAUGE: Gauge,
                    MetricType.HISTOGRAM: Histogram,
                    MetricType.SUMMARY: Summary,
                }[type]

                metric = metric_cls(
                    name,
                    description or f"Metric {name}",
                )
                self._metrics[name] = {
                    "metric": metric,
                    "type": type,
                }
            except Exception as e:
                raise MetricsError(f"Failed to create metric {name}: {e}")

        return self._metrics[name]["metric"]

    def record_metric(
        self,
        name: str,
        value: MetricValue,
        type: MetricType,
        tags: Tags | None = None,
        description: str | None = None,
    ) -> None:
        """Record a metric measurement.

        Args:
            name: Name of the metric
            value: Metric value
            type: Type of metric
            tags: Optional tags for metric categorization
            description: Optional metric description

        Raises:
            MetricsError: If recording fails
        """
        try:
            metric = self._get_or_create_metric(name, type, description)

            if type == MetricType.COUNTER:
                metric.inc(value)
            elif type == MetricType.GAUGE:
                metric.set(value)
            elif type == MetricType.HISTOGRAM:
                metric.observe(value)
            elif type == MetricType.SUMMARY:
                metric.observe(value)

        except Exception as e:
            raise MetricsError(f"Failed to record metric {name}: {e}")

    def get_metrics(self) -> list[Metric]:
        """Get all recorded metrics.

        Returns:
            List of recorded metrics

        Raises:
            MetricsError: If metrics retrieval fails
        """
        try:
            metrics = []
            timestamp = time.time()

            for name, info in self._metrics.items():
                metric = info["metric"]
                type = info["type"]

                if type == MetricType.COUNTER:
                    value = metric._value.get()
                elif type == MetricType.GAUGE:
                    value = metric._value.get()
                elif type == MetricType.HISTOGRAM:
                    value = metric._sum.get()
                elif type == MetricType.SUMMARY:
                    value = metric._count.get()

                metrics.append(
                    Metric(
                        name=name,
                        value=value,
                        type=type,
                        timestamp=timestamp,
                    )
                )

            return metrics

        except Exception as e:
            raise MetricsError(f"Failed to get metrics: {e}")
