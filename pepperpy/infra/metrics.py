"""Performance metrics and measurement utilities for PepperPy.

This module provides utilities for measuring and tracking performance metrics,
including execution time, memory usage, and custom metrics. It works in conjunction
with the telemetry system to provide a comprehensive performance monitoring solution.

Typical usage examples:

    # Simple time measurement
    with measure_time("operation_name") as timer:
        # Code to measure
        result = perform_operation()
    print(f"Operation took {timer.elapsed_time} seconds")

    # Memory usage tracking
    with measure_memory("memory_intensive_operation") as tracker:
        # Memory-intensive code
        result = process_large_dataset()
    print(f"Operation used {tracker.memory_used} bytes")

    # Full performance tracking
    with performance_tracker("critical_operation", track_memory=True) as perf:
        # Operation to track
        result = perform_critical_operation()
    print(f"Performance: {perf}")

    # Function decorator for benchmarking
    @benchmark(iterations=10, track_memory=True)
    def function_to_benchmark(arg1, arg2):
        # Function implementation
        return result
"""

import functools
import gc
import time
import tracemalloc
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import (
    Any,
    Callable,
    Dict,
    Generator,
    List,
    Optional,
    TypeVar,
    Union,
    cast,
)

from pepperpy.infra.logging import get_logger
from pepperpy.infra.telemetry import (
    MetricType,
    get_provider_telemetry,
    report_metric,
)

# Logger for this module
logger = get_logger(__name__)

# Type variables
T = TypeVar("T")  # Input type
R = TypeVar("R")  # Result type
F = TypeVar("F", bound=Callable[..., Any])


class MetricCategory(Enum):
    """Categories of metrics that can be collected."""

    PERFORMANCE = "performance"  # Performance-related metrics
    RESOURCE = "resource"  # Resource usage metrics
    BUSINESS = "business"  # Business-related metrics
    SYSTEM = "system"  # System-level metrics
    CUSTOM = "custom"  # Custom metrics


class PerformanceMetric(Enum):
    """Enum representing different performance metrics."""

    EXECUTION_TIME = auto()  # Execution time in seconds
    CPU_TIME = auto()  # CPU time in seconds
    MEMORY_USAGE = auto()  # Memory usage in bytes
    THROUGHPUT = auto()  # Operations per second
    LATENCY = auto()  # Time per operation
    CUSTOM = auto()  # Custom metric


@dataclass
class MetricResult:
    """Result of a metric measurement.

    This class stores the results of a metric measurement, including the metric name,
    value, and associated metadata.
    """

    name: str  # Name of the metric
    value: float  # Value of the metric
    unit: str  # Unit of measurement
    category: MetricCategory = MetricCategory.CUSTOM  # Category of the metric
    tags: Dict[str, str] = field(default_factory=dict)  # Tags for the metric
    timestamp: float = field(
        default_factory=time.time
    )  # Timestamp when the metric was recorded

    def __str__(self) -> str:
        """Get a string representation of the metric result.

        Returns:
            A string representation of the metric result
        """
        return f"{self.name}: {self.value} {self.unit} ({self.category.value})"


