"""Models for the metrics system.

This module defines the models used by the metrics system for
collecting and reporting metrics.
"""

from typing import Dict, List, Optional, cast

from pepperpy.core.metrics.types import (
    MetricDefinition,
    MetricName,
    MetricTags,
    MetricType,
    MetricUnit,
    MetricValue,
)


class Metric:
    """Base class for all metrics."""

    def __init__(
        self,
        name: MetricName,
        description: str,
        unit: MetricUnit = MetricUnit.CUSTOM,
        tags: Optional[MetricTags] = None,
    ):
        """Initialize a new metric.

        Args:
            name: The name of the metric
            description: A description of what the metric measures
            unit: The unit of the metric
            tags: Optional tags to associate with the metric
        """
        self.definition = MetricDefinition(
            name=name,
            type=self._get_metric_type(),
            description=description,
            unit=unit,
            tags=tags,
        )
        self.value: MetricValue = self._get_default_value()

    def _get_metric_type(self) -> MetricType:
        """Get the type of this metric."""
        raise NotImplementedError("Subclasses must implement this method")

    def _get_default_value(self) -> MetricValue:
        """Get the default value for this metric."""
        raise NotImplementedError("Subclasses must implement this method")

    def __repr__(self) -> str:
        """Return a string representation of the metric."""
        return f"{self.__class__.__name__}(name={self.definition.name}, value={self.value})"


class Counter(Metric):
    """A metric that represents a value that can only increase."""

    def __init__(
        self,
        name: MetricName,
        description: str,
        unit: MetricUnit = MetricUnit.COUNT,
        tags: Optional[MetricTags] = None,
        initial_value: int = 0,
    ):
        """Initialize a new counter metric.

        Args:
            name: The name of the metric
            description: A description of what the metric measures
            unit: The unit of the metric
            tags: Optional tags to associate with the metric
            initial_value: The initial value of the counter
        """
        super().__init__(name, description, unit, tags)
        self.value = initial_value

    def _get_metric_type(self) -> MetricType:
        """Get the type of this metric."""
        return MetricType.COUNTER

    def _get_default_value(self) -> int:
        """Get the default value for this metric."""
        return 0

    def increment(self, amount: int = 1) -> int:
        """Increment the counter by the specified amount.

        Args:
            amount: The amount to increment by

        Returns:
            The new value of the counter
        """
        if amount < 0:
            raise ValueError("Counter can only be incremented by a positive amount")
        self.value = cast(int, self.value) + amount
        return cast(int, self.value)


class Gauge(Metric):
    """A metric that represents a value that can go up and down."""

    def __init__(
        self,
        name: MetricName,
        description: str,
        unit: MetricUnit = MetricUnit.CUSTOM,
        tags: Optional[MetricTags] = None,
        initial_value: float = 0.0,
    ):
        """Initialize a new gauge metric.

        Args:
            name: The name of the metric
            description: A description of what the metric measures
            unit: The unit of the metric
            tags: Optional tags to associate with the metric
            initial_value: The initial value of the gauge
        """
        super().__init__(name, description, unit, tags)
        self.value = initial_value

    def _get_metric_type(self) -> MetricType:
        """Get the type of this metric."""
        return MetricType.GAUGE

    def _get_default_value(self) -> float:
        """Get the default value for this metric."""
        return 0.0

    def set(self, value: float) -> float:
        """Set the gauge to the specified value.

        Args:
            value: The value to set

        Returns:
            The new value of the gauge
        """
        self.value = value
        return cast(float, self.value)

    def increment(self, amount: float = 1.0) -> float:
        """Increment the gauge by the specified amount.

        Args:
            amount: The amount to increment by

        Returns:
            The new value of the gauge
        """
        self.value = cast(float, self.value) + amount
        return cast(float, self.value)

    def decrement(self, amount: float = 1.0) -> float:
        """Decrement the gauge by the specified amount.

        Args:
            amount: The amount to decrement by

        Returns:
            The new value of the gauge
        """
        self.value = cast(float, self.value) - amount
        return cast(float, self.value)


