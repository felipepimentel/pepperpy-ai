"""Metric-specific types and enums."""

from enum import Enum
from typing import Union

# Type aliases
MetricValue = Union[int, float, str, bool]
MetricLabels = dict[str, str]
MetricTags = dict[str, str]


class MetricType(str, Enum):
    """Types of metrics that can be collected."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class MetricUnit(str, Enum):
    """Common metric units."""

    COUNT = "count"
    SECONDS = "seconds"
    BYTES = "bytes"
    PERCENT = "percent"
    MILLISECONDS = "milliseconds"
    MICROSECONDS = "microseconds"
    NANOSECONDS = "nanoseconds"
    KILOBYTES = "kilobytes"
    MEGABYTES = "megabytes"
    GIGABYTES = "gigabytes"
    TERABYTES = "terabytes"
    BITS = "bits"
    KILOBITS = "kilobits"
    MEGABITS = "megabits"
    GIGABITS = "gigabits"
    TERABITS = "terabits"
    RATIO = "ratio"
    OPERATIONS = "operations"
    REQUESTS = "requests"
    MESSAGES = "messages"
    ERRORS = "errors"
    WARNINGS = "warnings"
    EVENTS = "events"
    CUSTOM = "custom"


__all__ = ["MetricLabels", "MetricTags", "MetricType", "MetricUnit", "MetricValue"]
