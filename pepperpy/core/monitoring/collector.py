"""Collector functionality for monitoring.

This module provides the collector class for monitoring data.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from pepperpy.core.lifecycle import LifecycleComponent
from pepperpy.core.monitoring.errors import CollectorError
from pepperpy.core.monitoring.types import MonitoringEvent, MonitoringMetric


class MonitoringCollector(LifecycleComponent, ABC):
    """Base class for monitoring collectors."""

    def __init__(self, name: str = "monitoring_collector") -> None:
        """Initialize collector.

        Args:
            name: Collector name
        """
        super().__init__(name)
        self._events: list[MonitoringEvent] = []
        self._metrics: list[MonitoringMetric] = []

    @abstractmethod
    async def collect_events(self) -> AsyncIterator[MonitoringEvent]:
        """Collect monitoring events.

        Yields:
            MonitoringEvent: Collected events

        Raises:
            CollectorError: If collection fails
        """
        ...

    @abstractmethod
    async def collect_metrics(self) -> AsyncIterator[MonitoringMetric]:
        """Collect monitoring metrics.

        Yields:
            MonitoringMetric: Collected metrics

        Raises:
            CollectorError: If collection fails
        """
        ...

    async def initialize(self) -> None:
        """Initialize collector.

        Raises:
            CollectorError: If initialization fails
        """
        try:
            await self._initialize()
        except Exception as e:
            raise CollectorError(f"Failed to initialize collector: {e}")

    async def cleanup(self) -> None:
        """Clean up collector.

        Raises:
            CollectorError: If cleanup fails
        """
        try:
            await self._cleanup()
        except Exception as e:
            raise CollectorError(f"Failed to clean up collector: {e}")

    @abstractmethod
    async def _initialize(self) -> None:
        """Initialize collector implementation.

        Raises:
            CollectorError: If initialization fails
        """
        ...

    @abstractmethod
    async def _cleanup(self) -> None:
        """Clean up collector implementation.

        Raises:
            CollectorError: If cleanup fails
        """
        ...


__all__ = ["MonitoringCollector"]
