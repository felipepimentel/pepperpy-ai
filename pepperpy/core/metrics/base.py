"""Base metrics module for the Pepperpy framework.

This module provides core metrics functionality including:
- Metrics collection
- Metrics aggregation
- Metrics export
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any

from pepperpy.core.errors import ValidationError
from pepperpy.core.metrics.types import (
    MetricCounter,
    MetricHistogram,
    MetricLabels,
    MetricType,
    MetricValue,
)
from pepperpy.core.protocols.lifecycle import Lifecycle
from pepperpy.core.types import ComponentState


class MetricsManager(Lifecycle):
    """Metrics manager."""

    def __init__(self, name: str = "metrics") -> None:
        """Initialize metrics manager.

        Args:
            name: Manager name
        """
        self.name = name
        self._state = ComponentState.CREATED
        self._metrics: dict[str, Any] = {}
        self._queue: asyncio.Queue[MetricValue] = asyncio.Queue()
        self._task: asyncio.Task[None] | None = None
        self.logger = logging.getLogger(__name__)

    async def initialize(self) -> None:
        """Initialize manager."""
        try:
            self._state = ComponentState.INITIALIZING
            self._task = asyncio.create_task(self._process_metrics())
            self._state = ComponentState.READY
        except Exception as e:
            self._state = ComponentState.ERROR
            raise ValidationError(f"Failed to initialize manager: {e}")

    async def cleanup(self) -> None:
        """Clean up manager."""
        try:
            self._state = ComponentState.CLEANING
            if self._task:
                self._task.cancel()
                await self._task
            self._state = ComponentState.CLEANED
        except Exception as e:
            self._state = ComponentState.ERROR
            raise ValidationError(f"Failed to clean up manager: {e}")

    async def create_counter(
        self,
        name: str,
        description: str = "",
        labels: MetricLabels | None = None,
    ) -> MetricCounter:
        """Create a counter metric.

        Args:
            name: Metric name
            description: Metric description
            labels: Optional metric labels

        Returns:
            MetricCounter: Created counter

        Raises:
            ValidationError: If metric already exists
        """
        if name in self._metrics:
            raise ValidationError(f"Metric already exists: {name}")

        counter = MetricCounter(
            name=name,
            description=description,
            labels=labels or {},
        )
        self._metrics[name] = counter
        return counter

    async def create_histogram(
        self,
        name: str,
        description: str = "",
        buckets: list[float] | None = None,
        labels: MetricLabels | None = None,
    ) -> MetricHistogram:
        """Create a histogram metric.

        Args:
            name: Metric name
            description: Metric description
            buckets: Optional histogram buckets
            labels: Optional metric labels

        Returns:
            MetricHistogram: Created histogram

        Raises:
            ValidationError: If metric already exists
        """
        if name in self._metrics:
            raise ValidationError(f"Metric already exists: {name}")

        histogram = MetricHistogram(
            name=name,
            description=description,
            buckets=buckets or [0.1, 0.5, 1.0, 2.0, 5.0],
            labels=labels or {},
        )
        self._metrics[name] = histogram
        return histogram

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
            ValidationError: If metric not found
        """
        if name not in self._metrics:
            raise ValidationError(f"Metric not found: {name}")

        metric = self._metrics[name]
        metric_value = MetricValue(
            name=name,
            type=metric_type,
            value=value,
            labels=labels or {},
            timestamp=timestamp or datetime.utcnow(),
        )
        await self._queue.put(metric_value)

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
            MetricValue: Metric value if found
        """
        if name not in self._metrics:
            return None

        metric = self._metrics[name]
        if not isinstance(metric, (MetricCounter, MetricHistogram)):
            return None

        return MetricValue(
            name=name,
            type=metric.type,
            value=metric.value,
            labels=labels or {},
            timestamp=datetime.utcnow(),
        )

    async def list_metrics(
        self,
        pattern: str | None = None,
        metric_type: MetricType | None = None,
        labels: MetricLabels | None = None,
    ) -> AsyncIterator[MetricValue]:
        """List metrics.

        Args:
            pattern: Optional name pattern
            metric_type: Optional metric type
            labels: Optional metric labels

        Yields:
            MetricValue: Matching metrics
        """
        for name, metric in self._metrics.items():
            if pattern and pattern not in name:
                continue
            if metric_type and metric.type != metric_type:
                continue
            if labels and not all(metric.labels.get(k) == v for k, v in labels.items()):
                continue

            value = await self.get_metric(name, labels)
            if value:
                yield value

    async def _process_metrics(self) -> None:
        """Process metrics from queue."""
        while True:
            try:
                metric = await self._queue.get()
                await self._handle_metric(metric)
                self._queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Failed to process metric: {e}", exc_info=True)

    async def _handle_metric(self, metric: MetricValue) -> None:
        """Handle metric value.

        Args:
            metric: Metric value to handle
        """
        if metric.name not in self._metrics:
            return

        target = self._metrics[metric.name]
        if isinstance(target, MetricCounter):
            target.inc(metric.value)
        elif isinstance(target, MetricHistogram):
            target.observe(metric.value)


# Export public API
__all__ = [
    "MetricsManager",
]
