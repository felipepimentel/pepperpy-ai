"""@file: monitor.py
@purpose: Runtime monitoring system core functionality
@component: Runtime
@created: 2024-02-15
@task: TASK-003
@status: active
"""

import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from uuid import UUID

from pepperpy.core.logging import get_logger
from pepperpy.runtime.context import get_current_context
from pepperpy.runtime.lifecycle import get_lifecycle_manager
from pepperpy.runtime.monitoring.metrics import Metrics, MetricsConfig
from pepperpy.runtime.monitoring.tracing import Tracer, TracingConfig

logger = get_logger(__name__)


@dataclass
class MonitoringConfig:
    """Configuration for runtime monitoring."""

    metrics: MetricsConfig = field(default_factory=MetricsConfig)
    tracing: TracingConfig = field(default_factory=TracingConfig)
    enabled: bool = True

    def validate(self) -> None:
        """Validate monitoring configuration."""
        self.metrics.validate()
        self.tracing.validate()


class Monitor:
    """Runtime monitoring system."""

    def __init__(self, config: Optional[MonitoringConfig] = None) -> None:
        """Initialize monitor.

        Args:
            config: Optional monitoring configuration

        """
        self.config = config or MonitoringConfig()
        self.config.validate()

        self._metrics: List[Metrics] = []
        self._tracers: Dict[UUID, Tracer] = {}
        self._lock = threading.Lock()
        self._lifecycle = get_lifecycle_manager().create(
            context=get_current_context(),
            metadata={"component": "monitor"},
        )

    def record_metric(
        self, name: str, value: float, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a metric.

        Args:
            name: Metric name
            value: Metric value
            tags: Optional metric tags

        """
        if not self.config.metrics.enabled:
            return

        metric = Metrics(name=name, value=value, tags=tags or {})
        with self._lock:
            self._metrics.append(metric)

            if len(self._metrics) >= self.config.metrics.batch_size:
                self._flush_metrics()

    def _flush_metrics(self) -> None:
        """Flush metrics to storage."""
        with self._lock:
            if not self._metrics:
                return

            # TODO: Implement metrics storage
            self._metrics.clear()

    def start_trace(
        self,
        name: str,
        parent_id: Optional[UUID] = None,
        attributes: Optional[Dict[str, str]] = None,
    ) -> Tracer:
        """Start a new trace span.

        Args:
            name: Trace name
            parent_id: Optional parent trace ID
            attributes: Optional trace attributes

        Returns:
            Created tracer instance

        """
        if not self.config.tracing.enabled:
            return Tracer(name=name)  # Return dummy tracer when disabled

        tracer = Tracer(
            name=name,
            parent_id=parent_id,
            attributes=attributes or {},
        )
        with self._lock:
            self._tracers[tracer.id] = tracer
        return tracer

    def end_trace(self, tracer_id: UUID) -> None:
        """End a trace span.

        Args:
            tracer_id: Tracer ID to end

        """
        with self._lock:
            if tracer_id in self._tracers:
                tracer = self._tracers[tracer_id]
                tracer.end()
                # TODO: Implement trace storage
                del self._tracers[tracer_id]


# Global monitor instance
_monitor = Monitor()


def get_monitor() -> Monitor:
    """Get the global monitor instance.

    Returns:
        Global monitor instance

    """
    return _monitor
