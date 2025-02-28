"""Analysis metrics functionality for PepperPy.

This module provides functionality for collecting and managing metrics
related to various types of analysis within PepperPy.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from pepperpy.common.base import Lifecycle
from pepperpy.core.types import ComponentState


@dataclass
class AnalysisMetric:
    """Container for an analysis metric."""

    name: str
    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    labels: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class AnalysisMetrics(Lifecycle):
    """Manager for analysis-related metrics."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize analysis metrics.

        Args:
            config: Optional configuration dictionary
        """
        super().__init__()
        self.config = config or {}
        self._metrics: Dict[str, List[AnalysisMetric]] = {}

    async def initialize(self) -> None:
        """Initialize the metrics system."""
        try:
            # Initialize metric categories
            self._metrics.clear()
            self._state = ComponentState.RUNNING
        except Exception as e:
            self._state = ComponentState.ERROR
            raise RuntimeError(
                f"Failed to initialize analysis metrics: {str(e)}"
            ) from e

    async def cleanup(self) -> None:
        """Clean up the metrics system."""
        try:
            self._metrics.clear()
            self._state = ComponentState.UNREGISTERED
        except Exception as e:
            self._state = ComponentState.ERROR
            raise RuntimeError(f"Failed to cleanup analysis metrics: {str(e)}") from e

    def record_metric(self, metric: AnalysisMetric) -> None:
        """Record a new analysis metric.

        Args:
            metric: The metric to record
        """
        if metric.name not in self._metrics:
            self._metrics[metric.name] = []
        self._metrics[metric.name].append(metric)

    def get_metric(self, name: str) -> List[AnalysisMetric]:
        """Get all recorded values for a specific metric.

        Args:
            name: Name of the metric to retrieve

        Returns:
            List of recorded metric values
        """
        return self._metrics.get(name, []).copy()

    def get_latest_metric(self, name: str) -> Optional[AnalysisMetric]:
        """Get the most recent value for a specific metric.

        Args:
            name: Name of the metric to retrieve

        Returns:
            Most recent metric value if available
        """
        metrics = self._metrics.get(name, [])
        return metrics[-1] if metrics else None

    def get_all_metrics(self) -> Dict[str, List[AnalysisMetric]]:
        """Get all recorded metrics.

        Returns:
            Dictionary mapping metric names to their recorded values
        """
        return {name: metrics.copy() for name, metrics in self._metrics.items()}

    def clear_metrics(self) -> None:
        """Clear all recorded metrics."""
        self._metrics.clear()
