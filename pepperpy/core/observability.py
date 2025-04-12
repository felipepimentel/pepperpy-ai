"""
PepperPy Observability Module.

Provides instrumentation, metrics, and tracing for PepperPy.
"""

import functools
import time
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from enum import Enum
from typing import Any, TypeVar, cast

from pepperpy.core.base import PepperpyError
from pepperpy.core.context import execution_context, get_current_context
from pepperpy.core.logging import get_logger

logger = get_logger(__name__)

# Type variables for generic functions
T = TypeVar("T")
R = TypeVar("R")


class ObservabilityError(PepperpyError):
    """Error related to observability operations."""

    pass


class MetricType(str, Enum):
    """Types of metrics."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class Metric:
    """Metric for observability."""

    def __init__(
        self,
        name: str,
        type: MetricType,
        description: str = "",
        labels: dict[str, str] | None = None,
    ):
        """Initialize a metric.

        Args:
            name: Metric name
            type: Metric type
            description: Metric description
            labels: Metric labels
        """
        self.name = name
        self.type = type
        self.description = description
        self.labels = labels or {}
        
        # Initialize value based on metric type
        if type in {MetricType.GAUGE, MetricType.COUNTER}:
            self.value: float | list[float] = 0.0
        else:
            self.value = []

    def increment(
        self, value: float = 1.0, labels: dict[str, str] | None = None
    ) -> None:
        """Increment a counter metric.

        Args:
            value: Value to increment by
            labels: Additional labels for this observation
        """
        if self.type != MetricType.COUNTER:
            raise ObservabilityError(f"Cannot increment metric of type {self.type}")
        
        # Type checking to satisfy mypy
        if isinstance(self.value, float):
            self.value += value
        
        # Log the metric
        combined_labels = {**self.labels, **(labels or {})}
        label_str = ", ".join(f"{k}={v}" for k, v in combined_labels.items())
        logger.debug(f"METRIC: {self.name}={self.value} ({label_str})")

    def set(self, value: float, labels: dict[str, str] | None = None) -> None:
        """Set a gauge metric.

        Args:
            value: Value to set
            labels: Additional labels for this observation
        """
        if self.type != MetricType.GAUGE:
            raise ObservabilityError(f"Cannot set metric of type {self.type}")
        
        # Assign the value directly
        self.value = value
        
        # Log the metric
        combined_labels = {**self.labels, **(labels or {})}
        label_str = ", ".join(f"{k}={v}" for k, v in combined_labels.items())
        logger.debug(f"METRIC: {self.name}={self.value} ({label_str})")

    def observe(self, value: float, labels: dict[str, str] | None = None) -> None:
        """Observe a histogram metric.

        Args:
            value: Value to observe
            labels: Additional labels for this observation
        """
        if self.type != MetricType.HISTOGRAM:
            raise ObservabilityError(f"Cannot observe metric of type {self.type}")
        
        # Type checking to satisfy mypy
        if isinstance(self.value, list):
            self.value.append(value)
        
        # Log the metric
        combined_labels = {**self.labels, **(labels or {})}
        label_str = ", ".join(f"{k}={v}" for k, v in combined_labels.items())
        logger.debug(f"METRIC: {self.name}={value} ({label_str})")


class MetricsRegistry:
    """Registry for metrics."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MetricsRegistry, cls).__new__(cls)
            cls._instance._metrics = {}
        return cls._instance

    def __init__(self):
        """Initialize the metrics registry."""
        # Ensure metrics is initialized
        if not hasattr(self, "_metrics"):
            self._metrics = {}

    def register(self, metric: Metric) -> Metric:
        """Register a metric.

        Args:
            metric: Metric to register

        Returns:
            Registered metric
        """
        self._metrics[metric.name] = metric
        return metric

    def get(self, name: str) -> Metric | None:
        """Get a metric by name.

        Args:
            name: Metric name

        Returns:
            Metric or None if not found
        """
        return self._metrics.get(name)

    def list(self) -> list[Metric]:
        """List all registered metrics.

        Returns:
            List of metrics
        """
        return list(self._metrics.values())


