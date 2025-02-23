"""Base metrics implementation.

This module provides the core metrics functionality:
- Metric types (Counter, Gauge, Histogram, Summary)
- Metric registration and management
- Metric collection and export
"""

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Optional, TypeVar

from pydantic import BaseModel, Field

from pepperpy.core.lifecycle import Lifecycle
from pepperpy.core.types import ComponentState
from pepperpy.monitoring.logging import logger

# Type variables
T = TypeVar("T")
MetricType = TypeVar("MetricType", bound="Metric")


class MetricConfig(BaseModel):
    """Base configuration for metrics.

    Attributes:
        name: Metric name
        description: Metric description
        labels: Optional metric labels
        enabled: Whether metric is enabled
    """

    name: str = Field(description="Metric name")
    description: str = Field(description="Metric description")
    labels: dict[str, str] = Field(default_factory=dict, description="Metric labels")
    enabled: bool = Field(default=True, description="Whether metric is enabled")


class Metric(Lifecycle, ABC):
    """Base class for all metrics.

    All metrics must implement this interface to ensure consistent
    behavior across the framework.
    """

    def __init__(self, config: MetricConfig) -> None:
        """Initialize metric.

        Args:
            config: Metric configuration
        """
        super().__init__()
        self.config = config
        self._state = ComponentState.UNREGISTERED
        self._value: int | float = 0
        self._lock = asyncio.Lock()

    @property
    def name(self) -> str:
        """Get metric name."""
        return self.config.name

    @property
    def description(self) -> str:
        """Get metric description."""
        return self.config.description

    @property
    def labels(self) -> dict[str, str]:
        """Get metric labels."""
        return self.config.labels

    @property
    def value(self) -> int | float:
        """Get current metric value."""
        return self._value

    async def initialize(self) -> None:
        """Initialize metric."""
        try:
            self._state = ComponentState.RUNNING
            logger.info(f"Metric initialized: {self.name}")
        except Exception as e:
            self._state = ComponentState.ERROR
            logger.error(f"Failed to initialize metric: {e}")
            raise

    async def cleanup(self) -> None:
        """Clean up metric."""
        try:
            self._state = ComponentState.UNREGISTERED
            logger.info(f"Metric cleaned up: {self.name}")
        except Exception as e:
            logger.error(f"Failed to cleanup metric: {e}")
            raise

    @abstractmethod
    async def collect(self) -> dict[str, Any]:
        """Collect metric data.

        Returns:
            Dictionary containing metric data
        """
        pass


class Counter(Metric):
    """Counter metric type.

    Counters can only increase or be reset to zero.
    """

    async def inc(self, value: float = 1.0) -> None:
        """Increment counter.

        Args:
            value: Value to increment by (must be positive)
        """
        if value < 0:
            raise ValueError("Counter value cannot decrease")

        async with self._lock:
            self._value += value

    async def collect(self) -> dict[str, Any]:
        """Collect counter data.

        Returns:
            Dictionary containing counter data
        """
        return {
            "name": self.name,
            "description": self.description,
            "type": "counter",
            "value": self.value,
            "labels": self.labels,
            "timestamp": datetime.utcnow().isoformat(),
        }


class Gauge(Metric):
    """Gauge metric type.

    Gauges can increase and decrease.
    """

    async def inc(self, value: float = 1.0) -> None:
        """Increment gauge.

        Args:
            value: Value to increment by
        """
        async with self._lock:
            self._value += value

    async def dec(self, value: float = 1.0) -> None:
        """Decrement gauge.

        Args:
            value: Value to decrement by
        """
        async with self._lock:
            self._value -= value

    async def set(self, value: float) -> None:
        """Set gauge value.

        Args:
            value: Value to set
        """
        async with self._lock:
            self._value = value

    async def collect(self) -> dict[str, Any]:
        """Collect gauge data.

        Returns:
            Dictionary containing gauge data
        """
        return {
            "name": self.name,
            "description": self.description,
            "type": "gauge",
            "value": self.value,
            "labels": self.labels,
            "timestamp": datetime.utcnow().isoformat(),
        }


class Histogram(Metric):
    """Histogram metric type.

    Histograms track distributions of values.
    """

    def __init__(
        self, config: MetricConfig, buckets: list[float] | None = None
    ) -> None:
        """Initialize histogram.

        Args:
            config: Metric configuration
            buckets: Optional bucket boundaries
        """
        super().__init__(config)
        self._buckets = sorted(buckets or [0.1, 0.5, 1.0, 2.0, 5.0])
        self._bucket_values: dict[float, int] = {b: 0 for b in self._buckets}
        self._sum = 0.0
        self._count = 0

    async def observe(self, value: float) -> None:
        """Record observation.

        Args:
            value: Value to observe
        """
        async with self._lock:
            self._sum += value
            self._count += 1
            for bucket in self._buckets:
                if value <= bucket:
                    self._bucket_values[bucket] += 1

    async def collect(self) -> dict[str, Any]:
        """Collect histogram data.

        Returns:
            Dictionary containing histogram data
        """
        return {
            "name": self.name,
            "description": self.description,
            "type": "histogram",
            "buckets": self._bucket_values,
            "sum": self._sum,
            "count": self._count,
            "labels": self.labels,
            "timestamp": datetime.utcnow().isoformat(),
        }


