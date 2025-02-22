"""Simple metrics collector implementation.

This module provides a simple metrics collector that writes metrics to a log file.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from pepperpy.core.errors import MonitoringError
from pepperpy.monitoring.base import MetricsCollector

logger = logging.getLogger(__name__)


class SimpleMetricsCollector(MetricsCollector):
    """Simple metrics collector that writes metrics to a log file.

    This collector writes metrics to a log file in JSON format.
    Each line in the log file represents a single metric export.

    Attributes:
        log_path: Path to the metrics log file
        metrics_interval: Interval in seconds between metrics exports
    """

    def __init__(
        self,
        log_path: Optional[str] = None,
        metrics_interval: float = 60.0,
    ) -> None:
        """Initialize simple metrics collector.

        Args:
            log_path: Optional path to metrics log file
            metrics_interval: Interval in seconds between metrics exports
        """
        super().__init__(metrics_interval=metrics_interval)

        # Use default log path if none provided
        if log_path is None:
            log_path = os.path.join(
                os.path.expanduser("~"),
                ".pepperpy",
                "metrics",
                "metrics.log",
            )

        self.log_path = Path(log_path)

    async def _initialize(self) -> None:
        """Initialize metrics collector.

        Creates the metrics log directory if it doesn't exist.

        Raises:
            MonitoringError: If initialization fails
        """
        try:
            # Create metrics directory if it doesn't exist
            self.log_path.parent.mkdir(parents=True, exist_ok=True)

            # Create empty log file if it doesn't exist
            if not self.log_path.exists():
                self.log_path.touch()

        except Exception as e:
            raise MonitoringError(f"Failed to initialize metrics log: {e}")

    async def _cleanup(self) -> None:
        """Clean up metrics collector.

        Nothing to clean up for this simple implementation.
        """
        pass

    async def export_metrics(self) -> None:
        """Export collected metrics to log file.

        Writes collected metrics to the log file in JSON format.
        Each line contains a timestamp and a list of metrics.

        Raises:
            MonitoringError: If export fails
        """
        if not self._metrics:
            return

        try:
            # Convert metrics to JSON format
            export_data: Dict[str, Any] = {
                "timestamp": datetime.now().isoformat(),
                "metrics": [
                    {
                        "name": metric.name,
                        "value": metric.value,
                        "timestamp": metric.timestamp,
                        "tags": metric.tags or {},
                    }
                    for metric in self._metrics
                ],
            }

            # Write metrics to log file
            with self.log_path.open("a") as f:
                json.dump(export_data, f)
                f.write("\n")

        except Exception as e:
            raise MonitoringError(f"Failed to export metrics: {e}")
