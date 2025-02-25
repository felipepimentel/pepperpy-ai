"""Metric types.

This module provides metric type definitions.
"""

from enum import Enum


class MetricType(Enum):
    """Types of metrics."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"


__all__ = ["MetricType"]