class Summary(Metric):
    """Summary metric type.

    Summaries track size and count of events.
    """

    def __init__(
        self,
        config: MetricConfig,
        max_age: float = 60.0,
        age_buckets: int = 5,
    ) -> None:
        """Initialize summary.

        Args:
            config: Metric configuration
            max_age: Maximum age of observations in seconds
            age_buckets: Number of age buckets
        """
        super().__init__(config)
        self._max_age = max_age
        self._age_buckets = age_buckets
        self._values: list[tuple[datetime, float]] = []

    async def observe(self, value: float) -> None:
        """Record observation.

        Args:
            value: Value to observe
        """
        async with self._lock:
            now = datetime.utcnow()
            self._values.append((now, value))
            cutoff = now.timestamp() - self._max_age
            self._values = [
                (ts, val) for ts, val in self._values if ts.timestamp() > cutoff
            ]

    async def collect(self) -> dict[str, Any]:
        """Collect summary data.

        Returns:
            Dictionary containing summary data
        """
        async with self._lock:
            values = [v for _, v in self._values]
            count = len(values)
            sum_values = sum(values) if values else 0.0

        return {
            "name": self.name,
            "description": self.description,
            "type": "summary",
            "count": count,
            "sum": sum_values,
            "labels": self.labels,
            "timestamp": datetime.utcnow().isoformat(),
        }


class MetricsManager(Lifecycle):
    """Metrics manager implementation.

    This class handles metric registration, collection, and export.
    """

    _instance: Optional["MetricsManager"] = None

    def __init__(self) -> None:
        """Initialize metrics manager."""
        super().__init__()
        self._metrics: dict[str, Metric] = {}
        self._state = ComponentState.UNREGISTERED

    @classmethod
    def get_instance(cls) -> "MetricsManager":
        """Get metrics manager instance.

        Returns:
            MetricsManager instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def initialize(self) -> None:
        """Initialize metrics manager."""
        try:
            self._state = ComponentState.RUNNING
            logger.info("Metrics manager initialized")
        except Exception as e:
            self._state = ComponentState.ERROR
            logger.error(f"Failed to initialize metrics manager: {e}")
            raise

    async def cleanup(self) -> None:
        """Clean up metrics manager."""
        try:
            self._metrics.clear()
            self._state = ComponentState.UNREGISTERED
            logger.info("Metrics manager cleaned up")
        except Exception as e:
            logger.error(f"Failed to cleanup metrics manager: {e}")
            raise

    def register_metric(self, metric: Metric) -> None:
        """Register metric.

        Args:
            metric: Metric to register
        """
        if metric.name in self._metrics:
            raise ValueError(f"Metric already registered: {metric.name}")
        self._metrics[metric.name] = metric

    def unregister_metric(self, name: str) -> None:
        """Unregister metric.

        Args:
            name: Name of metric to unregister
        """
        if name in self._metrics:
            del self._metrics[name]

    async def create_counter(
        self, name: str, description: str, labels: dict[str, str] | None = None
    ) -> Counter:
        """Create and register counter.

        Args:
            name: Counter name
            description: Counter description
            labels: Optional counter labels

        Returns:
            Counter instance
        """
        config = MetricConfig(
            name=name,
            description=description,
            labels=labels or {},
        )
        counter = Counter(config)
        self.register_metric(counter)
        await counter.initialize()
        return counter

    async def create_gauge(
        self, name: str, description: str, labels: dict[str, str] | None = None
    ) -> Gauge:
        """Create and register gauge.

        Args:
            name: Gauge name
            description: Gauge description
            labels: Optional gauge labels

        Returns:
            Gauge instance
        """
        config = MetricConfig(
            name=name,
            description=description,
            labels=labels or {},
        )
        gauge = Gauge(config)
        self.register_metric(gauge)
        await gauge.initialize()
        return gauge

    async def create_histogram(
        self,
        name: str,
        description: str,
        buckets: list[float] | None = None,
        labels: dict[str, str] | None = None,
    ) -> Histogram:
        """Create and register histogram.

        Args:
            name: Histogram name
            description: Histogram description
            buckets: Optional bucket boundaries
            labels: Optional histogram labels

        Returns:
            Histogram instance
        """
        config = MetricConfig(
            name=name,
            description=description,
            labels=labels or {},
        )
        histogram = Histogram(config, buckets)
        self.register_metric(histogram)
        await histogram.initialize()
        return histogram

    async def create_summary(
        self,
        name: str,
        description: str,
        max_age: float = 60.0,
        age_buckets: int = 5,
        labels: dict[str, str] | None = None,
    ) -> Summary:
        """Create and register summary.

        Args:
            name: Summary name
            description: Summary description
            max_age: Maximum age of observations in seconds
            age_buckets: Number of age buckets
            labels: Optional summary labels

        Returns:
            Summary instance
        """
        config = MetricConfig(
            name=name,
            description=description,
            labels=labels or {},
        )
        summary = Summary(config, max_age, age_buckets)
        self.register_metric(summary)
        await summary.initialize()
        return summary

    async def collect_all(self) -> list[dict[str, Any]]:
        """Collect all metrics.

        Returns:
            List of metric data dictionaries
        """
        metrics = []
        for metric in self._metrics.values():
            try:
                data = await metric.collect()
                metrics.append(data)
            except Exception as e:
                logger.error(f"Failed to collect metric {metric.name}: {e}")
        return metrics