class Histogram(Metric):
    """A metric that tracks the distribution of a value."""

    def __init__(
        self,
        name: MetricName,
        description: str,
        unit: MetricUnit = MetricUnit.CUSTOM,
        tags: Optional[MetricTags] = None,
        buckets: Optional[List[float]] = None,
    ):
        """Initialize a new histogram metric.

        Args:
            name: The name of the metric
            description: A description of what the metric measures
            unit: The unit of the metric
            tags: Optional tags to associate with the metric
            buckets: Optional list of bucket boundaries
        """
        super().__init__(name, description, unit, tags)
        self.buckets = buckets or [
            0.005,
            0.01,
            0.025,
            0.05,
            0.1,
            0.25,
            0.5,
            1,
            2.5,
            5,
            10,
        ]
        self.values: List[float] = []
        # Initialize with default value
        self._update_value()

    def _get_metric_type(self) -> MetricType:
        """Get the type of this metric."""
        return MetricType.HISTOGRAM

    def _get_default_value(self) -> str:
        """Get the default value for this metric."""
        return "{}"

    def _update_value(self) -> None:
        """Update the value dictionary."""
        # We store the serialized representation as a string to satisfy the MetricValue type
        value_dict = {
            "count": len(self.values),
            "sum": sum(self.values) if self.values else 0,
            "buckets": {
                str(b): sum(1 for v in self.values if v <= b) for b in self.buckets
            },
        }
        self.value = str(value_dict)

    def observe(self, value: float) -> None:
        """Record a value.

        Args:
            value: The value to record
        """
        self.values.append(value)
        self._update_value()


class Summary(Metric):
    """A metric that calculates statistics about a value."""

    def __init__(
        self,
        name: MetricName,
        description: str,
        unit: MetricUnit = MetricUnit.CUSTOM,
        tags: Optional[MetricTags] = None,
    ):
        """Initialize a new summary metric.

        Args:
            name: The name of the metric
            description: A description of what the metric measures
            unit: The unit of the metric
            tags: Optional tags to associate with the metric
        """
        super().__init__(name, description, unit, tags)
        self.values: List[float] = []
        # Initialize with default value
        self._update_value()

    def _get_metric_type(self) -> MetricType:
        """Get the type of this metric."""
        return MetricType.SUMMARY

    def _get_default_value(self) -> str:
        """Get the default value for this metric."""
        return "{}"

    def _update_value(self) -> None:
        """Update the value dictionary."""
        # We store the serialized representation as a string to satisfy the MetricValue type
        if self.values:
            value_dict = {
                "count": len(self.values),
                "sum": sum(self.values),
                "min": min(self.values),
                "max": max(self.values),
                "avg": sum(self.values) / len(self.values),
            }
        else:
            value_dict = {
                "count": 0,
                "sum": 0,
                "min": 0,
                "max": 0,
                "avg": 0,
            }
        self.value = str(value_dict)

    def observe(self, value: float) -> None:
        """Record a value.

        Args:
            value: The value to record
        """
        self.values.append(value)
        self._update_value()


class MetricRecord:
    """A record of a metric value at a point in time."""

    def __init__(
        self,
        name: MetricName,
        value: MetricValue,
        type: MetricType,
        unit: MetricUnit,
        tags: Optional[MetricTags] = None,
        timestamp: Optional[float] = None,
    ):
        """Initialize a new metric record.

        Args:
            name: The name of the metric
            value: The value of the metric
            type: The type of the metric
            unit: The unit of the metric
            tags: Optional tags to associate with the metric
            timestamp: Optional timestamp for the record
        """
        self.name = name
        self.value = value
        self.type = type
        self.unit = unit
        self.tags = tags or {}
        self.timestamp = timestamp or 0.0

    def __repr__(self) -> str:
        """Return a string representation of the metric record."""
        return f"MetricRecord(name={self.name}, value={self.value}, type={self.type})"


class MetricsRegistry:
    """Registry for metrics."""

    def __init__(self):
        """Initialize a new metrics registry."""
        self.metrics: Dict[str, Metric] = {}

    def register(self, metric: Metric) -> None:
        """Register a metric.

        Args:
            metric: The metric to register
        """
        self.metrics[metric.definition.name] = metric

    def get(self, name: str) -> Optional[Metric]:
        """Get a metric by name.

        Args:
            name: The name of the metric

        Returns:
            The metric, or None if not found
        """
        return self.metrics.get(name)

    def get_all(self) -> Dict[str, Metric]:
        """Get all registered metrics.

        Returns:
            A dictionary of all registered metrics
        """
        return self.metrics.copy()


class MetricsCollector:
    """Collector for metrics."""

    def __init__(self, registry: Optional[MetricsRegistry] = None):
        """Initialize a new metrics collector.

        Args:
            registry: Optional registry to use
        """
        self.registry = registry or MetricsRegistry()

    def register(self, metric: Metric) -> None:
        """Register a metric.

        Args:
            metric: The metric to register
        """
        self.registry.register(metric)

    def collect(self) -> List[MetricRecord]:
        """Collect all metrics.

        Returns:
            A list of metric records
        """
        records = []
        for metric in self.registry.get_all().values():
            records.append(
                MetricRecord(
                    name=metric.definition.name,
                    value=metric.value,
                    type=metric.definition.type,
                    unit=metric.definition.unit,
                    tags=metric.definition.tags,
                )
            )
        return records
