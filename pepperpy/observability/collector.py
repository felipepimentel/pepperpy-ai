"""Metrics collection functionality.

This module provides tools for collecting and managing metrics.
"""

from typing import Any

from pepperpy.core.observability.metrics import Counter, Gauge, Histogram


class MetricsCollector:
    """Collects and manages metrics."""

    def __init__(self) -> None:
        """Initialize metrics collector."""
        self._counters: dict[str, Counter] = {}
        self._gauges: dict[str, Gauge] = {}
        self._histograms: dict[str, Histogram] = {}

    def increment(self, name: str, labels: dict[str, str] | None = None) -> None:
        """Increment a counter.

        Args:
            name: Counter name
            labels: Optional metric labels
        """
        if name not in self._counters:
            self._counters[name] = Counter(name)
        self._counters[name].increment(labels or {})

    def set_gauge(
        self, name: str, value: float, labels: dict[str, str] | None = None
    ) -> None:
        """Set a gauge value.

        Args:
            name: Gauge name
            value: Value to set
            labels: Optional metric labels
        """
        if name not in self._gauges:
            self._gauges[name] = Gauge(name)
        self._gauges[name].set(value, labels or {})

    def observe(
        self, name: str, value: float, labels: dict[str, str] | None = None
    ) -> None:
        """Observe a histogram value.

        Args:
            name: Histogram name
            value: Value to observe
            labels: Optional metric labels
        """
        if name not in self._histograms:
            self._histograms[name] = Histogram(name)
        self._histograms[name].observe(value, labels or {})

    def get_metrics(self) -> dict[str, Any]:
        """Get all metrics.

        Returns:
            Dictionary of all metrics
        """
        metrics = {}

        # Add counters
        for name, counter in self._counters.items():
            metrics[name] = {
                "type": "counter",
                "value": counter.get_value(),
                "labels": counter.get_labels(),
            }

        # Add gauges
        for name, gauge in self._gauges.items():
            metrics[name] = {
                "type": "gauge",
                "value": gauge.get_value(),
                "labels": gauge.get_labels(),
            }

        # Add histograms
        for name, histogram in self._histograms.items():
            metrics[name] = {
                "type": "histogram",
                "value": histogram.get_value(),
                "labels": histogram.get_labels(),
            }

        return metrics


__all__ = ["MetricsCollector"]
