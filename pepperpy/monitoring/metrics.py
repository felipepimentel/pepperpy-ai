"""Metrics collection for the Pepperpy framework.

This module provides metrics collection functionality using:
- Counter metrics for monotonically increasing values
- Gauge metrics for values that can go up and down
- Histogram metrics for value distributions
- Summary metrics for statistical summaries
"""

import logging
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union

from pepperpy.core.enums import MetricType

__all__ = ["Metrics", "metrics"]

# Type aliases for better readability
MetricValue = Union[int, float]
MetricLabels = dict[str, str]
MetricCallback = Callable[[], MetricValue]

logger = logging.getLogger(__name__)


class Metrics:
    """Metrics collector for monitoring system behavior."""

    def __init__(self) -> None:
        """Initialize the metrics collector."""
        self._metrics: dict[str, tuple[MetricType, MetricValue]] = {}
        self._callbacks: dict[str, tuple[MetricType, MetricCallback]] = {}

    def register_callback(
        self,
        name: str,
        callback: MetricCallback,
        metric_type: MetricType,
    ) -> None:
        """Register a callback for collecting metrics.

        Args:
        ----
            name: Metric name
            callback: Function that returns the metric value
            metric_type: Type of metric to collect

        """
        self._callbacks[name] = (metric_type, callback)

    def record_metric(
        self,
        name: str,
        value: MetricValue,
        metric_type: MetricType,
        labels: MetricLabels | None = None,
    ) -> None:
        """Record a metric value.

        Args:
        ----
            name: Metric name
            value: Metric value
            metric_type: Type of metric
            labels: Optional metric labels

        """
        self._metrics[name] = (metric_type, value)

    def get_metric(self, name: str) -> tuple[MetricType, MetricValue] | None:
        """Get a metric value.

        Args:
        ----
            name: Metric name

        Returns:
        -------
            Tuple of metric type and value, or None if not found

        """
        if name in self._metrics:
            return self._metrics[name]
        if name in self._callbacks:
            metric_type, callback = self._callbacks[name]
            value = callback()
            return metric_type, value
        return None

    def clear_metric(self, name: str) -> None:
        """Clear a metric.

        Args:
        ----
            name: Metric name

        """
        self._metrics.pop(name, None)
        self._callbacks.pop(name, None)

    def clear_all(self) -> None:
        """Clear all metrics."""
        self._metrics.clear()
        self._callbacks.clear()


# Create default metrics instance
metrics = Metrics()


def parse_time_period(period: str) -> timedelta:
    """Parse a time period string into a timedelta.

    Args:
    ----
        period: Time period string (e.g., "24h", "7d", "30d")

    Returns:
    -------
        Equivalent timedelta

    Raises:
    ------
        ValueError: If period format is invalid

    """
    unit = period[-1].lower()
    try:
        value = int(period[:-1])
    except ValueError:
        raise ValueError(f"Invalid period format: {period}")

    if unit == "h":
        return timedelta(hours=value)
    elif unit == "d":
        return timedelta(days=value)
    elif unit == "w":
        return timedelta(weeks=value)
    else:
        raise ValueError(f"Invalid time unit: {unit}")


def get_search_stats(
    index_name: Optional[str] = None, period: str = "24h"
) -> Dict[str, Any]:
    """Get search usage statistics.

    Args:
    ----
        index_name: Optional index to filter stats for
        period: Time period to get stats for (e.g., "24h", "7d", "30d")

    Returns:
    -------
        Dict containing search statistics

    """
    try:
        time_period = parse_time_period(period)
        start_time = datetime.now() - time_period

        # TODO: Implement actual metrics collection
        stats = {
            "queries": {"total": 1000, "avg_latency": 50.5, "cache_hit_rate": 85.5},
            "indexing": {
                "docs_indexed": 5000,
                "index_size": 1024 * 1024 * 10,
                "avg_index_time": 25.5,
            },
            "errors": {"query_errors": 10, "index_errors": 5, "validation_errors": 2},
        }

        logger.info(
            "Retrieved search stats",
            extra={
                "index": index_name,
                "period": period,
                "start_time": start_time.isoformat(),
            },
        )

        return stats

    except Exception as e:
        logger.error(
            "Failed to get search stats",
            extra={"error": str(e), "index": index_name, "period": period},
        )
        raise
