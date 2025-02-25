"""Base exporter functionality for monitoring.

This module provides the base exporter class for monitoring data.
"""

from abc import ABC, abstractmethod

from pepperpy.core.lifecycle import LifecycleComponent
from pepperpy.core.monitoring.errors import ExporterError
from pepperpy.core.monitoring.types import MonitoringEvent, MonitoringMetric


class MonitoringExporter(LifecycleComponent, ABC):
    """Base class for monitoring exporters."""

    def __init__(self, name: str = "monitoring_exporter") -> None:
        """Initialize exporter.

        Args:
            name: Exporter name
        """
        super().__init__(name)
        self._events: list[MonitoringEvent] = []
        self._metrics: list[MonitoringMetric] = []

    @abstractmethod
    async def export_events(self, events: list[MonitoringEvent]) -> None:
        """Export monitoring events.

        Args:
            events: Events to export

        Raises:
            ExporterError: If export fails
        """
        ...

    @abstractmethod
    async def export_metrics(self, metrics: list[MonitoringMetric]) -> None:
        """Export monitoring metrics.

        Args:
            metrics: Metrics to export

        Raises:
            ExporterError: If export fails
        """
        ...

    async def initialize(self) -> None:
        """Initialize exporter.

        Raises:
            ExporterError: If initialization fails
        """
        try:
            await self._initialize()
        except Exception as e:
            raise ExporterError(f"Failed to initialize exporter: {e}")

    async def cleanup(self) -> None:
        """Clean up exporter.

        Raises:
            ExporterError: If cleanup fails
        """
        try:
            await self._cleanup()
        except Exception as e:
            raise ExporterError(f"Failed to clean up exporter: {e}")

    @abstractmethod
    async def _initialize(self) -> None:
        """Initialize exporter implementation.

        Raises:
            ExporterError: If initialization fails
        """
        ...

    @abstractmethod
    async def _cleanup(self) -> None:
        """Clean up exporter implementation.

        Raises:
            ExporterError: If cleanup fails
        """
        ...


__all__ = ["MonitoringExporter"]
