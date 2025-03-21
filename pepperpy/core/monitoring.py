"""Monitoring and metrics collection for PepperPy.
 
This module provides functionality for collecting and managing metrics
across the PepperPy framework, including performance metrics, usage
statistics, and system health information.
"""


import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class Metric:
    """A single metric measurement.

    Attributes:
        name: Name of the metric
        value: Value of the metric
        timestamp: When the metric was recorded
        tags: Optional tags for categorizing the metric
    """

    name: str
    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    tags: Dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """Collector for framework metrics.

    This class provides methods for collecting and managing various
    metrics across the PepperPy framework.
    """

    def __init__(self) -> None:
        """Initialize the metrics collector."""
        self._metrics: List[Metric] = []
        self._start_time = time.time()

    def record(self, name: str, value: float, **tags: str) -> None:
        """Record a metric.

        Args:
            name: Name of the metric
            value: Value of the metric
            **tags: Optional tags for categorizing the metric
        """
        metric = Metric(name=name, value=value, tags=tags)
        self._metrics.append(metric)
        logger.debug(f"Recorded metric: {metric}")

    def get_metrics(self, name: Optional[str] = None, **tags: str) -> List[Metric]:
        """Get recorded metrics.

        Args:
            name: Optional name to filter by
            **tags: Optional tags to filter by

        Returns:
            List of matching metrics
        """
        metrics = self._metrics
        if name:
            metrics = [m for m in metrics if m.name == name]
        if tags:
            metrics = [
                m for m in metrics if all(m.tags.get(k) == v for k, v in tags.items())
            ]
        return metrics

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of all metrics.

        Returns:
            Dictionary containing metric summaries
        """
        summary: Dict[str, Any] = {
            "total_metrics": len(self._metrics),
            "uptime": time.time() - self._start_time,
            "metrics_by_name": {},
        }

        for metric in self._metrics:
            if metric.name not in summary["metrics_by_name"]:
                summary["metrics_by_name"][metric.name] = {
                    "count": 0,
                    "total": 0.0,
                    "min": float("inf"),
                    "max": float("-inf"),
                }
            stats = summary["metrics_by_name"][metric.name]
            stats["count"] += 1
            stats["total"] += metric.value
            stats["min"] = min(stats["min"], metric.value)
            stats["max"] = max(stats["max"], metric.value)

        # Calculate averages
        for stats in summary["metrics_by_name"].values():
            stats["avg"] = stats["total"] / stats["count"]

        return summary
