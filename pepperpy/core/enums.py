"""Core enums for the Pepperpy framework.

This module provides core enum definitions used throughout the framework.
"""

from enum import Enum


class MetricType(str, Enum):
    """Types of metrics that can be collected."""

    COUNTER = "counter"  # Monotonically increasing counter
    GAUGE = "gauge"  # Value that can go up and down
    HISTOGRAM = "histogram"  # Distribution of values
    SUMMARY = "summary"  # Statistical summary
    TIMER = "timer"  # Duration measurements
