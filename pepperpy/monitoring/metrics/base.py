"""Base metrics functionality for the Pepperpy framework.

This module provides base classes for metrics functionality.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Optional, TypeVar

from pepperpy.core.models import BaseModel, Field
from pepperpy.core.lifecycle.base import LifecycleComponent
from pepperpy.core.types.states import ComponentState
from pepperpy.monitoring.logging import get_logger

# Type variables
T = TypeVar("T")

# Initialize logger
logger = get_logger(__name__)


class MetricConfig(BaseModel):
    """Configuration for a metric."""

    name: str = Field(description="Metric name")
    description: str = Field(default="", description="Metric description")
    labels: dict[str, str] = Field(default_factory=dict, description="Metric labels")


class Metric(LifecycleComponent):
    """Base class for metrics."""

    def __init__(self, config: MetricConfig) -> None:
        """Initialize the metric.

        Args:
            config: Metric configuration
        """
        super().__init__(config.name)
        self.config = config
        self._value: float = 0.0

    @property
    def value(self) -> float:
        """Get current value."""
        return self._value

    @abstractmethod
    def update(self, value: float) -> None:
        """Update metric value.

        Args:
            value: New value
        """
        ...


class Counter(Metric):
    """Counter metric type."""

    def update(self, value: float) -> None:
        """Increment counter.

        Args:
            value: Value to increment by
        """
        self._value += value


class Gauge(Metric):
    """Gauge metric type."""

    def update(self, value: float) -> None:
        """Set gauge value.

        Args:
            value: New value
        """
        self._value = value


class Histogram(Metric):
    """Histogram metric type."""

    def __init__(self, config: MetricConfig, buckets: list[float] | None = None) -> None:
        """Initialize histogram.

        Args:
            config: Metric configuration
            buckets: Optional histogram buckets
        """
        super().__init__(config)
        self.buckets = buckets or [0.1, 0.5, 1.0, 2.0, 5.0]
        self._bucket_values = {b: 0 for b in self.buckets}

    def update(self, value: float) -> None:
        """Observe value.

        Args:
            value: Value to observe
        """
        self._value = value
        for bucket in self.buckets:
            if value <= bucket:
                self._bucket_values[bucket] += 1

    def get_bucket_values(self) -> dict[float, int]:
        """Get bucket values.

        Returns:
            dict[float, int]: Bucket values
        """
        return self._bucket_values.copy()


class Summary(Metric):
    """Summary metric type."""

    def __init__(self, config: MetricConfig, max_age: float = 60.0) -> None:
        """Initialize summary.

        Args:
            config: Metric configuration
            max_age: Maximum age of values in seconds
        """
        super().__init__(config)
        self.max_age = max_age
        self._values: list[tuple[float, float]] = []

    def update(self, value: float) -> None:
        """Add value.

        Args:
            value: Value to add
        """
        now = asyncio.get_event_loop().time()
        self._values.append((now, value))
        self._cleanup()
        self._value = sum(v for _, v in self._values) / len(self._values)

    def _cleanup(self) -> None:
        """Remove old values."""
        now = asyncio.get_event_loop().time()
        self._values = [(t, v) for t, v in self._values if now - t <= self.max_age]


__all__ = [
    "Counter",
    "Gauge",
    "Histogram",
    "Metric",
    "MetricConfig",
    "Summary",
]
