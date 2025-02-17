"""Manager for collecting and exporting metrics."""

import asyncio
from typing import Dict, List, Optional, Protocol, Set

from pepperpy.core.lifecycle import Lifecycle

from .types import Counter, Gauge, Histogram, Metric, MetricType


class MetricExporter(Protocol):
    """Protocol for metric exporters."""

    async def export(self, metrics: List[Metric]) -> None:
        """Export metrics.

        Args:
            metrics: List of metrics to export

        """
        ...


class MetricsManager(Lifecycle):
    """Central manager for metrics.

    This class manages metric collection and export.
    It supports multiple metric types and exporters.

    Attributes:
        metrics: Current metrics
        exporters: Registered metric exporters

    """

    def __init__(self) -> None:
        """Initialize the manager."""
        super().__init__()
        self._metrics: Dict[str, Metric] = {}
        self._exporters: Set[MetricExporter] = set()
        self._lock = asyncio.Lock()
        self._export_task: Optional[asyncio.Task] = None
        self._export_interval = 10.0  # seconds

    def add_exporter(self, exporter: MetricExporter) -> None:
        """Add a metric exporter.

        Args:
            exporter: Exporter to add

        """
        self._exporters.add(exporter)

    def remove_exporter(self, exporter: MetricExporter) -> None:
        """Remove a metric exporter.

        Args:
            exporter: Exporter to remove

        """
        self._exporters.discard(exporter)

    async def record_counter(
        self,
        name: str,
        value: float = 1.0,
        *,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """Record a counter metric.

        Args:
            name: Metric name
            value: Value to add (defaults to 1.0)
            labels: Optional metric labels

        """
        async with self._lock:
            if name not in self._metrics:
                self._metrics[name] = Counter(
                    name=name,
                    type=MetricType.COUNTER,
                    description=f"Counter metric {name}",
                    labels=labels or {},
                )
            metric = self._metrics[name]
            if isinstance(metric, Counter):
                metric.inc(value)

    async def record_gauge(
        self,
        name: str,
        value: float,
        *,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """Record a gauge metric.

        Args:
            name: Metric name
            value: Current value
            labels: Optional metric labels

        """
        async with self._lock:
            if name not in self._metrics:
                self._metrics[name] = Gauge(
                    name=name,
                    type=MetricType.GAUGE,
                    description=f"Gauge metric {name}",
                    labels=labels or {},
                )
            metric = self._metrics[name]
            if isinstance(metric, Gauge):
                metric.set(value)

    async def record_histogram(
        self,
        name: str,
        value: float,
        *,
        labels: Optional[Dict[str, str]] = None,
        buckets: Optional[List[float]] = None,
    ) -> None:
        """Record a histogram metric.

        Args:
            name: Metric name
            value: Value to observe
            labels: Optional metric labels
            buckets: Optional histogram buckets

        """
        async with self._lock:
            if name not in self._metrics:
                self._metrics[name] = Histogram(
                    name=name,
                    type=MetricType.HISTOGRAM,
                    description=f"Histogram metric {name}",
                    labels=labels or {},
                    buckets=buckets or [],
                )
            metric = self._metrics[name]
            if isinstance(metric, Histogram):
                metric.observe(value)

    async def _export_metrics(self) -> None:
        """Export metrics to all registered exporters."""
        try:
            async with self._lock:
                metrics = list(self._metrics.values())

            for exporter in self._exporters:
                try:
                    await exporter.export(metrics)
                except Exception as e:
                    # Log error but continue with other exporters
                    print(f"Error exporting metrics: {e}")
        except Exception as e:
            # Log error but continue running
            print(f"Error in metric export: {e}")

    async def _export_loop(self) -> None:
        """Run the metric export loop."""
        while True:
            try:
                await self._export_metrics()
                await asyncio.sleep(self._export_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                # Log error but continue running
                print(f"Error in export loop: {e}")
                await asyncio.sleep(1.0)  # Back off on error

    async def initialize(self) -> None:
        """Initialize the manager.

        This starts the metric export loop.
        """
        self._export_task = asyncio.create_task(self._export_loop())

    async def cleanup(self) -> None:
        """Clean up the manager.

        This stops the metric export loop and clears all metrics.
        """
        if self._export_task:
            self._export_task.cancel()
            try:
                await self._export_task
            except asyncio.CancelledError:
                pass
            self._export_task = None

        # Export final metrics
        await self._export_metrics()

        # Clear metrics and exporters
        self._metrics.clear()
        self._exporters.clear()


# Global metrics manager instance
metrics_manager = MetricsManager()
