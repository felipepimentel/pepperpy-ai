"""Metrics collection and monitoring for PepperPy.
 
This module provides utilities for collecting and monitoring metrics in the PepperPy framework.
"""


import logging
import platform
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, ParamSpec, TypeVar

import psutil

P = ParamSpec("P")
T = TypeVar("T")

logger = logging.getLogger(__name__)


class MetricCategory(Enum):
    """Categories for metrics."""

    PERFORMANCE = "performance"
    MEMORY = "memory"
    SYSTEM = "system"
    CUSTOM = "custom"
    BUSINESS = "business"


@dataclass
class Metric:
    """A metric data point.

    Attributes:
        name: Name of the metric
        value: float
        timestamp: When the metric was recorded
        category: Category of the metric
        tags: Optional tags for the metric
    """

    name: str
    value: float
    timestamp: datetime
    category: MetricCategory
    tags: Optional[Dict[str, Any]] = None


class BaseContext:
    """Base context for metric tracking."""

    def __init__(
        self,
        name: str,
        collector: "MetricsCollector",
        tags: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the context.

        Args:
            name: Name of the metric
            collector: Metrics collector
            tags: Optional tags
        """
        self.name = name
        self.collector = collector
        self.tags = tags or {}

    def add_custom_metric(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a custom metric.

        Args:
            name: Name of the metric
            value: Value of the metric
            tags: Optional tags
        """
        metric_tags = dict(self.tags)
        if tags:
            metric_tags.update(tags)

        self.collector.record_metric(
            name=name,
            value=value,
            category=MetricCategory.CUSTOM,
            tags=metric_tags,
        )


class TimeContext(BaseContext):
    """Context for tracking execution time."""

    def __init__(
        self,
        name: str,
        collector: "MetricsCollector",
        tags: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the time context.

        Args:
            name: Name of the metric
            collector: Metrics collector
            tags: Optional tags
        """
        super().__init__(name, collector, tags)
        self.start_time = 0.0
        self.end_time = 0.0

    def start(self) -> None:
        """Start the timer."""
        self.start_time = time.time()

    def stop(self) -> None:
        """Stop the timer and record the metric."""
        self.end_time = time.time()
        self.collector.record_metric(
            self.name,
            (self.end_time - self.start_time) * 1000,
            MetricCategory.PERFORMANCE,
            self.tags,
        )


class MemoryContext(BaseContext):
    """Context for tracking memory usage."""

    def __init__(
        self,
        name: str,
        collector: "MetricsCollector",
        tags: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the memory context.

        Args:
            name: Name of the metric
            collector: Metrics collector
            tags: Optional tags
        """
        super().__init__(name, collector, tags)
        self.start_memory = 0
        self.end_memory = 0

    def start(self) -> None:
        """Start memory measurement."""
        self.start_memory = psutil.Process().memory_info().rss

    def stop(self) -> None:
        """Stop memory measurement and record the metric."""
        self.end_memory = psutil.Process().memory_info().rss
        memory_diff_mb = (self.end_memory - self.start_memory) / (1024 * 1024)
        self.collector.record_metric(
            self.name, memory_diff_mb, MetricCategory.MEMORY, self.tags
        )


class MetricsCollector:
    """Collector for metrics."""

    def __init__(self):
        """Initialize the metrics collector."""
        self.metrics: Dict[str, List[Metric]] = {}

    def record_metric(
        self,
        name: str,
        value: float,
        category: MetricCategory,
        tags: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record a metric.

        Args:
            name: Name of the metric
            value: Value of the metric
            category: Category of the metric
            tags: Optional tags
        """
        metric = Metric(
            name=name,
            value=value,
            timestamp=datetime.now(),
            category=category,
            tags=tags,
        )

        if name not in self.metrics:
            self.metrics[name] = []

        self.metrics[name].append(metric)

        # Log the metric for debugging
        tag_str = ""
        if tags:
            tag_parts = []
            for key, value in tags.items():
                tag_parts.append(f"{key}={value}")
            tag_str = " " + " ".join(tag_parts)

        logger.debug(f"Recorded metric: {name}={value:.4f} [{category.value}]{tag_str}")

    def get_metrics(
        self,
        name: Optional[str] = None,
        category: Optional[MetricCategory] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Dict[str, List[Metric]]:
        """Get metrics with optional filtering.

        Args:
            name: Filter by metric name
            category: Filter by category
            start_time: Filter by start time
            end_time: Filter by end time

        Returns:
            Filtered metrics
        """
        result: Dict[str, List[Metric]] = {}

        # Filter by name if provided
        metrics_to_filter = (
            {name: self.metrics[name]}
            if name and name in self.metrics
            else self.metrics
        )

        # Apply additional filters
        for metric_name, metric_list in metrics_to_filter.items():
            filtered_metrics = []

            for metric in metric_list:
                # Filter by category
                if category and metric.category != category:
                    continue

                # Filter by time range
                if start_time and metric.timestamp < start_time:
                    continue

                if end_time and metric.timestamp > end_time:
                    continue

                filtered_metrics.append(metric)

            if filtered_metrics:
                result[metric_name] = filtered_metrics

        return result


class PerformanceTracker:
    """Track performance metrics."""

    def __init__(self, collector: Optional[MetricsCollector] = None):
        """Initialize the performance tracker.

        Args:
            collector: Optional metrics collector
        """
        self.collector = collector or MetricsCollector()

    @contextmanager
    def measure_time(self, name: str, tags: Optional[Dict[str, Any]] = None):
        """Measure execution time.

        Args:
            name: Name of the metric
            tags: Optional tags

        Yields:
            TimeContext for additional custom metrics
        """
        context = TimeContext(name, self.collector, tags)
        context.start()
        try:
            yield context
        finally:
            context.stop()

    @contextmanager
    def measure_memory(self, name: str, tags: Optional[Dict[str, Any]] = None):
        """Measure memory usage.

        Args:
            name: Name of the metric
            tags: Optional tags

        Yields:
            MemoryContext for additional custom metrics
        """
        context = MemoryContext(name, self.collector, tags)
        context.start()
        try:
            yield context
        finally:
            context.stop()

    def add_custom_metric(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a custom metric.

        Args:
            name: Name of the metric
            value: Value of the metric
            tags: Optional tags
        """
        self.collector.record_metric(
            name=name,
            value=value,
            category=MetricCategory.CUSTOM,
            tags=tags,
        )


def get_system_info() -> Dict[str, Any]:
    """Get system information.

    Returns:
        Dictionary with system information
    """
    return {
        "platform": platform.system(),
        "platform_release": platform.release(),
        "platform_version": platform.version(),
        "architecture": platform.machine(),
        "processor": platform.processor(),
        "cpu_count": psutil.cpu_count(),
        "memory_total": psutil.virtual_memory().total / (1024 * 1024 * 1024),  # GB
    }


def get_memory_usage() -> Dict[str, Any]:
    """Get current memory usage.

    Returns:
        Dictionary with memory usage information
    """
    process = psutil.Process()
    memory_info = process.memory_info()

    # Get memory usage in MB
    rss_mb = memory_info.rss / (1024 * 1024)
    vms_mb = memory_info.vms / (1024 * 1024)

    # Get system memory usage
    system_memory = psutil.virtual_memory()
    system_memory_percent = system_memory.percent
    system_memory_used_gb = system_memory.used / (1024 * 1024 * 1024)
    system_memory_total_gb = system_memory.total / (1024 * 1024 * 1024)

    return {
        "process_rss_mb": rss_mb,
        "process_vms_mb": vms_mb,
        "system_memory_percent": system_memory_percent,
        "system_memory_used_gb": system_memory_used_gb,
        "system_memory_total_gb": system_memory_total_gb,
    }


def benchmark(
    iterations: int = 1,
    warmup_iterations: int = 0,
    track_memory: bool = False,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Benchmark a function.

    Args:
        iterations: Number of iterations
        warmup_iterations: Number of warmup iterations
        track_memory: Whether to track memory usage

    Returns:
        Decorator function
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            """Wrap function with benchmarking.

            Args:
                *args: Function arguments
                **kwargs: Function keyword arguments

            Returns:
                Function result
            """
            # Get function name
            func_name = func.__name__

            # Perform warmup iterations
            if warmup_iterations > 0:
                for _ in range(warmup_iterations):
                    func(*args, **kwargs)

            # Create performance tracker
            tracker = PerformanceTracker()

            # Track execution times
            execution_times = []
            memory_before = []
            memory_after = []
            memory_diff = []

            if track_memory:
                # Get initial memory for memory diff calculation
                process = psutil.Process()
                initial_memory = process.memory_info().rss

            # Execute the function multiple times and measure performance
            result: T = None  # type: ignore
            for i in range(iterations):
                if track_memory:
                    # Measure memory before execution
                    memory_before.append(psutil.Process().memory_info().rss)

                # Measure execution time
                start_time = time.time()
                result = func(*args, **kwargs)
                end_time = time.time()
                execution_time = (end_time - start_time) * 1000  # ms
                execution_times.append(execution_time)

                if track_memory:
                    # Measure memory after execution
                    current_memory = psutil.Process().memory_info().rss
                    memory_after.append(current_memory)
                    memory_diff.append(current_memory - memory_before[i])

            # Calculate statistics
            avg_time = sum(execution_times) / len(execution_times)
            min_time = min(execution_times)
            max_time = max(execution_times)

            # Log benchmark results
            logger.info(f"Benchmark results for {func_name}:")
            logger.info(f"  Iterations: {iterations}")
            logger.info(f"  Average execution time: {avg_time:.2f} ms")
            logger.info(f"  Min execution time: {min_time:.2f} ms")
            logger.info(f"  Max execution time: {max_time:.2f} ms")

            if track_memory:
                # Calculate memory usage statistics
                avg_memory_diff = sum(memory_diff) / len(memory_diff)
                min_memory_diff = min(memory_diff)
                max_memory_diff = max(memory_diff)

                # Convert to MB for easier reading
                avg_memory_diff_mb = avg_memory_diff / (1024 * 1024)
                min_memory_diff_mb = min_memory_diff / (1024 * 1024)
                max_memory_diff_mb = max_memory_diff / (1024 * 1024)

                logger.info(f"  Average memory increase: {avg_memory_diff_mb:.2f} MB")
                logger.info(f"  Min memory increase: {min_memory_diff_mb:.2f} MB")
                logger.info(f"  Max memory increase: {max_memory_diff_mb:.2f} MB")

                # Calculate final memory increase
                final_memory = psutil.Process().memory_info().rss
                total_memory_diff = final_memory - initial_memory
                total_memory_diff_mb = total_memory_diff / (1024 * 1024)
                logger.info(f"  Total memory increase: {total_memory_diff_mb:.2f} MB")

            return result

        return wrapper

    return decorator


def measure_time(name: str, tags: Optional[Dict[str, Any]] = None):
    """Measure execution time of a function.

    Args:
        name: Name of the metric
        tags: Optional tags

    Returns:
        Decorator function
    """
    tracker = PerformanceTracker()
    return tracker.measure_time(name, tags)


def measure_memory(name: str, tags: Optional[Dict[str, Any]] = None):
    """Measure memory usage of a function.

    Args:
        name: Name of the metric
        tags: Optional tags

    Returns:
        Decorator function
    """
    tracker = PerformanceTracker()
    return tracker.measure_memory(name, tags)


def performance_tracker(name: str, track_memory: bool = False):
    """Create a performance tracker for a function.

    Args:
        name: Base name for metrics
        track_memory: Whether to track memory usage

    Returns:
        Decorator function
    """
    tracker = PerformanceTracker()

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with tracker.measure_time(f"{name}_time"):
                if track_memory:
                    with tracker.measure_memory(f"{name}_memory"):
                        return func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)

        return wrapper

    return decorator


def report_custom_metric(
    name: str,
    value: float,
    unit: Optional[str] = None,
    category: Optional[MetricCategory] = None,
    tags: Optional[Dict[str, Any]] = None,
) -> None:
    """Report a custom metric.

    Args:
        name: Name of the metric
        value: Value of the metric
        unit: Optional unit of the metric
        category: Optional category of the metric
        tags: Optional tags
    """
    # Create a new collector or use a global one
    collector = MetricsCollector()

    # Update tags with unit if provided
    metric_tags = tags or {}
    if unit:
        metric_tags["unit"] = unit

    # Use specified category or default to CUSTOM
    metric_category = category or MetricCategory.CUSTOM

    # Record the metric
    collector.record_metric(
        name=name,
        value=value,
        category=metric_category,
        tags=metric_tags,
    )