@dataclass
class PerformanceResult:
    """Result of a performance measurement.

    This class stores the results of a performance measurement, including execution time,
    memory usage, and custom metrics.
    """

    # Name of the measurement
    name: str
    # Number of iterations
    iterations: int = 1
    # Execution time in seconds
    execution_time: float = 0.0
    # Execution time per iteration in seconds
    time_per_iteration: float = 0.0
    # Memory usage in bytes (peak)
    memory_usage: Optional[int] = None
    # Memory usage per iteration in bytes
    memory_per_iteration: Optional[float] = None
    # Custom metrics
    custom_metrics: Dict[str, Any] = field(default_factory=dict)
    # Raw timing data for each iteration
    iteration_times: List[float] = field(default_factory=list)
    # Raw memory data for each iteration
    iteration_memory: List[Optional[int]] = field(default_factory=list)
    # Timestamp when the measurement was taken
    timestamp: float = field(default_factory=time.time)

    def __str__(self) -> str:
        """Get a string representation of the performance result.

        Returns:
            A string representation of the performance result
        """
        result = [
            f"Performance: {self.name}",
            f"Iterations: {self.iterations}",
            f"Total time: {self.execution_time:.6f} seconds",
            f"Time per iteration: {self.time_per_iteration:.6f} seconds",
        ]

        if self.memory_usage is not None:
            result.append(f"Peak memory usage: {self.format_bytes(self.memory_usage)}")
            if self.memory_per_iteration is not None:
                result.append(
                    f"Memory per iteration: {self.format_bytes(self.memory_per_iteration)}"
                )

        if self.custom_metrics:
            result.append("Custom metrics:")
            for name, value in self.custom_metrics.items():
                result.append(f"  {name}: {value}")

        return "\n".join(result)

    @staticmethod
    def format_bytes(size: Union[int, float]) -> str:
        """Format a byte size as a human-readable string.

        Args:
            size: The size in bytes

        Returns:
            A human-readable string representation of the size
        """
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024 or unit == "TB":
                return f"{size:.2f} {unit}"
            size /= 1024

        # This should never be reached, but added to satisfy the linter
        return f"{size:.2f} TB"

    def to_metrics(self) -> List[MetricResult]:
        """Convert the performance result to a list of metric results.

        Returns:
            A list of metric results
        """
        metrics = [
            MetricResult(
                name=f"{self.name}.execution_time",
                value=self.execution_time,
                unit="seconds",
                category=MetricCategory.PERFORMANCE,
                tags={"iterations": str(self.iterations)},
                timestamp=self.timestamp,
            ),
            MetricResult(
                name=f"{self.name}.time_per_iteration",
                value=self.time_per_iteration,
                unit="seconds",
                category=MetricCategory.PERFORMANCE,
                tags={"iterations": str(self.iterations)},
                timestamp=self.timestamp,
            ),
        ]

        if self.memory_usage is not None:
            metrics.append(
                MetricResult(
                    name=f"{self.name}.memory_usage",
                    value=float(self.memory_usage),
                    unit="bytes",
                    category=MetricCategory.RESOURCE,
                    tags={"iterations": str(self.iterations)},
                    timestamp=self.timestamp,
                )
            )

        if self.memory_per_iteration is not None:
            metrics.append(
                MetricResult(
                    name=f"{self.name}.memory_per_iteration",
                    value=self.memory_per_iteration,
                    unit="bytes",
                    category=MetricCategory.RESOURCE,
                    tags={"iterations": str(self.iterations)},
                    timestamp=self.timestamp,
                )
            )

        for name, value in self.custom_metrics.items():
            if isinstance(value, (int, float)):
                metrics.append(
                    MetricResult(
                        name=f"{self.name}.{name}",
                        value=float(value),
                        unit="",
                        category=MetricCategory.CUSTOM,
                        tags={"iterations": str(self.iterations)},
                        timestamp=self.timestamp,
                    )
                )

        return metrics

    def report_to_telemetry(self, provider_id: Optional[str] = None) -> None:
        """Report the performance result to the telemetry system.

        Args:
            provider_id: The ID of the provider to report the metrics for
        """
        metrics = self.to_metrics()

        for metric in metrics:
            if provider_id:
                telemetry = get_provider_telemetry(provider_id)
                if "time" in metric.name.lower():
                    telemetry.report_metric(
                        name=metric.name,
                        value=metric.value,
                        type=MetricType.TIMER,
                        tags=metric.tags,
                    )
                else:
                    telemetry.report_metric(
                        name=metric.name,
                        value=metric.value,
                        type=MetricType.GAUGE,
                        tags=metric.tags,
                    )
            else:
                if "time" in metric.name.lower():
                    report_metric(
                        name=metric.name,
                        value=metric.value,
                        type=MetricType.TIMER,
                        tags=metric.tags,
                    )
                else:
                    report_metric(
                        name=metric.name,
                        value=metric.value,
                        type=MetricType.GAUGE,
                        tags=metric.tags,
                    )


class PerformanceTracker:
    """Utility class for tracking performance metrics.

    This class provides methods for tracking performance metrics, including
    execution time measurement, memory usage tracking, and custom metrics.
    """

    def __init__(self, name: str):
        """Initialize the performance tracker.

        Args:
            name: The name of the performance tracking session
        """
        self.name = name
        self.reset()

    def reset(self) -> None:
        """Reset the performance tracker state."""
        self.iteration_times: List[float] = []
        self.iteration_memory: List[Optional[int]] = []
        self.custom_metrics: Dict[str, Any] = {}
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

    def start(self, track_memory: bool = False) -> None:
        """Start the performance tracking.

        Args:
            track_memory: Whether to track memory usage
        """
        self.reset()
        self.start_time = time.time()

        # Start memory tracking if requested
        if track_memory:
            tracemalloc.start()

    def stop(self, track_memory: bool = False) -> PerformanceResult:
        """Stop the performance tracking and get the result.

        Args:
            track_memory: Whether memory usage was tracked

        Returns:
            The performance result
        """
        if self.start_time is None:
            raise ValueError("Performance tracking not started")

        self.end_time = time.time()
        execution_time = self.end_time - self.start_time

        # Get peak memory usage
        memory_usage = None
        memory_per_iteration = None
        if track_memory:
            memory_usage = tracemalloc.get_traced_memory()[1]
            tracemalloc.stop()

            # Calculate memory per iteration
            if self.iteration_memory:
                memory_per_iteration = sum(
                    m for m in self.iteration_memory if m is not None
                ) / len(self.iteration_memory)

        # Create performance result
        result = PerformanceResult(
            name=self.name,
            iterations=max(1, len(self.iteration_times)),
            execution_time=execution_time,
            time_per_iteration=execution_time / max(1, len(self.iteration_times)),
            memory_usage=memory_usage,
            memory_per_iteration=memory_per_iteration,
            custom_metrics=self.custom_metrics,
            iteration_times=self.iteration_times,
            iteration_memory=self.iteration_memory,
        )

        return result

    def add_custom_metric(self, name: str, value: Any) -> None:
        """Add a custom metric to the performance tracker.

        Args:
            name: The name of the metric
            value: The value of the metric
        """
        self.custom_metrics[name] = value


