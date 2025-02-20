"""Core metrics module for Pepperpy.

This module provides centralized metrics collection and reporting.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Protocol, Set

from pepperpy.monitoring.metrics.base import (
    BaseMetric,
    Counter,
    Gauge,
    Histogram,
    MetricConfig,
)
from pepperpy.monitoring.metrics.types import MetricType, MetricUnit

logger = logging.getLogger(__name__)


class MetricExporter(Protocol):
    """Protocol for metric exporters."""

    async def export(self, metric: BaseMetric) -> None:
        """Export a metric.

        Args:
            metric: Metric to export
        """
        ...

    async def flush(self) -> None:
        """Flush any buffered metrics."""
        ...


class MetricsManager:
    """Manages metrics collection and reporting.

    This is a singleton class that provides a centralized way to collect
    and report metrics across the framework.
    """

    _instance: Optional["MetricsManager"] = None
    _metrics: Dict[str, BaseMetric] = {}
    _exporters: Set[MetricExporter] = set()
    _initialized: bool = False
    _lock: asyncio.Lock = asyncio.Lock()

    def __init__(self) -> None:
        """Initialize metrics manager."""
        if MetricsManager._instance is not None:
            raise RuntimeError("MetricsManager is a singleton")
        MetricsManager._instance = self

    @classmethod
    def get_instance(cls) -> "MetricsManager":
        """Get the singleton instance.

        Returns:
            MetricsManager instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def initialize(self) -> None:
        """Initialize the metrics manager."""
        async with self._lock:
            if self._initialized:
                return
            self._initialized = True
            logger.info("Metrics manager initialized")

    async def cleanup(self) -> None:
        """Clean up metrics and exporters."""
        async with self._lock:
            # Flush all exporters
            for exporter in self._exporters:
                try:
                    await exporter.flush()
                except Exception as e:
                    logger.error("Failed to flush exporter: %s", str(e))

            # Clear metrics and exporters
            self._metrics.clear()
            self._exporters.clear()
            self._initialized = False
            logger.info("Metrics manager cleaned up")

    def add_exporter(self, exporter: MetricExporter) -> None:
        """Add a metric exporter.

        Args:
            exporter: Metric exporter to add
        """
        self._exporters.add(exporter)

    async def create_counter(
        self,
        name: str,
        description: str,
        labels: Optional[Dict[str, str]] = None,
        unit: str = MetricUnit.COUNT,
    ) -> Counter:
        """Create a counter metric.

        Args:
            name: Metric name
            description: Metric description
            labels: Optional metric labels
            unit: Metric unit

        Returns:
            Counter metric
        """
        async with self._lock:
            if name in self._metrics:
                raise ValueError(f"Metric {name} already exists")

            config = MetricConfig(
                name=name,
                description=description,
                unit=unit,
                labels=labels or {},
            )
            counter = Counter(config)
            self._metrics[name] = counter
            return counter

    async def create_gauge(
        self,
        name: str,
        description: str,
        labels: Optional[Dict[str, str]] = None,
        unit: str = MetricUnit.COUNT,
    ) -> Gauge:
        """Create a gauge metric.

        Args:
            name: Metric name
            description: Metric description
            labels: Optional metric labels
            unit: Metric unit

        Returns:
            Gauge metric
        """
        async with self._lock:
            if name in self._metrics:
                raise ValueError(f"Metric {name} already exists")

            config = MetricConfig(
                name=name,
                description=description,
                unit=unit,
                labels=labels or {},
            )
            gauge = Gauge(config)
            self._metrics[name] = gauge
            return gauge

    async def create_histogram(
        self,
        name: str,
        description: str,
        buckets: List[float],
        labels: Optional[Dict[str, str]] = None,
        unit: str = MetricUnit.COUNT,
    ) -> Histogram:
        """Create a histogram metric.

        Args:
            name: Metric name
            description: Metric description
            buckets: Histogram buckets
            labels: Optional metric labels
            unit: Metric unit

        Returns:
            Histogram metric

        Raises:
            ValueError: If buckets are not in ascending order
        """
        async with self._lock:
            if name in self._metrics:
                raise ValueError(f"Metric {name} already exists")

            # Validate buckets
            if not all(buckets[i] < buckets[i + 1] for i in range(len(buckets) - 1)):
                raise ValueError("Histogram buckets must be in ascending order")

            config = MetricConfig(
                name=name,
                description=description,
                unit=unit,
                labels=labels or {},
            )
            histogram = Histogram(config, buckets)
            self._metrics[name] = histogram
            return histogram

    def get_metric(self, name: str) -> Optional[BaseMetric]:
        """Get a metric by name.

        Args:
            name: Metric name

        Returns:
            Metric if found, None otherwise
        """
        return self._metrics.get(name)

    def get_all_metrics(self) -> Dict[str, BaseMetric]:
        """Get all metrics.

        Returns:
            Dictionary of all metrics
        """
        return self._metrics.copy()


__all__ = [
    "MetricsManager",
    "MetricExporter",
    "Counter",
    "Gauge",
    "Histogram",
    "MetricType",
    "MetricUnit",
]
