"""Unified metrics management for the Pepperpy framework.

This module provides a unified interface for managing metrics across the framework.
"""

from typing import Any, Optional

from pepperpy.core.lifecycle import LifecycleComponent
from pepperpy.core.types.states import ComponentState
from pepperpy.monitoring.logging import get_logger


class MetricsManager(LifecycleComponent):
    """Unified metrics manager.

    This class provides a centralized way to manage metrics across the framework.
    It follows the singleton pattern to ensure only one instance exists.
    """

    _instance: Optional["MetricsManager"] = None

    def __init__(self) -> None:
        """Initialize the metrics manager."""
        super().__init__("metrics_manager")
        self._metrics: dict[str, list[dict[str, Any]]] = {}
        self._state = ComponentState.UNREGISTERED
        self._logger = get_logger(__name__)

    @classmethod
    def get_instance(cls) -> "MetricsManager":
        """Get the singleton instance.

        Returns:
            MetricsManager: The singleton instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def _initialize(self) -> None:
        """Initialize the metrics manager."""
        try:
            self._state = ComponentState.RUNNING
            self._logger.info("Metrics manager initialized")
        except Exception as e:
            self._state = ComponentState.ERROR
            self._logger.error(f"Failed to initialize metrics manager: {e}")
            raise

    async def _cleanup(self) -> None:
        """Clean up the metrics manager."""
        try:
            self._metrics.clear()
            self._state = ComponentState.CLEANED
            self._logger.info("Metrics manager cleaned up")
        except Exception as e:
            self._logger.error(f"Failed to cleanup metrics manager: {e}")
            raise

    def record_metric(
        self, name: str, value: float, labels: dict[str, str] | None = None
    ) -> None:
        """Record a metric value.

        Args:
            name: Metric name
            value: Metric value
            labels: Optional metric labels
        """
        if labels is None:
            labels = {}

        if name not in self._metrics:
            self._metrics[name] = []

        self._metrics[name].append({"value": value, "labels": labels})

    def get_metrics(self) -> dict[str, list[dict[str, Any]]]:
        """Get all recorded metrics.

        Returns:
            dict[str, list[dict[str, Any]]]: Recorded metrics
        """
        return self._metrics

    def clear_metrics(self) -> None:
        """Clear all recorded metrics."""
        self._metrics.clear()


__all__ = ["MetricsManager"]
