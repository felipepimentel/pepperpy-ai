"""Metrics management functionality for PepperPy observability.

This module provides centralized management of metrics collection and reporting.
"""

from typing import Dict, Optional

from pepperpy.core.metrics import MetricsCollector, MetricsRegistry


class MetricsManager:
    """Manager for metrics collection and reporting."""

    def __init__(self, config: Optional[Dict] = None):
        """Initialize metrics manager.

        Args:
            config: Optional configuration dictionary

        """
        self.config = config or {}
        self._registry = MetricsRegistry()
        self._state = "INITIALIZED"

    async def initialize(self) -> None:
        """Initialize the metrics system."""
        try:
            # Initialize default collectors
            system_collector = self._registry.get_collector("system")
            if not system_collector:
                self._registry.register_collector("system", MetricsCollector())

            self._state = "READY"
        except Exception as e:
            self._state = "ERROR"
            raise RuntimeError(f"Failed to initialize metrics manager: {e!s}") from e

    async def cleanup(self) -> None:
        """Clean up the metrics system."""
        try:
            # Clear all metrics
            for collector_name in list(self._registry._collectors.keys()):
                collector = self._registry.get_collector(collector_name)
                if collector:
                    collector.clear_metrics()

            self._state = "CLEANED"
        except Exception as e:
            self._state = "ERROR"
            raise RuntimeError(f"Failed to cleanup metrics manager: {e!s}") from e

    def get_registry(self) -> MetricsRegistry:
        """Get the metrics registry.

        Returns:
            Metrics registry

        """
        return self._registry

    def get_collector(self, name: str) -> Optional[MetricsCollector]:
        """Get a metrics collector by name.

        Args:
            name: Collector name

        Returns:
            Metrics collector, or None if not found

        """
        return self._registry.get_collector(name)

    def register_collector(self, name: str, collector: MetricsCollector) -> None:
        """Register a metrics collector.

        Args:
            name: Collector name
            collector: Metrics collector

        """
        self._registry.register_collector(name, collector)

    def get_metrics(self, collector_name: Optional[str] = None) -> Dict:
        """Get metrics from the specified collector.

        Args:
            collector_name: Optional name of the collector to get metrics from

        Returns:
            Dict containing the requested metrics

        """
        if collector_name:
            collector = self._registry.get_collector(collector_name)
            if collector:
                return collector.get_all_metrics()
            return {}
        return self._registry.get_all_metrics()
