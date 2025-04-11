"""Metrics collection for workflow operations."""

import asyncio
import json
import statistics
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class OperationMetrics:
    """Metrics for a specific operation type."""

    operation_type: str
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_duration: float = 0.0
    durations: list[float] = field(default_factory=list)
    errors: dict[str, int] = field(default_factory=dict)
    last_error: str | None = None
    last_error_time: datetime | None = None

    @property
    def error_rate(self) -> float:
        """Calculate error rate."""
        return self.failed_calls / self.total_calls if self.total_calls > 0 else 0.0

    @property
    def avg_duration(self) -> float:
        """Calculate average duration."""
        return statistics.mean(self.durations) if self.durations else 0.0

    @property
    def p95_duration(self) -> float:
        """Calculate 95th percentile duration."""
        return (
            statistics.quantiles(self.durations, n=20)[-1]
            if len(self.durations) >= 20
            else 0.0
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert metrics to dict."""
        return {
            "operation_type": self.operation_type,
            "total_calls": self.total_calls,
            "successful_calls": self.successful_calls,
            "failed_calls": self.failed_calls,
            "error_rate": self.error_rate,
            "avg_duration": self.avg_duration,
            "p95_duration": self.p95_duration,
            "errors": self.errors,
            "last_error": self.last_error,
            "last_error_time": self.last_error_time.isoformat()
            if self.last_error_time
            else None,
        }


class MetricsCollector:
    """Collects and manages workflow metrics."""

    def __init__(self, storage_path: str = "/tmp/workflow_metrics"):
        self.storage_path = storage_path
        self._metrics: dict[str, OperationMetrics] = {}
        self._lock = asyncio.Lock()

    async def record_operation(
        self,
        operation_type: str,
        duration: float,
        success: bool,
        error: Exception | None = None,
    ) -> None:
        """Record operation metrics."""
        async with self._lock:
            if operation_type not in self._metrics:
                self._metrics[operation_type] = OperationMetrics(operation_type)

            metrics = self._metrics[operation_type]
            metrics.total_calls += 1
            metrics.total_duration += duration
            metrics.durations.append(duration)

            if success:
                metrics.successful_calls += 1
            else:
                metrics.failed_calls += 1
                if error:
                    error_type = type(error).__name__
                    metrics.errors[error_type] = metrics.errors.get(error_type, 0) + 1
                    metrics.last_error = str(error)
                    metrics.last_error_time = datetime.utcnow()

            # Keep only last 1000 durations to prevent memory growth
            if len(metrics.durations) > 1000:
                metrics.durations = metrics.durations[-1000:]

            await self._persist_metrics()

    async def get_metrics(self, operation_type: str) -> OperationMetrics | None:
        """Get metrics for operation type."""
        return self._metrics.get(operation_type)

    async def get_all_metrics(self) -> dict[str, dict[str, Any]]:
        """Get all metrics as dict."""
        return {op: metrics.to_dict() for op, metrics in self._metrics.items()}

    async def _persist_metrics(self) -> None:
        """Persist metrics to storage."""
        import os

        os.makedirs(self.storage_path, exist_ok=True)

        path = f"{self.storage_path}/metrics.json"
        async with self._lock:
            with open(path, "w") as f:
                json.dump(await self.get_all_metrics(), f, indent=2)

    async def load_metrics(self) -> None:
        """Load metrics from storage."""
        path = f"{self.storage_path}/metrics.json"
        try:
            with open(path) as f:
                data = json.load(f)
                for op_type, metrics_dict in data.items():
                    metrics = OperationMetrics(op_type)
                    metrics.total_calls = metrics_dict["total_calls"]
                    metrics.successful_calls = metrics_dict["successful_calls"]
                    metrics.failed_calls = metrics_dict["failed_calls"]
                    metrics.total_duration = (
                        metrics_dict["avg_duration"] * metrics_dict["total_calls"]
                    )
                    metrics.errors = metrics_dict["errors"]
                    metrics.last_error = metrics_dict["last_error"]
                    if metrics_dict["last_error_time"]:
                        metrics.last_error_time = datetime.fromisoformat(
                            metrics_dict["last_error_time"]
                        )
                    self._metrics[op_type] = metrics
        except FileNotFoundError:
            pass  # No metrics file yet
