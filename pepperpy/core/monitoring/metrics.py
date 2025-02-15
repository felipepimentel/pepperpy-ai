"""Centralized metrics system.

This module provides a unified metrics interface with support for different metric
types, labels, and exporters. It integrates with the lifecycle system for proper
resource management.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from pepperpy.core.lifecycle import Lifecycle
from pepperpy.core.monitoring import get_logger
from pepperpy.core.monitoring.types import MetricType, MonitoringError

__all__ = [
    "Metric",
    "MetricsError",
    "MetricsManager",
    "metrics_manager",
]


class MetricsError(MonitoringError):
    """Error raised by metrics operations."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the error.

        Args:
            message: Error message
            details: Additional error details

        """
        super().__init__(message, "METRICS_ERROR", details)


@dataclass
class Metric:
    """Representation of a metric with metadata."""

    name: str
    type: MetricType
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    description: Optional[str] = None
    timestamp: Optional[float] = None


class MetricExporter(ABC):
    """Base class for metric exporters.

    Metric exporters are responsible for sending metrics to external systems
    like Prometheus, StatsD, or custom monitoring solutions.
    """

    @abstractmethod
    async def export(self, metric: Metric) -> None:
        """Export a metric to the target system.

        Args:
            metric: Metric to export

        Raises:
            MetricsError: If export fails

        """
        pass

    @abstractmethod
    async def flush(self) -> None:
        """Flush any buffered metrics.

        This should be called before shutdown to ensure all metrics are sent.

        Raises:
            MetricsError: If flush fails

        """
        pass


class MetricsManager(Lifecycle):
    """Central manager for metrics collection and export.

    This class provides a unified interface for recording metrics and managing
    their export to various monitoring systems.
    """

    def __init__(self) -> None:
        """Initialize the metrics manager."""
        super().__init__()
        self._metrics: Dict[str, Metric] = {}
        self._exporters: List[MetricExporter] = []
        self._logger = get_logger(__name__)

    async def initialize(self) -> None:
        """Initialize the metrics manager."""
        self._logger.info("Initializing metrics manager")

    async def cleanup(self) -> None:
        """Clean up metrics resources.

        This ensures all metrics are flushed before shutdown.
        """
        self._logger.info("Cleaning up metrics manager")
        for exporter in self._exporters:
            try:
                await exporter.flush()
            except Exception as e:
                self._logger.error(
                    "Failed to flush metrics",
                    exporter=exporter.__class__.__name__,
                    error=str(e),
                )
        self._metrics.clear()
        self._exporters.clear()

    def add_exporter(self, exporter: MetricExporter) -> None:
        """Add a metric exporter.

        Args:
            exporter: Exporter to add

        """
        self._exporters.append(exporter)
        self._logger.info(
            "Added metric exporter",
            exporter=exporter.__class__.__name__,
        )

    def remove_exporter(self, exporter: MetricExporter) -> None:
        """Remove a metric exporter.

        Args:
            exporter: Exporter to remove

        """
        if exporter in self._exporters:
            self._exporters.remove(exporter)
            self._logger.info(
                "Removed metric exporter",
                exporter=exporter.__class__.__name__,
            )

    async def record(
        self,
        name: str,
        value: float,
        type: MetricType,
        labels: Optional[Dict[str, str]] = None,
        description: Optional[str] = None,
    ) -> None:
        """Record a metric value.

        Args:
            name: Metric name
            value: Metric value
            type: Type of metric
            labels: Optional labels to attach
            description: Optional metric description

        Raises:
            ValueError: If metric name is invalid
            MetricsError: If recording fails

        """
        if not name:
            raise ValueError("Metric name cannot be empty")

        try:
            metric = Metric(
                name=name,
                type=type,
                value=value,
                labels=labels or {},
                description=description,
            )

            self._metrics[name] = metric
            self._logger.debug(
                "Recorded metric",
                metric_name=name,
                metric_value=value,
                metric_type=type.value,
            )

            # Export metric
            for exporter in self._exporters:
                try:
                    await exporter.export(metric)
                except Exception as e:
                    self._logger.error(
                        "Failed to export metric",
                        metric_name=name,
                        exporter=exporter.__class__.__name__,
                        error=str(e),
                    )
                    raise MetricsError(
                        f"Failed to export metric {name}",
                        {"error": str(e), "exporter": exporter.__class__.__name__},
                    ) from e

        except Exception as e:
            raise MetricsError(
                f"Failed to record metric {name}", {"error": str(e)}
            ) from e

    def get_metric(self, name: str) -> Optional[Metric]:
        """Get the current value of a metric.

        Args:
            name: Metric name

        Returns:
            Metric if found, None otherwise

        """
        return self._metrics.get(name)

    def get_all_metrics(self) -> Dict[str, Metric]:
        """Get all current metrics.

        Returns:
            Dictionary of metric names to metrics

        """
        return self._metrics.copy()


# Global metrics manager instance
metrics_manager = MetricsManager()


async def record_metric(
    name: str,
    value: float,
    type: MetricType,
    labels: Optional[Dict[str, str]] = None,
    description: Optional[str] = None,
) -> None:
    """Record a metric value using the global metrics manager.

    This is a convenience function that uses the global metrics manager.

    Args:
        name: Metric name
        value: Metric value
        type: Type of metric
        labels: Optional labels to attach
        description: Optional metric description

    Raises:
        ValueError: If metric name is invalid
        MetricsError: If recording fails

    """
    await metrics_manager.record(name, value, type, labels, description)
