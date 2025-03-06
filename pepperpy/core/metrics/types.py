"""Type definitions for the metrics system.

This module defines the types used by the metrics system for
collecting and reporting metrics.
"""

from enum import Enum, auto
from typing import Dict, Optional, Union

# Type aliases
MetricValue = Union[int, float, str, bool]
MetricName = str
MetricTags = Dict[str, str]


class MetricUnit(Enum):
    """Units for metrics."""

    # Time units
    MILLISECONDS = "ms"
    SECONDS = "s"
    MINUTES = "min"
    HOURS = "h"

    # Size units
    BYTES = "bytes"
    KILOBYTES = "kb"
    MEGABYTES = "mb"
    GIGABYTES = "gb"

    # Count units
    COUNT = "count"
    PERCENT = "percent"

    # Custom
    CUSTOM = "custom"


class MetricType(Enum):
    """Types of metrics that can be collected."""

    # Counter metrics (values that only increase)
    COUNTER = auto()

    # Gauge metrics (values that can go up and down)
    GAUGE = auto()

    # Histogram metrics (distribution of values)
    HISTOGRAM = auto()

    # Summary metrics (calculated statistics)
    SUMMARY = auto()

    # Timer metrics (duration measurements)
    TIMER = auto()


class MetricDefinition:
    """Definition of a metric."""

    def __init__(
        self,
        name: MetricName,
        type: MetricType,
        description: str,
        unit: MetricUnit = MetricUnit.CUSTOM,
        tags: Optional[MetricTags] = None,
    ):
        """Initialize a new metric definition.

        Args:
            name: The name of the metric
            type: The type of the metric
            description: A description of what the metric measures
            unit: The unit of the metric
            tags: Optional tags to associate with the metric
        """
        self.name = name
        self.type = type
        self.description = description
        self.unit = unit
        self.tags = tags or {}

    def __repr__(self) -> str:
        """Return a string representation of the metric definition."""
        return f"MetricDefinition(name={self.name}, type={self.type}, unit={self.unit})"
