"""System monitoring functionality for PepperPy.

This module provides functionality for monitoring system-level metrics and resources
used by PepperPy.
"""

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

import psutil


@dataclass
class SystemMetrics:
    """Container for system metrics."""

    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    network_io_counters: Dict[str, int]
    open_files: int
    open_connections: int


class SystemMonitor:
    """Monitor system-level metrics and resources."""

    def __init__(self):
        self._process = psutil.Process(os.getpid())
        self._last_metrics: Optional[SystemMetrics] = None

    def collect_metrics(self) -> SystemMetrics:
        """Collect current system metrics."""
        metrics = SystemMetrics(
            timestamp=datetime.now(),
            cpu_percent=self._process.cpu_percent(),
            memory_percent=self._process.memory_percent(),
            disk_usage_percent=psutil.disk_usage("/").percent,
            network_io_counters={
                "bytes_sent": psutil.net_io_counters().bytes_sent,
                "bytes_recv": psutil.net_io_counters().bytes_recv,
            },
            open_files=len(self._process.open_files()),
            open_connections=len(self._process.connections()),
        )
        self._last_metrics = metrics
        return metrics

    def get_last_metrics(self) -> Optional[SystemMetrics]:
        """Get the last collected metrics."""
        return self._last_metrics

    def get_resource_usage(self) -> Dict[str, Any]:
        """Get detailed resource usage information."""
        return {
            "cpu_times": self._process.cpu_times()._asdict(),
            "memory_info": self._process.memory_info()._asdict(),
            "io_counters": self._process.io_counters()._asdict()
            if hasattr(self._process, "io_counters")
            else {},
            "num_threads": self._process.num_threads(),
            "num_fds": self._process.num_fds()
            if hasattr(self._process, "num_fds")
            else None,
            "context_switches": self._process.num_ctx_switches()._asdict(),
        }

    def is_resource_critical(self) -> bool:
        """Check if any system resources are in a critical state."""
        if not self._last_metrics:
            return False

        return any([
            self._last_metrics.cpu_percent > 90,
            self._last_metrics.memory_percent > 90,
            self._last_metrics.disk_usage_percent > 95,
        ])
