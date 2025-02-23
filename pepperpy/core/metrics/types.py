"""Metric type definitions for the Pepperpy framework.

This module provides type definitions for metrics to avoid circular imports
and provide a centralized location for metric-related types.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import Any, Protocol, TypeVar, Union, runtime_checkable

from pepperpy.utils.imports import safe_import

# Import prometheus_client safely
prometheus_client = safe_import("prometheus_client")

# Type variables
T_Metric = TypeVar("T_Metric", bound="Metric")

# Type aliases
MetricValue = Union[int, float]
MetricLabels = dict[str, str]
MetricType = Union["MetricCounter", "MetricHistogram"]


@runtime_checkable
class Metric(Protocol):
    """Protocol for metrics."""

    @abstractmethod
    def inc(self, value: float = 1.0) -> None:
        """Increment counter.

        Args:
            value: Value to increment by
        """
        ...

    @abstractmethod
    def observe(self, value: float) -> None:
        """Record observation.

        Args:
            value: Value to record
        """
        ...

    @abstractmethod
    def get_value(self) -> Any:
        """Get metric value.

        Returns:
            Current metric value
        """
        ...


# Type aliases for metrics
if prometheus_client:
    PrometheusCounter = prometheus_client.Counter
    PrometheusHistogram = prometheus_client.Histogram
    MetricCounter = PrometheusCounter
    MetricHistogram = PrometheusHistogram
else:
    # Use string literals for forward references
    MetricCounter = "CoreCounter"
    MetricHistogram = "CoreHistogram"


__all__ = [
    # Type variables
    "T_Metric",
    # Protocols
    "Metric",
    # Type aliases
    "MetricCounter",
    "MetricHistogram",
    "MetricValue",
    "MetricLabels",
    "MetricType",
]