class Timer:
    """Utility class for measuring execution time.

    This class provides methods for measuring the execution time of code blocks.
    """

    def __init__(self, name: str):
        """Initialize the timer.

        Args:
            name: The name of the timer
        """
        self.name = name
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.elapsed_time: float = 0.0

    def start(self) -> None:
        """Start the timer."""
        self.start_time = time.time()

    def stop(self) -> float:
        """Stop the timer and get the elapsed time.

        Returns:
            The elapsed time in seconds
        """
        if self.start_time is None:
            raise ValueError("Timer not started")

        self.end_time = time.time()
        self.elapsed_time = self.end_time - self.start_time
        return self.elapsed_time

    def reset(self) -> None:
        """Reset the timer."""
        self.start_time = None
        self.end_time = None
        self.elapsed_time = 0.0

    def __enter__(self) -> "Timer":
        """Enter the context manager.

        Returns:
            The timer instance
        """
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the context manager.

        Args:
            exc_type: The exception type, if any
            exc_val: The exception value, if any
            exc_tb: The exception traceback, if any
        """
        self.stop()

        # Report to telemetry
        report_metric(
            name=f"{self.name}.execution_time",
            value=self.elapsed_time,
            type=MetricType.TIMER,
        )


class MemoryTracker:
    """Utility class for tracking memory usage.

    This class provides methods for tracking the memory usage of code blocks.
    """

    def __init__(self, name: str):
        """Initialize the memory tracker.

        Args:
            name: The name of the memory tracker
        """
        self.name = name
        self.start_memory: Optional[int] = None
        self.end_memory: Optional[int] = None
        self.peak_memory: Optional[int] = None
        self.memory_used: Optional[int] = None

    def start(self) -> None:
        """Start the memory tracker."""
        tracemalloc.start()
        self.start_memory = tracemalloc.get_traced_memory()[1]

    def stop(self) -> Optional[int]:
        """Stop the memory tracker and get the memory used.

        Returns:
            The memory used in bytes
        """
        if self.start_memory is None:
            raise ValueError("Memory tracker not started")

        self.end_memory, self.peak_memory = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        self.memory_used = self.peak_memory - self.start_memory
        return self.memory_used

    def reset(self) -> None:
        """Reset the memory tracker."""
        self.start_memory = None
        self.end_memory = None
        self.peak_memory = None
        self.memory_used = None

    def __enter__(self) -> "MemoryTracker":
        """Enter the context manager.

        Returns:
            The memory tracker instance
        """
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the context manager.

        Args:
            exc_type: The exception type, if any
            exc_val: The exception value, if any
            exc_tb: The exception traceback, if any
        """
        self.stop()

        # Report to telemetry
        if self.memory_used is not None:
            report_metric(
                name=f"{self.name}.memory_usage",
                value=float(self.memory_used),
                type=MetricType.GAUGE,
            )


@contextmanager
def measure_time(name: str) -> Generator[Timer, None, None]:
    """Context manager for measuring execution time.

    Args:
        name: The name of the timer

    Yields:
        The timer instance
    """
    timer = Timer(name)
    timer.start()
    try:
        yield timer
    finally:
        timer.stop()


@contextmanager
def measure_memory(name: str) -> Generator[MemoryTracker, None, None]:
    """Context manager for tracking memory usage.

    Args:
        name: The name of the memory tracker

    Yields:
        The memory tracker instance
    """
    tracker = MemoryTracker(name)
    tracker.start()
    try:
        yield tracker
    finally:
        tracker.stop()


