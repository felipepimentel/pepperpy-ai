"""Common types used across the observability system.

This module defines the core types used throughout the observability system,
including metrics, logging, tracing, and health checks.

Example:
    >>> metric = Metric(
    ...     name="requests_total",
    ...     value=1.0,
    ...     type=MetricType.COUNTER,
    ...     timestamp=time.time(),
    ... )
    >>> assert metric.type == MetricType.COUNTER
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Union


class MetricType(Enum):
    """Types of metrics that can be collected.

    Attributes:
        COUNTER: A cumulative metric that only increases
        GAUGE: A metric that can increase and decrease
        HISTOGRAM: A metric that samples observations
        SUMMARY: A metric that samples observations with quantiles
    """

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class LogLevel(Enum):
    """Standard log levels.

    Attributes:
        DEBUG: Detailed information for debugging
        INFO: General information about system operation
        WARNING: Warning messages for potential issues
        ERROR: Error messages for actual problems
        CRITICAL: Critical messages requiring immediate attention
    """

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class HealthStatus(Enum):
    """Possible health check statuses.

    Attributes:
        HEALTHY: Component is functioning normally
        DEGRADED: Component is functioning but with issues
        UNHEALTHY: Component is not functioning properly
    """

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class Metric:
    """A single metric measurement.

    Attributes:
        name: Name of the metric
        value: Current value of the metric
        type: Type of metric (counter, gauge, etc.)
        timestamp: Unix timestamp when metric was recorded
        tags: Optional key-value pairs for categorization
        description: Optional description of the metric
    """

    name: str
    value: float
    type: MetricType
    timestamp: float
    tags: dict[str, str] | None = None
    description: str | None = None


@dataclass
class LogRecord:
    """A structured log record.

    Attributes:
        message: The log message
        level: Severity level of the log
        timestamp: Unix timestamp when log was created
        context: Structured context data
        trace_id: Optional ID linking to a trace
        span_id: Optional ID linking to a span
    """

    message: str
    level: LogLevel
    timestamp: float
    context: dict[str, Any]
    trace_id: str | None = None
    span_id: str | None = None


@dataclass
class Span:
    """A tracing span representing a unit of work.

    Attributes:
        name: Name of the operation being traced
        trace_id: ID of the trace this span belongs to
        span_id: Unique ID of this span
        parent_id: Optional ID of parent span
        start_time: Unix timestamp when span started
        end_time: Optional Unix timestamp when span ended
        attributes: Key-value pairs describing the span
        events: List of events that occurred during the span
    """

    name: str
    trace_id: str
    span_id: str
    parent_id: str | None
    start_time: float
    end_time: float | None = None
    attributes: dict[str, Any] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class HealthCheck:
    """Result of a health check.

    Attributes:
        name: Name of the component checked
        status: Current health status
        timestamp: Unix timestamp of the check
        details: Detailed health information
        dependencies: Optional list of dependency names
    """

    name: str
    status: HealthStatus
    timestamp: float
    details: dict[str, Any]
    dependencies: list[str] | None = None


# Type aliases
MetricValue = Union[int, float]
Tags = dict[str, str]
Context = dict[str, Any]
