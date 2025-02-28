"""Metrics management functionality for PepperPy observability.

This module provides centralized management of metrics collection and reporting.
"""

from typing import Dict, Optional

from pepperpy.common.base import Lifecycle
from pepperpy.core.types import ComponentState

from .collector import Metric, MetricsCollector, MetricsRegistry


class MetricsManager(Lifecycle):
    """Manager for metrics collection and reporting."""

    def __init__(self, config: Optional[Dict] = None):
        """Initialize metrics manager.

        Args:
            config: Optional configuration dictionary
        """
        super().__init__()
        self.config = config or {}
        self._registry = MetricsRegistry()

    async def initialize(self) -> None:
        """Initialize the metrics system."""
        try:
            # Initialize default collectors
            system_collector = self._registry.get_collector("system")
            if not system_collector:
                self._registry.register_collector("system", MetricsCollector())

            self._state = ComponentState.RUNNING
        except Exception as e:
            self._state = ComponentState.ERROR
            raise RuntimeError(f"Failed to initialize metrics manager: {str(e)}") from e

    async def cleanup(self) -> None:
        """Clean up the metrics system."""
        try:
            # Clear all metrics
            for collector_name in self._registry._collectors:
                collector = self._registry.get_collector(collector_name)
                if collector:
                    collector.clear_metrics()
            self._registry._default_collector.clear_metrics()

            self._state = ComponentState.UNREGISTERED
        except Exception as e:
            self._state = ComponentState.ERROR
            raise RuntimeError(f"Failed to cleanup metrics manager: {str(e)}") from e

    def record_metric(
        self, metric: Metric, collector_name: Optional[str] = None
    ) -> None:
        """Record a metric using the specified collector.

        Args:
            metric: The metric to record
            collector_name: Optional name of the collector to use
        """
        self._registry.record_metric(metric, collector_name)

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