@contextmanager
def performance_tracker(
    name: str, track_memory: bool = False
) -> Generator[PerformanceTracker, None, None]:
    """Context manager for tracking performance metrics.

    Args:
        name: The name of the performance tracker
        track_memory: Whether to track memory usage

    Yields:
        The performance tracker instance
    """
    tracker = PerformanceTracker(name)
    tracker.start(track_memory=track_memory)
    try:
        yield tracker
    finally:
        result = tracker.stop(track_memory=track_memory)
        logger.debug(f"Performance tracking result: {result}")


def benchmark(
    iterations: int = 1,
    warmup_iterations: int = 0,
    track_memory: bool = False,
    gc_collect: bool = True,
    report_telemetry: bool = True,
    provider_id: Optional[str] = None,
) -> Callable[[F], F]:
    """Decorator for benchmarking functions.

    Args:
        iterations: The number of iterations to run
        warmup_iterations: The number of warmup iterations to run
        track_memory: Whether to track memory usage
        gc_collect: Whether to collect garbage before each iteration
        report_telemetry: Whether to report metrics to telemetry
        provider_id: The ID of the provider to report metrics for

    Returns:
        The decorated function
    """

    def decorator(func: F) -> F:
        """Decorator function.

        Args:
            func: The function to decorate

        Returns:
            The decorated function
        """

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Wrapper function.

            Args:
                *args: Positional arguments
                **kwargs: Keyword arguments

            Returns:
                The result of the function
            """
            name = f"{func.__module__}.{func.__name__}"
            tracker = PerformanceTracker(name)

            # Start tracking
            tracker.start(track_memory=track_memory)

            # Run warmup iterations
            for _ in range(warmup_iterations):
                func(*args, **kwargs)

            # Define the function to benchmark
            def benchmark_func() -> Any:
                return func(*args, **kwargs)

            # Run iterations
            result = None
            for i in range(iterations):
                # Collect garbage if requested
                if gc_collect:
                    gc.collect()

                # Measure memory usage before iteration
                if track_memory:
                    memory_before = tracemalloc.get_traced_memory()[1]

                # Run iteration
                iteration_start = time.time()
                if i == iterations - 1:  # Save result from last iteration
                    result = benchmark_func()
                else:
                    benchmark_func()
                iteration_time = time.time() - iteration_start
                tracker.iteration_times.append(iteration_time)

                # Measure memory usage after iteration
                if track_memory:
                    memory_after = tracemalloc.get_traced_memory()[1]
                    memory_diff = memory_after - memory_before
                    tracker.iteration_memory.append(memory_diff)
                else:
                    tracker.iteration_memory.append(None)

            # Stop tracking and get result
            perf_result = tracker.stop(track_memory=track_memory)

            # Report to telemetry if requested
            if report_telemetry:
                perf_result.report_to_telemetry(provider_id)

            # Log result
            logger.debug(f"Benchmark result: {perf_result}")

            return result

        return cast(F, wrapper)

    return decorator


def get_memory_usage() -> Dict[str, Any]:
    """Get current memory usage.

    Returns:
        A dictionary with memory usage information
    """
    tracemalloc.start()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return {
        "current_bytes": current,
        "peak_bytes": peak,
        "current_formatted": PerformanceResult.format_bytes(current),
        "peak_formatted": PerformanceResult.format_bytes(peak),
    }


def get_system_info() -> Dict[str, Any]:
    """Get system information.

    Returns:
        A dictionary with system information
    """
    import platform

    import psutil  # type: ignore

    memory = psutil.virtual_memory()

    return {
        "platform": platform.platform(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "memory_total_bytes": memory.total,
        "memory_available_bytes": memory.available,
        "memory_used_percent": memory.percent,
        "cpu_count": psutil.cpu_count(),
        "cpu_percent": psutil.cpu_percent(interval=0.1),
    }


def report_custom_metric(
    name: str,
    value: float,
    unit: str = "",
    category: MetricCategory = MetricCategory.CUSTOM,
    tags: Optional[Dict[str, str]] = None,
    report_telemetry: bool = True,
    provider_id: Optional[str] = None,
) -> MetricResult:
    """Report a custom metric.

    Args:
        name: The name of the metric
        value: The value of the metric
        unit: The unit of measurement
        category: The category of the metric
        tags: Tags for the metric
        report_telemetry: Whether to report the metric to telemetry
        provider_id: The ID of the provider to report the metric for

    Returns:
        The metric result
    """
    metric = MetricResult(
        name=name,
        value=value,
        unit=unit,
        category=category,
        tags=tags or {},
    )

    # Report to telemetry if requested
    if report_telemetry:
        if provider_id:
            telemetry = get_provider_telemetry(provider_id)
            telemetry.report_metric(
                name=name,
                value=value,
                type=MetricType.GAUGE,
                tags=tags,
            )
        else:
            report_metric(
                name=name,
                value=value,
                type=MetricType.GAUGE,
                tags=tags,
            )

    return metric
