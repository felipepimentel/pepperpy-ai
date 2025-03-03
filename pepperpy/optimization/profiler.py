"""Resource usage monitoring and profiling."""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .base import OptimizationComponent


@dataclass
class ResourceMetrics:
    """Resource usage metrics."""

    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    memory_used: int = 0
    memory_available: int = 0
    io_read_bytes: int = 0
    io_write_bytes: int = 0
    network_sent_bytes: int = 0
    network_recv_bytes: int = 0
    timestamp: float = field(default_factory=time.time)


@dataclass
class OperationMetrics:
    """Operation performance metrics."""

    operation: str
    duration_ms: float
    success: bool
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class ResourceProfiler(OptimizationComponent):
    """Monitors system resource usage."""

    def __init__(self, interval: float = 1.0):
        self._name = "resource_profiler"
        self._enabled = True
        self._interval = interval
        self._metrics: List[ResourceMetrics] = []
        self._task: Optional[asyncio.Task] = None

    @property
    def name(self) -> str:
        """Get profiler name."""
        return self._name

    @property
    def enabled(self) -> bool:
        """Check if profiler is enabled."""
        return self._enabled

    @property
    def metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        if not self._metrics:
            return {}

        latest = self._metrics[-1]
        return {
            "cpu_percent": latest.cpu_percent,
            "memory_percent": latest.memory_percent,
            "memory_used": latest.memory_used,
            "memory_available": latest.memory_available,
            "io_read_bytes": latest.io_read_bytes,
            "io_write_bytes": latest.io_write_bytes,
            "network_sent_bytes": latest.network_sent_bytes,
            "network_recv_bytes": latest.network_recv_bytes,
        }

    async def start(self):
        """Start resource monitoring."""
        if self._task is None:
            self._task = asyncio.create_task(self._monitor())

    async def stop(self):
        """Stop resource monitoring."""
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _monitor(self):
        """Monitor resource usage periodically."""
        while True:
            try:
                metrics = await self._collect_metrics()
                self._metrics.append(metrics)

                # Keep only last hour of metrics
                cutoff = time.time() - 3600
                self._metrics = [m for m in self._metrics if m.timestamp > cutoff]

                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error collecting metrics: {e}")
                await asyncio.sleep(self._interval)

    async def _collect_metrics(self) -> ResourceMetrics:
        """Collect current resource metrics."""
        # This is a placeholder implementation
        # In practice, you would use psutil or similar to get real metrics
        return ResourceMetrics(
            cpu_percent=0.0,
            memory_percent=0.0,
            memory_used=0,
            memory_available=0,
            io_read_bytes=0,
            io_write_bytes=0,
            network_sent_bytes=0,
            network_recv_bytes=0,
        )


class OperationProfiler(OptimizationComponent):
    """Profiles individual operations."""

    def __init__(self, max_history: int = 1000):
        self._name = "operation_profiler"
        self._enabled = True
        self._max_history = max_history
        self._operations: List[OperationMetrics] = []

    @property
    def name(self) -> str:
        """Get profiler name."""
        return self._name

    @property
    def enabled(self) -> bool:
        """Check if profiler is enabled."""
        return self._enabled

    @property
    def metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        if not self._operations:
            return {}

        # Calculate average duration and success rate per operation
        stats: Dict[str, Dict[str, Any]] = {}
        for op in self._operations:
            if op.operation not in stats:
                stats[op.operation] = {
                    "count": 0,
                    "success_count": 0,
                    "total_duration": 0.0,
                }

            s = stats[op.operation]
            s["count"] += 1
            if op.success:
                s["success_count"] += 1
            s["total_duration"] += op.duration_ms

        return {
            op: {
                "avg_duration_ms": s["total_duration"] / s["count"],
                "success_rate": s["success_count"] / s["count"],
                "count": s["count"],
            }
            for op, s in stats.items()
        }

    def record_operation(
        self,
        operation: str,
        duration_ms: float,
        success: bool,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Record an operation's metrics."""
        self._operations.append(
            OperationMetrics(
                operation=operation,
                duration_ms=duration_ms,
                success=success,
                error=error,
                metadata=metadata or {},
            ),
        )

        # Trim history if needed
        if len(self._operations) > self._max_history:
            self._operations = self._operations[-self._max_history :]

    def get_operation_history(
        self, operation: Optional[str] = None,
    ) -> List[OperationMetrics]:
        """Get operation history, optionally filtered by operation type."""
        if operation:
            return [op for op in self._operations if op.operation == operation]
        return self._operations.copy()

    def clear_history(self):
        """Clear operation history."""
        self._operations.clear()
