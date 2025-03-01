"""Metrics management system for PepperPy.

This module provides a unified metrics collection and reporting system
for tracking performance, usage, and other metrics across the framework.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
import logging


class Metric(ABC):
    """Base class for all metrics."""

    def __init__(self, name: str, description: str, labels: Optional[Dict[str, str]] = None):
        """Initialize metric.

        Args:
            name: Metric name
            description: Metric description
            labels: Optional metric labels
        """
        self.name = name
        self.description = description
        self.labels = labels or {}
        self._logger = logging.getLogger(f"pepperpy.metrics.{name}")

    @abstractmethod
    async def record(self, value: Any, labels: Optional[Dict[str, str]] = None) -> None:
        """Record a metric value.

        Args:
            value: Metric value
            labels: Optional additional labels
        """
        pass


class Counter(Metric):
    """Counter metric that can only increase."""

    def __init__(self, name: str, description: str, labels: Optional[Dict[str, str]] = None):
        """Initialize counter.

        Args:
            name: Counter name
            description: Counter description
            labels: Optional counter labels
        """
        super().__init__(name, description, labels)
        self._value = 0

    async def record(self, value: Union[int, float] = 1, labels: Optional[Dict[str, str]] = None) -> None:
        """Increment counter.

        Args:
            value: Increment value (default: 1)
            labels: Optional additional labels
        """
        self._value += value
        self._logger.debug(f"Counter {self.name} incremented by {value} to {self._value}")

    async def get_value(self) -> Union[int, float]:
        """Get current counter value.

        Returns:
            Current value
        """
        return self._value


class Gauge(Metric):
    """Gauge metric that can increase and decrease."""

    def __init__(self, name: str, description: str, labels: Optional[Dict[str, str]] = None):
        """Initialize gauge.

        Args:
            name: Gauge name
            description: Gauge description
            labels: Optional gauge labels
        """
        super().__init__(name, description, labels)
        self._value = 0

    async def record(self, value: Union[int, float], labels: Optional[Dict[str, str]] = None) -> None:
        """Set gauge value.

        Args:
            value: New gauge value
            labels: Optional additional labels
        """
        self._value = value
        self._logger.debug(f"Gauge {self.name} set to {value}")

    async def get_value(self) -> Union[int, float]:
        """Get current gauge value.

        Returns:
            Current value
        """
        return self._value


class Histogram(Metric):
    """Histogram metric for measuring distributions."""

    def __init__(
        self,
        name: str,
        description: str,
        labels: Optional[Dict[str, str]] = None,
        buckets: Optional[List[float]] = None,
    ):
        """Initialize histogram.

        Args:
            name: Histogram name
            description: Histogram description
            labels: Optional histogram labels
            buckets: Optional histogram buckets
        """
        super().__init__(name, description, labels)
        self._buckets = buckets or [0.1, 0.5, 1.0, 2.5, 5.0, 10.0]
        self._values: List[float] = []

    async def record(self, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Record a histogram observation.

        Args:
            value: Observation value
            labels: Optional additional labels
        """
        self._values.append(value)
        self._logger.debug(f"Histogram {self.name} observed value {value}")

    async def get_values(self) -> List[float]:
        """Get all recorded values.

        Returns:
            List of values
        """
        return self._values


class MetricsManager:
    """Manager for creating and tracking metrics."""

    def __init__(self, namespace: str):
        """Initialize metrics manager.

        Args:
            namespace: Metrics namespace
        """
        self.namespace = namespace
        self._metrics: Dict[str, Metric] = {}
        self._logger = logging.getLogger(f"pepperpy.metrics.{namespace}")

    async def initialize(self) -> None:
        """Initialize metrics manager."""
        self._logger.info(f"Initializing metrics manager for namespace: {self.namespace}")

    async def cleanup(self) -> None:
        """Clean up metrics manager."""
        self._metrics.clear()
        self._logger.info(f"Cleaned up metrics manager for namespace: {self.namespace}")

    async def create_counter(
        self, name: str, description: str, labels: Optional[Dict[str, str]] = None
    ) -> Counter:
        """Create a counter metric.

        Args:
            name: Counter name
            description: Counter description
            labels: Optional counter labels

        Returns:
            Counter metric
        """
        full_name = f"{self.namespace}.{name}"
        counter = Counter(full_name, description, labels)
        self._metrics[full_name] = counter
        self._logger.debug(f"Created counter: {full_name}")
        return counter

    async def create_gauge(
        self, name: str, description: str, labels: Optional[Dict[str, str]] = None
    ) -> Gauge:
        """Create a gauge metric.

        Args:
            name: Gauge name
            description: Gauge description
            labels: Optional gauge labels

        Returns:
            Gauge metric
        """
        full_name = f"{self.namespace}.{name}"
        gauge = Gauge(full_name, description, labels)
        self._metrics[full_name] = gauge
        self._logger.debug(f"Created gauge: {full_name}")
        return gauge

    async def create_histogram(
        self,
        name: str,
        description: str,
        labels: Optional[Dict[str, str]] = None,
        buckets: Optional[List[float]] = None,
    ) -> Histogram:
        """Create a histogram metric.

        Args:
            name: Histogram name
            description: Histogram description
            labels: Optional histogram labels
            buckets: Optional histogram buckets

        Returns:
            Histogram metric
        """
        full_name = f"{self.namespace}.{name}"
        histogram = Histogram(full_name, description, labels, buckets)
        self._metrics[full_name] = histogram
        self._logger.debug(f"Created histogram: {full_name}")
        return histogram

    async def get_metric(self, name: str) -> Optional[Metric]:
        """Get a metric by name.

        Args:
            name: Metric name

        Returns:
            Metric or None if not found
        """
        full_name = f"{self.namespace}.{name}"
        return self._metrics.get(full_name)

    async def increment_counter(
        self, name: str, value: Union[int, float] = 1, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Increment a counter metric.

        Args:
            name: Counter name
            value: Increment value (default: 1)
            labels: Optional additional labels
        """
        full_name = f"{self.namespace}.{name}"
        counter = self._metrics.get(full_name)
        if counter is not None and isinstance(counter, Counter):
            await counter.record(value, labels)
        else:
            self._logger.warning(f"Counter not found: {full_name}")

    async def set_gauge(
        self, name: str, value: Union[int, float], labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Set a gauge metric.

        Args:
            name: Gauge name
            value: New gauge value
            labels: Optional additional labels
        """
        full_name = f"{self.namespace}.{name}"
        gauge = self._metrics.get(full_name)
        if gauge is not None and isinstance(gauge, Gauge):
            await gauge.record(value, labels)
        else:
            self._logger.warning(f"Gauge not found: {full_name}")

    async def observe_histogram(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a histogram observation.

        Args:
            name: Histogram name
            value: Observation value
            labels: Optional additional labels
        """
        full_name = f"{self.namespace}.{name}"
        histogram = self._metrics.get(full_name)
        if histogram is not None and isinstance(histogram, Histogram):
            await histogram.record(value, labels)
        else:
            self._logger.warning(f"Histogram not found: {full_name}")
