"""Base metrics functionality for the Pepperpy framework.

This module provides base metrics functionality including metrics collection,
aggregation, and export.
"""

import asyncio
import logging
from collections.abc import AsyncGenerator
from datetime import datetime

from pepperpy.core.errors import MetricsError
from pepperpy.core.lifecycle.types import Lifecycle
from pepperpy.core.metrics.types import (
    BaseMetric,
    MetricCounter,
    MetricHistogram,
    MetricLabels,
    MetricType,
    MetricValue,
)
from pepperpy.core.types.states import ComponentState


class MetricsManager(Lifecycle):
    """Manager for metrics collection and aggregation."""

    def __init__(self, name: str = "metrics") -> None:
        """Initialize metrics manager.

        Args:
            name: Manager name
        """
        self._name = name
        self._state = ComponentState.UNREGISTERED
        self._metrics: dict[str, BaseMetric] = {}
        self._queue: asyncio.Queue[
            tuple[str, float, MetricType, MetricLabels, datetime]
        ] = asyncio.Queue()
        self._task: asyncio.Task[None] | None = None
        self.logger = logging.getLogger(__name__)

    @property
    def name(self) -> str:
        """Get component name."""
        return self._name

    async def initialize(self) -> None:
        """Initialize metrics manager."""
        try:
            self._state = ComponentState.INITIALIZING
            self._task = asyncio.create_task(self._process_metrics())
            self._state = ComponentState.READY
        except Exception as e:
            self._state = ComponentState.ERROR
            raise MetricsError(f"Failed to initialize metrics manager: {e}")

    async def cleanup(self) -> None:
        """Clean up metrics manager."""
        try:
            self._state = ComponentState.CLEANING
            if self._task:
                self._task.cancel()
                await self._task
            self._state = ComponentState.CLEANED
        except Exception as e:
            self._state = ComponentState.ERROR
            raise MetricsError(f"Failed to clean up metrics manager: {e}")

    async def create_counter(
        self,
        name: str,
        description: str = "",
        labels: MetricLabels | None = None,
    ) -> MetricCounter:
        """Create a counter metric.

        Args:
            name: Counter name
            description: Counter description
            labels: Optional counter labels

        Returns:
            MetricCounter: Counter metric

        Raises:
            MetricsError: If counter creation fails
        """
        try:
            counter = MetricCounter(name, description, labels)
            self._metrics[name] = counter
            return counter
        except Exception as e:
            raise MetricsError(f"Failed to create counter {name}: {e}")

    async def create_histogram(
        self,
        name: str,
        description: str = "",
        buckets: list[float] | None = None,
        labels: MetricLabels | None = None,
    ) -> MetricHistogram:
        """Create a histogram metric.

        Args:
            name: Histogram name
            description: Histogram description
            buckets: Optional histogram buckets
            labels: Optional histogram labels

        Returns:
            MetricHistogram: Histogram metric

        Raises:
            MetricsError: If histogram creation fails
        """
        try:
            histogram = MetricHistogram(name, description, buckets, labels)
            self._metrics[name] = histogram
            return histogram
        except Exception as e:
            raise MetricsError(f"Failed to create histogram {name}: {e}")

    async def record_metric(
        self,
        name: str,
        value: float,
        metric_type: MetricType,
        labels: MetricLabels | None = None,
        timestamp: datetime | None = None,
    ) -> None:
        """Record a metric value.

        Args:
            name: Metric name
            value: Metric value
            metric_type: Metric type
            labels: Optional metric labels
            timestamp: Optional timestamp

        Raises:
            MetricsError: If metric recording fails
        """
        try:
            await self._queue.put((
                name,
                value,
                metric_type,
                labels or {},
                timestamp or datetime.utcnow(),
            ))
        except Exception as e:
            raise MetricsError(f"Failed to record metric {name}: {e}")

    async def get_metric(
        self,
        name: str,
        labels: MetricLabels | None = None,
    ) -> MetricValue | None:
        """Get metric value.

        Args:
            name: Metric name
            labels: Optional metric labels

        Returns:
            MetricValue | None: Metric value if found

        Raises:
            MetricsError: If metric retrieval fails
        """
        try:
            metric = self._metrics.get(name)
            if not metric:
                return None

            return {
                "name": name,
                "type": metric.type,
                "value": metric.value,
                "labels": labels or {},
                "timestamp": datetime.utcnow(),
            }
        except Exception as e:
            raise MetricsError(f"Failed to get metric {name}: {e}")

    async def list_metrics(
        self,
        pattern: str | None = None,
        metric_type: MetricType | None = None,
        labels: MetricLabels | None = None,
    ) -> AsyncGenerator[MetricValue, None]:
        """List metrics.

        Args:
            pattern: Optional name pattern
            metric_type: Optional metric type
            labels: Optional metric labels

        Yields:
            MetricValue: Metric values

        Raises:
            MetricsError: If metric listing fails
        """
        try:
            for name, metric in self._metrics.items():
                if pattern and pattern not in name:
                    continue
                if metric_type and metric.type != metric_type:
                    continue
                if labels and not all(
                    metric.labels.get(k) == v for k, v in labels.items()
                ):
                    continue

                metric_value = await self.get_metric(name, labels)
                if metric_value is not None:
                    yield metric_value
        except Exception as e:
            raise MetricsError(f"Failed to list metrics: {e}")

    async def _process_metrics(self) -> None:
        """Process metrics from queue."""
        while True:
            try:
                name, value, metric_type, labels, timestamp = await self._queue.get()
                await self._handle_metric(name, value, metric_type, labels, timestamp)
                self._queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Failed to process metric: {e}")

    async def _handle_metric(
        self,
        name: str,
        value: float,
        metric_type: MetricType,
        labels: MetricLabels,
        timestamp: datetime,
    ) -> None:
        """Handle metric value.

        Args:
            name: Metric name
            value: Metric value
            metric_type: Metric type
            labels: Metric labels
            timestamp: Metric timestamp
        """
        metric = self._metrics.get(name)
        if not metric:
            if metric_type == MetricType.COUNTER:
                metric = await self.create_counter(name, labels=labels)
            else:
                metric = await self.create_histogram(name, labels=labels)
            self._metrics[name] = metric

        if isinstance(metric, MetricCounter):
            metric.inc(value)
        elif isinstance(metric, MetricHistogram):
            metric.observe(value)


__all__ = ["MetricsManager"]
