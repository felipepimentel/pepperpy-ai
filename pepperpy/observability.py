"""Observability module.

This module provides metrics tracking and monitoring capabilities.
"""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class MetricsManager:
    """Manager for metrics tracking.

    Provides a centralized way to track metrics across the application.
    Uses the singleton pattern to ensure a single instance.

    Example:
        >>> metrics = MetricsManager.get_instance()
        >>> metrics.increment("requests_total")
    """

    _instance: Optional["MetricsManager"] = None

    def __init__(self) -> None:
        """Initialize metrics manager."""
        if MetricsManager._instance is not None:
            raise RuntimeError("Use get_instance() to access MetricsManager")
        self._metrics: dict[str, int] = {}

    @classmethod
    def get_instance(cls) -> "MetricsManager":
        """Get the singleton instance.

        Returns:
            The MetricsManager instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def increment(self, metric: str, value: int = 1) -> None:
        """Increment a metric counter.

        Args:
            metric: Name of metric to increment
            value: Value to increment by
        """
        self._metrics[metric] = self._metrics.get(metric, 0) + value
        logger.debug("Metric %s = %d", metric, self._metrics[metric])

    def set(self, metric: str, value: Any) -> None:
        """Set a metric value.

        Args:
            metric: Name of metric to set
            value: Value to set
        """
        self._metrics[metric] = value
        logger.debug("Metric %s = %s", metric, value)

    def get(self, metric: str) -> Any:
        """Get a metric value.

        Args:
            metric: Name of metric to get

        Returns:
            Current metric value

        Raises:
            KeyError: If metric doesn't exist
        """
        return self._metrics[metric]
