"""Interfaces base para o sistema de observabilidade

Este módulo define as interfaces e classes base para o sistema de observabilidade,
fornecendo:

- Métricas e telemetria
- Tracing distribuído
- Logging estruturado
- Monitoramento de saúde
- Alertas e notificações
- Dashboards e visualizações

O sistema de observabilidade é essencial para:
- Monitorar o comportamento do sistema
- Diagnosticar problemas
- Otimizar performance
- Garantir confiabilidade
- Manter segurança
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


class Metric:
    """Base class for metrics."""

    def __init__(self, name: str, description: str = ""):
        self.id = uuid4()
        self.name = name
        self.description = description
        self.created_at = datetime.utcnow()


class Counter(Metric):
    """Metric that represents a cumulative value."""

    def __init__(self, name: str, description: str = ""):
        super().__init__(name, description)
        self._value = 0

    def increment(self, value: int = 1) -> None:
        """Increment the counter by a value."""
        self._value += value

    @property
    def value(self) -> int:
        """Get the current value."""
        return self._value


class Gauge(Metric):
    """Metric that represents a value that can go up and down."""

    def __init__(self, name: str, description: str = ""):
        super().__init__(name, description)
        self._value = 0.0

    def set(self, value: float) -> None:
        """Set the gauge to a value."""
        self._value = value

    def increment(self, value: float = 1.0) -> None:
        """Increment the gauge by a value."""
        self._value += value

    def decrement(self, value: float = 1.0) -> None:
        """Decrement the gauge by a value."""
        self._value -= value

    @property
    def value(self) -> float:
        """Get the current value."""
        return self._value


class Histogram(Metric):
    """Metric that samples observations and counts them in configurable buckets."""

    def __init__(self, name: str, buckets: List[float], description: str = ""):
        super().__init__(name, description)
        self.buckets = sorted(buckets)
        self._counts = {b: 0 for b in buckets}
        self._sum = 0.0
        self._count = 0

    def observe(self, value: float) -> None:
        """Record an observation."""
        self._sum += value
        self._count += 1

        for bucket in self.buckets:
            if value <= bucket:
                self._counts[bucket] += 1

    @property
    def counts(self) -> Dict[float, int]:
        """Get the current bucket counts."""
        return self._counts.copy()

    @property
    def sum(self) -> float:
        """Get the sum of all observations."""
        return self._sum

    @property
    def count(self) -> int:
        """Get the total number of observations."""
        return self._count


class Span:
    """Represents a span in a trace."""

    def __init__(self, name: str, parent: Optional["Span"] = None):
        self.id = uuid4()
        self.name = name
        self.parent = parent
        self.start_time = datetime.utcnow()
        self.end_time: Optional[datetime] = None
        self.attributes: Dict[str, Any] = {}
        self.events: List[Dict[str, Any]] = []

    def set_attribute(self, key: str, value: Any) -> None:
        """Set a span attribute."""
        self.attributes[key] = value

    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
        """Add an event to the span."""
        self.events.append({
            "name": name,
            "timestamp": datetime.utcnow(),
            "attributes": attributes or {},
        })

    def end(self) -> None:
        """End the span."""
        self.end_time = datetime.utcnow()


class Tracer:
    """Utility for creating and managing traces."""

    def __init__(self):
        self._active_span: Optional[Span] = None

    def start_span(self, name: str) -> Span:
        """Start a new span."""
        span = Span(name, parent=self._active_span)
        self._active_span = span
        return span

    def end_span(self) -> None:
        """End the current span."""
        if self._active_span:
            self._active_span.end()
            self._active_span = self._active_span.parent


class MetricsCollector:
    """Collector for metrics."""

    def __init__(self):
        self._metrics: Dict[UUID, Metric] = {}

    def register(self, metric: Metric) -> None:
        """Register a metric."""
        self._metrics[metric.id] = metric

    def unregister(self, metric: Metric) -> None:
        """Unregister a metric."""
        if metric.id in self._metrics:
            del self._metrics[metric.id]

    def get(self, metric_id: UUID) -> Optional[Metric]:
        """Get a metric by ID."""
        return self._metrics.get(metric_id)

    def collect(self) -> Dict[str, Any]:
        """Collect all metric values."""
        result = {}
        for metric in self._metrics.values():
            if isinstance(metric, (Counter, Gauge)):
                result[metric.name] = metric.value
            elif isinstance(metric, Histogram):
                result[metric.name] = {
                    "counts": metric.counts,
                    "sum": metric.sum,
                    "count": metric.count,
                }
        return result


class ObservabilityManager:
    """Manager for observability features."""

    def __init__(self):
        self.metrics = MetricsCollector()
        self.tracer = Tracer()

    def create_counter(self, name: str, description: str = "") -> Counter:
        """Create and register a new counter."""
        counter = Counter(name, description)
        self.metrics.register(counter)
        return counter

    def create_gauge(self, name: str, description: str = "") -> Gauge:
        """Create and register a new gauge."""
        gauge = Gauge(name, description)
        self.metrics.register(gauge)
        return gauge

    def create_histogram(
        self, name: str, buckets: List[float], description: str = ""
    ) -> Histogram:
        """Create and register a new histogram."""
        histogram = Histogram(name, buckets, description)
        self.metrics.register(histogram)
        return histogram

    def start_trace(self, name: str) -> Span:
        """Start a new trace."""
        return self.tracer.start_span(name)

    def end_trace(self) -> None:
        """End the current trace."""
        self.tracer.end_span()


def create_observability_manager() -> ObservabilityManager:
    """Create and configure a new observability manager instance."""
    return ObservabilityManager()


# Export all types
__all__ = [
    "Metric",
    "Counter",
    "Gauge",
    "Histogram",
    "Span",
    "Tracer",
    "MetricsCollector",
    "ObservabilityManager",
    "create_observability_manager",
]
