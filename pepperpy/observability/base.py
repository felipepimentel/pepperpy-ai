"""Base monitoring functionality.

This module provides base classes and utilities for monitoring and metrics collection,
including metrics recording, aggregation, and export capabilities.
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional

from pepperpy.core.errors import MonitoringError

logger = logging.getLogger(__name__)


@dataclass
class Metric:
    """Represents a single metric measurement.

    Attributes:
        name: Name of the metric
        value: Metric value
        timestamp: Unix timestamp when metric was recorded
        tags: Optional tags for metric categorization
    """

    name: str
    value: float
    timestamp: float
    tags: Optional[Dict[str, str]] = None


class MetricsCollector(ABC):
    """Base class for metrics collection.

    This class defines the interface that all metrics collectors must implement.
    It provides methods for recording, aggregating, and exporting metrics.

    Attributes:
        metrics_interval: Interval in seconds between metrics exports
        _metrics: List of collected metrics
        _export_task: Optional background task for metrics export
        _initialized: Whether the collector has been initialized
    """

    def __init__(
        self,
        metrics_interval: float = 60.0,
    ) -> None:
        """Initialize metrics collector.

        Args:
            metrics_interval: Interval in seconds between metrics exports
        """
        self.metrics_interval = metrics_interval
        self._metrics: List[Metric] = []
        self._export_task = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize metrics collector.

        This method must be called before using the collector.
        It will initialize any required resources and start background tasks.

        Raises:
            MonitoringError: If initialization fails
        """
        if self._initialized:
            return

        try:
            await self._initialize()
            self._initialized = True

            # Start metrics export task
            self._export_task = asyncio.create_task(self._run_export())
        except Exception as e:
            raise MonitoringError(f"Failed to initialize metrics collector: {e}")

    async def cleanup(self) -> None:
        """Clean up metrics collector.

        This method must be called when the collector is no longer needed.
        It will clean up any allocated resources and stop background tasks.

        Raises:
            MonitoringError: If cleanup fails
        """
        if not self._initialized:
            return

        try:
            # Stop metrics export task
            if self._export_task:
                self._export_task.cancel()
                await self._export_task

            await self._cleanup()
            self._initialized = False
        except Exception as e:
            raise MonitoringError(f"Failed to clean up metrics collector: {e}")

    @abstractmethod
    async def _initialize(self) -> None:
        """Initialize metrics collector implementation.

        This method must be implemented by subclasses to perform
        collector-specific initialization.

        Raises:
            MonitoringError: If initialization fails
        """
        pass

    @abstractmethod
    async def _cleanup(self) -> None:
        """Clean up metrics collector implementation.

        This method must be implemented by subclasses to perform
        collector-specific cleanup.

        Raises:
            MonitoringError: If cleanup fails
        """
        pass

    async def record_metric(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None,
    ) -> None:
        """Record a metric measurement.

        Args:
            name: Name of the metric
            value: Metric value
            tags: Optional tags for metric categorization

        Raises:
            MonitoringError: If recording fails
        """
        if not self._initialized:
            raise MonitoringError("Metrics collector not initialized")

        try:
            metric = Metric(
                name=name,
                value=value,
                timestamp=time.time(),
                tags=tags,
            )
            self._metrics.append(metric)
        except Exception as e:
            raise MonitoringError(f"Failed to record metric: {e}")

    @abstractmethod
    async def export_metrics(self) -> None:
        """Export collected metrics.

        This method must be implemented by subclasses to export
        collected metrics to their destination.

        Raises:
            MonitoringError: If export fails
        """
        pass

    async def _run_export(self) -> None:
        """Run automatic metrics export task.

        This method runs in the background to periodically export
        collected metrics.
        """
        while True:
            try:
                await asyncio.sleep(self.metrics_interval)
                await self.export_metrics()
                self._metrics.clear()
            except Exception as e:
                logger.error(f"Metrics export failed: {e}")
