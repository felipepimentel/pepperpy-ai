"""Metrics collection implementation.

This module provides a metrics collector that implements the metrics collection 
interface of the observability system.

Example:
    >>> collector = ObservabilityMetricsCollector()
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
from typing import Dict, List, Optional, Union

from pepperpy.core.metrics.types import (
    Counter,
    Gauge,
    Histogram,
    Summary,
    MetricType,
    MetricValue,
    MetricLabels,
)

from ..errors import MetricsError
from ..types import Metric, Tags


class ObservabilityMetricsCollector:
    """Metrics collector for observability.

    This class implements metrics collection using the core metrics system.
    It provides methods for recording and retrieving metrics.

    Attributes:
        _counters: Dictionary mapping counter names to Counter instances
        _gauges: Dictionary mapping gauge names to Gauge instances
        _histograms: Dictionary mapping histogram names to Histogram instances
        _summaries: Dictionary mapping summary names to Summary instances

    Example:
        >>> collector = ObservabilityMetricsCollector()
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
        self._counters: Dict[str, Counter] = {}
        self._gauges: Dict[str, Gauge] = {}
        self._histograms: Dict[str, Histogram] = {}
        self._summaries: Dict[str, Summary] = {}

    def _get_or_create_metric(
        self,
        name: str,
        type: MetricType,
        description: Optional[str] = None,
        labels: Optional[List[str]] = None,
        buckets: Optional[List[float]] = None,
        quantiles: Optional[List[float]] = None,
    ) -> Union[Counter, Gauge, Histogram, Summary]:
        """Get or create a metric.

        Args:
            name: Name of the metric
            type: Type of metric
            description: Optional metric description
            labels: Optional label names
            buckets: Optional histogram buckets
            quantiles: Optional summary quantiles

        Returns:
            The metric instance

        Raises:
            MetricsError: If metric creation fails
        """
        try:
            if type == MetricType.COUNTER:
                if name not in self._counters:
                    self._counters[name] = Counter(name, description or "", labels)
                return self._counters[name]
            elif type == MetricType.GAUGE:
                if name not in self._gauges:
                    self._gauges[name] = Gauge(name, description or "", labels)
                return self._gauges[name]
            elif type == MetricType.HISTOGRAM:
                if name not in self._histograms:
                    self._histograms[name] = Histogram(
                        name, description or "", labels, buckets
                    )
                return self._histograms[name]
            elif type == MetricType.SUMMARY:
                if name not in self._summaries:
                    self._summaries[name] = Summary(
                        name, description or "", labels, quantiles
                    )
                return self._summaries[name]
            else:
                raise MetricsError(f"Invalid metric type: {type}")

        except Exception as e:
            raise MetricsError(f"Failed to create metric {name}: {e}")

    def record_metric(
        self,
        name: str,
        value: MetricValue,
        type: MetricType,
        tags: Optional[Tags] = None,
        description: Optional[str] = None,
        buckets: Optional[List[float]] = None,
        quantiles: Optional[List[float]] = None,
    ) -> None:
        """Record a metric measurement.

        Args:
            name: Name of the metric
            value: Metric value
            type: Type of metric
            tags: Optional tags for metric categorization
            description: Optional metric description
            buckets: Optional histogram buckets
            quantiles: Optional summary quantiles

        Raises:
            MetricsError: If recording fails
        """
        try:
            labels = list(tags.keys()) if tags else None
            metric = self._get_or_create_metric(
                name, type, description, labels, buckets, quantiles
            )

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

    def get_metrics(self) -> List[Metric]:
        """Get all recorded metrics.

        Returns:
            List of recorded metrics

        Raises:
            MetricsError: If metrics retrieval fails
        """
        try:
            metrics = []
            timestamp = time.time()

            # Collect counters
            for name, counter in self._counters.items():
                metrics.append(
                    Metric(
                        name=name,
                        value=counter.get(),
                        type=MetricType.COUNTER,
                        timestamp=timestamp,
                    )
                )

            # Collect gauges
            for name, gauge in self._gauges.items():
                metrics.append(
                    Metric(
                        name=name,
                        value=gauge.get(),
                        type=MetricType.GAUGE,
                        timestamp=timestamp,
                    )
                )

            # Collect histograms
            for name, histogram in self._histograms.items():
                metrics.append(
                    Metric(
                        name=name,
                        value=histogram.get_sum(),
                        type=MetricType.HISTOGRAM,
                        timestamp=timestamp,
                    )
                )

            # Collect summaries
            for name, summary in self._summaries.items():
                metrics.append(
                    Metric(
                        name=name,
                        value=summary.get_count(),
                        type=MetricType.SUMMARY,
                        timestamp=timestamp,
                    )
                )

            return metrics

        except Exception as e:
            raise MetricsError(f"Failed to get metrics: {e}")
