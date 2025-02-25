"""Base classes for monitoring functionality."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from pepperpy.core.lifecycle import LifecycleComponent


class MonitoringExporter(LifecycleComponent, ABC):
    """Base class for monitoring exporters.

    This class defines the interface that all monitoring exporters must implement.
    Exporters are responsible for sending monitoring data (events and metrics) to
    external systems.
    """

    def __init__(self, name: str) -> None:
        """Initialize the exporter.

        Args:
            name: The name of the exporter.
        """
        super().__init__(name)

    @abstractmethod
    async def export_events(self, events: List[Dict[str, Any]]) -> None:
        """Export events to the external system.

        Args:
            events: The events to export.
        """
        pass

    @abstractmethod
    async def export_metrics(self, metrics: List[Dict[str, Any]]) -> None:
        """Export metrics to the external system.

        Args:
            metrics: The metrics to export.
        """
        pass

