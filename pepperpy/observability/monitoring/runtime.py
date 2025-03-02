"""Runtime monitoring functionality for PepperPy.

This module provides functionality for monitoring runtime metrics and performance
of PepperPy components and operations.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class RuntimeMetrics:
    """Container for runtime metrics."""

    start_time: datetime
    end_time: Optional[datetime] = None
    memory_usage: float = 0.0
    cpu_usage: float = 0.0
    active_threads: int = 0
    error_count: int = 0
    warning_count: int = 0


class RuntimeMonitor:
    """Monitor runtime metrics and performance."""

    def __init__(self):
        self._metrics: Dict[str, RuntimeMetrics] = {}
        self._current_operation: Optional[str] = None

    def start_operation(self, operation_name: str) -> None:
        """Start monitoring a new operation."""
        self._metrics[operation_name] = RuntimeMetrics(start_time=datetime.now())
        self._current_operation = operation_name

    def end_operation(self, operation_name: str) -> None:
        """End monitoring for an operation."""
        if operation_name in self._metrics:
            self._metrics[operation_name].end_time = datetime.now()
            if self._current_operation == operation_name:
                self._current_operation = None

    def update_metrics(self, operation_name: str, metrics: Dict[str, Any]) -> None:
        """Update metrics for an operation."""
        if operation_name in self._metrics:
            for key, value in metrics.items():
                if hasattr(self._metrics[operation_name], key):
                    setattr(self._metrics[operation_name], key, value)

    def get_metrics(self, operation_name: str) -> Optional[RuntimeMetrics]:
        """Get metrics for a specific operation."""
        return self._metrics.get(operation_name)

    def get_all_metrics(self) -> Dict[str, RuntimeMetrics]:
        """Get all collected metrics."""
        return self._metrics.copy()

    def clear_metrics(self) -> None:
        """Clear all collected metrics."""
        self._metrics.clear()
        self._current_operation = None