# Global metrics registry
_metrics_registry = MetricsRegistry()


def get_metrics_registry() -> MetricsRegistry:
    """Get the global metrics registry.

    Returns:
        Global metrics registry
    """
    return _metrics_registry


def create_counter(
    name: str, description: str = "", labels: dict[str, str] | None = None
) -> Metric:
    """Create a counter metric.

    Args:
        name: Metric name
        description: Metric description
        labels: Metric labels

    Returns:
        Counter metric
    """
    metric = Metric(name, MetricType.COUNTER, description, labels)
    return _metrics_registry.register(metric)


def create_gauge(
    name: str, description: str = "", labels: dict[str, str] | None = None
) -> Metric:
    """Create a gauge metric.

    Args:
        name: Metric name
        description: Metric description
        labels: Metric labels

    Returns:
        Gauge metric
    """
    metric = Metric(name, MetricType.GAUGE, description, labels)
    return _metrics_registry.register(metric)


def create_histogram(
    name: str, description: str = "", labels: dict[str, str] | None = None
) -> Metric:
    """Create a histogram metric.

    Args:
        name: Metric name
        description: Metric description
        labels: Metric labels

    Returns:
        Histogram metric
    """
    metric = Metric(name, MetricType.HISTOGRAM, description, labels)
    return _metrics_registry.register(metric)


def get_metric(name: str) -> Metric | None:
    """Get a metric by name.

    Args:
        name: Metric name

    Returns:
        Metric or None if not found
    """
    return _metrics_registry.get(name)


@asynccontextmanager
async def timed_operation(
    name: str, labels: dict[str, str] | None = None
) -> AsyncGenerator[None, None]:
    """Time an operation and record metrics.

    Args:
        name: Operation name
        labels: Operation labels

    Yields:
        None
    """
    # Create or get timer metric
    metric_name = f"operation_time_{name}"
    metric = get_metric(metric_name)
    if not metric:
        metric = create_histogram(
            metric_name,
            description=f"Time spent in {name} operation",
            labels={"operation": name},
        )

    # Get execution context
    context = get_current_context()
    if context:
        span_id = context.start_span(name)

    # Record start time
    start_time = time.time()

    try:
        # Yield control to the caller
        yield
    finally:
        # Record end time and calculate duration
        end_time = time.time()
        duration = end_time - start_time

        # Record metric
        combined_labels = {**{"operation": name}, **(labels or {})}
        metric.observe(duration, combined_labels)

        # End span if context exists
        if context and span_id:
            context.end_span(span_id)

        # Log the operation time
        label_str = ", ".join(f"{k}={v}" for k, v in combined_labels.items())
        logger.debug(f"OPERATION: {name} took {duration:.6f}s ({label_str})")


def instrument(name: str | None = None, labels: dict[str, str] | None = None):
    """Decorator for instrumenting async functions.

    Args:
        name: Operation name (defaults to function name)
        labels: Operation labels

    Returns:
        Decorated function
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Use provided name or function name
            operation_name = name or func.__name__

            # Create execution context if one doesn't exist
            context = get_current_context()
            if not context:
                async with execution_context() as _:
                    # Time the operation
                    async with timed_operation(operation_name, labels):
                        return await func(*args, **kwargs)
            else:
                # Time the operation
                async with timed_operation(operation_name, labels):
                    return await func(*args, **kwargs)

        return wrapper

    return decorator


# Built-in metrics
request_counter = create_counter(
    "pepperpy_requests_total",
    "Total number of requests",
)

error_counter = create_counter(
    "pepperpy_errors_total",
    "Total number of errors",
)

active_requests = create_gauge(
    "pepperpy_active_requests",
    "Active requests",
)

response_time = create_histogram(
    "pepperpy_response_time",
    "Response time in seconds",
)
