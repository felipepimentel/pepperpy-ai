"""@file: metrics.py
@purpose: Runtime metrics collection and management
@component: Runtime
@created: 2024-02-15
@task: TASK-003
@status: active
"""

import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from pepperpy.core.errors import ConfigurationError
from pepperpy.core.logging import get_logger
from pepperpy.core.types import JSON
from pepperpy.runtime.context import get_current_context
from pepperpy.runtime.lifecycle import get_lifecycle_manager

logger = get_logger(__name__)


@dataclass
class MetricsConfig:
    """Configuration for metrics collection."""

    enabled: bool = True
    batch_size: int = 100
    flush_interval: float = 60.0

    def validate(self) -> None:
        """Validate metrics configuration."""
        if self.batch_size < 1:
            raise ConfigurationError("Batch size must be positive")
        if self.flush_interval <= 0:
            raise ConfigurationError("Flush interval must be positive")


@dataclass
class Metrics:
    """Runtime metrics collection."""

    name: str
    value: float
    id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    tags: Dict[str, str] = field(default_factory=dict)

    def to_json(self) -> JSON:
        """Convert metrics to JSON format."""
        return {
            "id": str(self.id),
            "name": self.name,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "tags": self.tags,
        }


class MetricsManager:
    """Manager for runtime metrics."""

    def __init__(self, config: Optional[MetricsConfig] = None) -> None:
        """Initialize metrics manager.

        Args:
            config: Optional metrics configuration

        """
        self.config = config or MetricsConfig()
        self.config.validate()

        self._metrics: Dict[str, List[Metrics]] = {}
        self._lock = threading.Lock()
        self._lifecycle = get_lifecycle_manager().create(
            context=get_current_context(),
            metadata={"component": "metrics_manager"},
        )

    def record(
        self, name: str, value: float, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a metric.

        Args:
            name: Metric name
            value: Metric value
            tags: Optional metric tags

        """
        if not self.config.enabled:
            return

        metric = Metrics(name=name, value=value, tags=tags or {})
        with self._lock:
            if name not in self._metrics:
                self._metrics[name] = []
            self._metrics[name].append(metric)

            if len(self._metrics[name]) >= self.config.batch_size:
                self._flush_metrics(name)

    def get_metrics(self, name: str) -> List[Metrics]:
        """Get metrics by name.

        Args:
            name: Metric name

        Returns:
            List of metrics

        """
        with self._lock:
            return self._metrics.get(name, []).copy()

    def _flush_metrics(self, name: str) -> None:
        """Flush metrics for a given name.

        Args:
            name: Metric name to flush

        """
        with self._lock:
            metrics = self._metrics.get(name, [])
            if name in self._metrics:
                self._metrics[name] = []

        # Here you would typically send metrics to a monitoring system
        logger.debug(f"Flushing {len(metrics)} metrics for {name}")

    def cleanup(self) -> None:
        """Clean up metrics manager resources."""
        with self._lock:
            for name in list(self._metrics.keys()):
                self._flush_metrics(name)
            self._metrics.clear()
