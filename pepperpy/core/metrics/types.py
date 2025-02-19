"""Metric-specific types and enums."""

from enum import Enum, auto
from typing import Dict, Union

# Type aliases
MetricValue = Union[int, float, str, bool]
MetricLabels = Dict[str, str]
MetricTags = Dict[str, str]


class MetricType(Enum):
    """Metric type enumeration."""

    COUNTER = auto()
    GAUGE = auto()


class MetricUnit(Enum):
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
