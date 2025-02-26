"""@file: manager.py
@purpose: Metrics manager for backward compatibility
@component: Core > Metrics
@created: 2024-03-21
@task: TASK-007-R060
@status: active
"""

from typing import Optional

from pepperpy.core.metrics.types import Counter, Gauge, Histogram


class MetricsManager:
    """Metrics manager for backward compatibility.

    This class provides compatibility with the old metrics manager interface
    while using the new metric classes internally.
    """

    _instance: Optional["MetricsManager"] = None

    def __init__(self) -> None:
        """Initialize metrics manager."""
        if MetricsManager._instance is not None:
            raise RuntimeError("Use get_instance() instead")
        self._counters: dict[str, Counter] = {}
        self._gauges: dict[str, Gauge] = {}
        self._histograms: dict[str, Histogram] = {}
        MetricsManager._instance = self

    @classmethod
    def get_instance(cls) -> "MetricsManager":
        """Get singleton instance.

        Returns:
            Singleton metrics manager instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def create_counter(
        self,
        name: str,
        description: str = "",
        labels: list[str] | None = None,
    ) -> Counter:
        """Create counter metric.

        Args:
            name: Metric name
            description: Metric description
            labels: Optional label names

        Returns:
            Counter metric
        """
        if name not in self._counters:
            self._counters[name] = Counter(
                name=name, description=description, labels=labels
            )
        return self._counters[name]

    async def create_gauge(
        self,
        name: str,
        description: str = "",
        labels: list[str] | None = None,
    ) -> Gauge:
        """Create gauge metric.

        Args:
            name: Metric name
            description: Metric description
            labels: Optional label names

        Returns:
            Gauge metric
        """
        if name not in self._gauges:
            self._gauges[name] = Gauge(
                name=name, description=description, labels=labels
            )
        return self._gauges[name]

    async def create_histogram(
        self,
        name: str,
        description: str = "",
        labels: list[str] | None = None,
        buckets: list[float] | None = None,
    ) -> Histogram:
        """Create histogram metric.

        Args:
            name: Metric name
            description: Metric description
            labels: Optional label names
            buckets: Optional bucket boundaries

        Returns:
            Histogram metric
        """
        if name not in self._histograms:
            self._histograms[name] = Histogram(
                name=name, description=description, labels=labels, buckets=buckets
            )
        return self._histograms[name]


# Singleton instance
metrics_manager = MetricsManager.get_instance()
