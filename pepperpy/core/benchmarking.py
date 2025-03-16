"""Performance benchmarking and profiling tools.

This module provides utilities for benchmarking and profiling code performance,
including execution time measurement, memory usage tracking, and performance
comparison tools.
"""

import cProfile
import functools
import gc
import io
import pstats
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

from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)

# Type variables
T = TypeVar("T")  # Input type
R = TypeVar("R")  # Result type
F = TypeVar("F", bound=Callable[..., Any])


class BenchmarkMetric(Enum):
    """Enum representing different benchmark metrics."""

    EXECUTION_TIME = auto()  # Execution time in seconds
    CPU_TIME = auto()  # CPU time in seconds
    MEMORY_USAGE = auto()  # Memory usage in bytes
    THROUGHPUT = auto()  # Operations per second
    LATENCY = auto()  # Time per operation
    CUSTOM = auto()  # Custom metric


@dataclass
class BenchmarkResult:
    """Result of a benchmark run.

    This class stores the results of a benchmark run, including execution time,
    memory usage, and custom metrics.
    """

    # Name of the benchmark
    name: str
    # Number of iterations
    iterations: int
    # Execution time in seconds
    execution_time: float
    # Execution time per iteration in seconds
    time_per_iteration: float
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
    # Timestamp when the benchmark was run
    timestamp: float = field(default_factory=time.time)

    def __str__(self) -> str:
        """Get a string representation of the benchmark result.

        Returns:
            A string representation of the benchmark result
        """
        result = [
            f"Benchmark: {self.name}",
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


@dataclass
class ProfileResult:
    """Result of a profile run.

    This class stores the results of a profile run, including function call
    statistics and memory usage.
    """

    # Name of the profile
    name: str
    # Function call statistics
    stats: pstats.Stats
    # Memory usage statistics
    memory_stats: Optional[Dict[str, Any]] = None
    # Custom metrics
    custom_metrics: Dict[str, Any] = field(default_factory=dict)
    # Timestamp when the profile was run
    timestamp: float = field(default_factory=time.time)

    def __str__(self) -> str:
        """Get a string representation of the profile result.

        Returns:
            A string representation of the profile result
        """
        result = [f"Profile: {self.name}"]

        if self.memory_stats:
            result.append("Memory statistics:")
            for name, value in self.memory_stats.items():
                if isinstance(value, (int, float)) and name.endswith("_bytes"):
                    value_str = BenchmarkResult.format_bytes(value)
                else:
                    value_str = str(value)
                result.append(f"  {name}: {value_str}")

        if self.custom_metrics:
            result.append("Custom metrics:")
            for name, value in self.custom_metrics.items():
                result.append(f"  {name}: {value}")

        return "\n".join(result)

    def print_stats(
        self, sort_by: str = "cumulative", limit: int = 20, strip_dirs: bool = True
    ) -> None:
        """Print function call statistics.

        Args:
            sort_by: The field to sort by (cumulative, time, calls, etc.)
            limit: The maximum number of functions to show
            strip_dirs: Whether to strip directory paths from filenames
        """
        stats = self.stats
        if strip_dirs:
            stats = stats.strip_dirs()
        stats.sort_stats(sort_by).print_stats(limit)

    def get_stats_as_string(
        self, sort_by: str = "cumulative", limit: int = 20, strip_dirs: bool = True
    ) -> str:
        """Get function call statistics as a string.

        Args:
            sort_by: The field to sort by (cumulative, time, calls, etc.)
            limit: The maximum number of functions to show
            strip_dirs: Whether to strip directory paths from filenames

        Returns:
            Function call statistics as a string
        """
        stats = self.stats
        if strip_dirs:
            stats = stats.strip_dirs()

        stream = io.StringIO()
        stats.sort_stats(sort_by).print_stats(limit)
        return stream.getvalue()


class Benchmark:
    """Utility class for benchmarking code performance.

    This class provides methods for benchmarking code performance, including
    execution time measurement, memory usage tracking, and custom metrics.
    """

    def __init__(self, name: str):
        """Initialize the benchmark.

        Args:
            name: The name of the benchmark
        """
        self.name = name
        self.reset()

    def reset(self) -> None:
        """Reset the benchmark state."""
        self.iteration_times: List[float] = []
        self.iteration_memory: List[Optional[int]] = []
        self.custom_metrics: Dict[str, Any] = {}

    def run(
        self,
        func: Callable[[], T],
        iterations: int = 1,
        warmup_iterations: int = 0,
        track_memory: bool = False,
        gc_collect: bool = True,
    ) -> BenchmarkResult:
        """Run a benchmark.

        Args:
            func: The function to benchmark
            iterations: The number of iterations to run
            warmup_iterations: The number of warmup iterations to run
            track_memory: Whether to track memory usage
            gc_collect: Whether to collect garbage before each iteration

        Returns:
            The benchmark result
        """
        # Reset state
        self.reset()

        # Run warmup iterations
        for _ in range(warmup_iterations):
            func()

        # Initialize memory tracking if requested
        if track_memory:
            tracemalloc.start()

        # Run benchmark iterations
        start_time = time.time()
        for _ in range(iterations):
            # Collect garbage if requested
            if gc_collect:
                gc.collect()

            # Measure memory usage before iteration
            if track_memory:
                memory_before = tracemalloc.get_traced_memory()[1]

            # Run iteration
            iteration_start = time.time()
            func()
            iteration_time = time.time() - iteration_start
            self.iteration_times.append(iteration_time)

            # Measure memory usage after iteration
            if track_memory:
                memory_after = tracemalloc.get_traced_memory()[1]
                memory_diff = memory_after - memory_before
                self.iteration_memory.append(memory_diff)
            else:
                self.iteration_memory.append(None)

        # Calculate total execution time
        execution_time = time.time() - start_time

        # Get peak memory usage
        if track_memory:
            memory_usage = tracemalloc.get_traced_memory()[1]
            tracemalloc.stop()
        else:
            memory_usage = None

        # Calculate memory per iteration
        if track_memory and self.iteration_memory:
            memory_per_iteration = sum(
                m for m in self.iteration_memory if m is not None
            ) / len(self.iteration_memory)
        else:
            memory_per_iteration = None

        # Create benchmark result
        result = BenchmarkResult(
            name=self.name,
            iterations=iterations,
            execution_time=execution_time,
            time_per_iteration=execution_time / iterations,
            memory_usage=memory_usage,
            memory_per_iteration=memory_per_iteration,
            custom_metrics=self.custom_metrics,
            iteration_times=self.iteration_times,
            iteration_memory=self.iteration_memory,
        )

        return result

    def add_custom_metric(self, name: str, value: Any) -> None:
        """Add a custom metric to the benchmark.

        Args:
            name: The name of the metric
            value: The value of the metric
        """
        self.custom_metrics[name] = value


class Profiler:
    """Utility class for profiling code performance.

    This class provides methods for profiling code performance, including
    function call statistics and memory usage tracking.
    """

    def __init__(self, name: str):
        """Initialize the profiler.

        Args:
            name: The name of the profiler
        """
        self.name = name
        self.reset()

    def reset(self) -> None:
        """Reset the profiler state."""
        self.custom_metrics: Dict[str, Any] = {}

    def run(
        self,
        func: Callable[[], T],
        track_memory: bool = False,
        gc_collect: bool = True,
    ) -> ProfileResult:
        """Run a profile.

        Args:
            func: The function to profile
            track_memory: Whether to track memory usage
            gc_collect: Whether to collect garbage before profiling

        Returns:
            The profile result
        """
        # Reset state
        self.reset()

        # Collect garbage if requested
        if gc_collect:
            gc.collect()

        # Initialize memory tracking if requested
        memory_stats = None
        if track_memory:
            tracemalloc.start()

        # Run profiler
        profiler = cProfile.Profile()
        profiler.enable()
        func()
        profiler.disable()

        # Get memory statistics if requested
        if track_memory:
            current, peak = tracemalloc.get_traced_memory()
            memory_stats = {
                "current_bytes": current,
                "peak_bytes": peak,
            }
            tracemalloc.stop()

        # Create profile result
        stats = pstats.Stats(profiler)
        result = ProfileResult(
            name=self.name,
            stats=stats,
            memory_stats=memory_stats,
            custom_metrics=self.custom_metrics,
        )

        return result

    def add_custom_metric(self, name: str, value: Any) -> None:
        """Add a custom metric to the profile.

        Args:
            name: The name of the metric
            value: The value of the metric
        """
        self.custom_metrics[name] = value


@contextmanager
def benchmark_context(
    name: str, track_memory: bool = False, log_level: str = "info"
) -> Generator[None, None, None]:
    """Context manager for benchmarking code.

    Args:
        name: The name of the benchmark
        track_memory: Whether to track memory usage
        log_level: The log level to use for reporting results

    Yields:
        None
    """
    # Initialize memory tracking if requested
    if track_memory:
        tracemalloc.start()

    # Record start time
    start_time = time.time()

    try:
        yield
    finally:
        # Calculate execution time
        execution_time = time.time() - start_time

        # Get memory usage if requested
        if track_memory:
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            memory_str = f", Peak memory: {BenchmarkResult.format_bytes(peak)}"
        else:
            memory_str = ""

        # Log results
        log_func = getattr(logger, log_level)
        log_func(f"Benchmark '{name}': {execution_time:.6f} seconds{memory_str}")


def benchmark(
    iterations: int = 1,
    warmup_iterations: int = 0,
    track_memory: bool = False,
    gc_collect: bool = True,
    log_level: str = "info",
) -> Callable[[F], F]:
    """Decorator for benchmarking functions.

    Args:
        iterations: The number of iterations to run
        warmup_iterations: The number of warmup iterations to run
        track_memory: Whether to track memory usage
        gc_collect: Whether to collect garbage before each iteration
        log_level: The log level to use for reporting results

    Returns:
        A decorator function
    """

    def decorator(func: F) -> F:
        """Decorator function.

        Args:
            func: The function to decorate

        Returns:
            The decorated function
        """
        benchmark_name = f"{func.__module__}.{func.__name__}"

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Wrapper function.

            Args:
                *args: Positional arguments
                **kwargs: Keyword arguments

            Returns:
                The result of the function
            """
            # Create benchmark
            bench = Benchmark(benchmark_name)

            # Define function to benchmark
            def benchmark_func() -> Any:
                return func(*args, **kwargs)

            # Run benchmark
            result = bench.run(
                benchmark_func,
                iterations=iterations,
                warmup_iterations=warmup_iterations,
                track_memory=track_memory,
                gc_collect=gc_collect,
            )

            # Log results
            log_func = getattr(logger, log_level)
            log_func(f"Benchmark: {result}")

            # Return the result of the last iteration
            return benchmark_func()

        return cast(F, wrapper)

    return decorator


def profile(
    track_memory: bool = False,
    gc_collect: bool = True,
    print_stats: bool = True,
    sort_by: str = "cumulative",
    limit: int = 20,
    strip_dirs: bool = True,
    log_level: str = "info",
) -> Callable[[F], F]:
    """Decorator for profiling functions.

    Args:
        track_memory: Whether to track memory usage
        gc_collect: Whether to collect garbage before profiling
        print_stats: Whether to print function call statistics
        sort_by: The field to sort by (cumulative, time, calls, etc.)
        limit: The maximum number of functions to show
        strip_dirs: Whether to strip directory paths from filenames
        log_level: The log level to use for reporting results

    Returns:
        A decorator function
    """

    def decorator(func: F) -> F:
        """Decorator function.

        Args:
            func: The function to decorate

        Returns:
            The decorated function
        """
        profile_name = f"{func.__module__}.{func.__name__}"

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Wrapper function.

            Args:
                *args: Positional arguments
                **kwargs: Keyword arguments

            Returns:
                The result of the function
            """
            # Create profiler
            prof = Profiler(profile_name)

            # Define function to profile
            def profile_func() -> Any:
                return func(*args, **kwargs)

            # Run profiler
            result = prof.run(
                profile_func,
                track_memory=track_memory,
                gc_collect=gc_collect,
            )

            # Print statistics if requested
            if print_stats:
                result.print_stats(
                    sort_by=sort_by,
                    limit=limit,
                    strip_dirs=strip_dirs,
                )

            # Log memory statistics if available
            if result.memory_stats and log_level:
                log_func = getattr(logger, log_level)
                memory_str = ", ".join(
                    f"{k}: {BenchmarkResult.format_bytes(v)}"
                    for k, v in result.memory_stats.items()
                    if k.endswith("_bytes")
                )
                log_func(f"Profile '{profile_name}' memory usage: {memory_str}")

            # Return the result of the profiled function
            return profile_func()

        return cast(F, wrapper)

    return decorator


class BenchmarkSuite:
    """A suite of benchmarks for comparing performance.

    This class provides methods for running multiple benchmarks and comparing
    their performance.
    """

    def __init__(self, name: str):
        """Initialize the benchmark suite.

        Args:
            name: The name of the benchmark suite
        """
        self.name = name
        self.benchmarks: Dict[str, Callable[[], Any]] = {}
        self.results: Dict[str, BenchmarkResult] = {}

    def add_benchmark(self, name: str, func: Callable[[], Any]) -> None:
        """Add a benchmark to the suite.

        Args:
            name: The name of the benchmark
            func: The function to benchmark
        """
        self.benchmarks[name] = func

    def run_all(
        self,
        iterations: int = 1,
        warmup_iterations: int = 0,
        track_memory: bool = False,
        gc_collect: bool = True,
    ) -> Dict[str, BenchmarkResult]:
        """Run all benchmarks in the suite.

        Args:
            iterations: The number of iterations to run
            warmup_iterations: The number of warmup iterations to run
            track_memory: Whether to track memory usage
            gc_collect: Whether to collect garbage before each iteration

        Returns:
            A dictionary mapping benchmark names to results
        """
        self.results = {}
        for name, func in self.benchmarks.items():
            benchmark = Benchmark(name)
            result = benchmark.run(
                func,
                iterations=iterations,
                warmup_iterations=warmup_iterations,
                track_memory=track_memory,
                gc_collect=gc_collect,
            )
            self.results[name] = result
        return self.results

    def compare(
        self, baseline: Optional[str] = None, metrics: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, float]]:
        """Compare benchmark results.

        Args:
            baseline: The name of the baseline benchmark to compare against
            metrics: The metrics to compare (default: execution_time, memory_usage)

        Returns:
            A dictionary mapping benchmark names to comparison results
        """
        if not self.results:
            raise ValueError("No benchmark results to compare")

        if baseline is None:
            # Use the first benchmark as the baseline
            baseline = next(iter(self.results.keys()))

        if baseline not in self.results:
            raise ValueError(f"Baseline benchmark '{baseline}' not found")

        if metrics is None:
            metrics = ["execution_time", "memory_usage"]

        baseline_result = self.results[baseline]
        comparisons: Dict[str, Dict[str, float]] = {}

        for name, result in self.results.items():
            if name == baseline:
                continue

            comparison: Dict[str, float] = {}
            for metric in metrics:
                if metric == "execution_time":
                    baseline_value = baseline_result.execution_time
                    current_value = result.execution_time
                    if baseline_value > 0:
                        comparison[metric] = current_value / baseline_value
                elif metric == "memory_usage":
                    if (
                        baseline_result.memory_usage is not None
                        and result.memory_usage is not None
                    ):
                        baseline_value = baseline_result.memory_usage
                        current_value = result.memory_usage
                        if baseline_value > 0:
                            comparison[metric] = current_value / baseline_value
                elif (
                    metric in baseline_result.custom_metrics
                    and metric in result.custom_metrics
                ):
                    baseline_value = baseline_result.custom_metrics[metric]
                    current_value = result.custom_metrics[metric]
                    if isinstance(baseline_value, (int, float)) and isinstance(
                        current_value, (int, float)
                    ):
                        if baseline_value > 0:
                            comparison[metric] = current_value / baseline_value

            comparisons[name] = comparison

        return comparisons

    def print_results(self) -> None:
        """Print benchmark results."""
        if not self.results:
            print(f"Benchmark suite '{self.name}': No results")
            return

        print(f"Benchmark suite '{self.name}':")
        for name, result in self.results.items():
            print(f"\n{result}")

    def print_comparison(
        self, baseline: Optional[str] = None, metrics: Optional[List[str]] = None
    ) -> None:
        """Print benchmark comparison.

        Args:
            baseline: The name of the baseline benchmark to compare against
            metrics: The metrics to compare (default: execution_time, memory_usage)
        """
        if not self.results:
            print(f"Benchmark suite '{self.name}': No results to compare")
            return

        comparisons = self.compare(baseline=baseline, metrics=metrics)
        if not comparisons:
            print(f"Benchmark suite '{self.name}': No comparisons available")
            return

        if baseline is None:
            baseline = next(iter(self.results.keys()))

        print(f"Benchmark suite '{self.name}' comparison (baseline: {baseline}):")
        for name, comparison in comparisons.items():
            print(f"\n{name}:")
            for metric, ratio in comparison.items():
                if metric == "execution_time":
                    faster_slower = "slower" if ratio > 1 else "faster"
                    print(
                        f"  Execution time: {ratio:.2f}x ({abs(1 - ratio) * 100:.1f}% {faster_slower})"
                    )
                elif metric == "memory_usage":
                    more_less = "more" if ratio > 1 else "less"
                    print(
                        f"  Memory usage: {ratio:.2f}x ({abs(1 - ratio) * 100:.1f}% {more_less})"
                    )
                else:
                    print(f"  {metric}: {ratio:.2f}x")


def get_memory_usage() -> Dict[str, Any]:
    """Get current memory usage.

    Returns:
        A dictionary with memory usage information
    """
    try:
        import psutil  # type: ignore

        process = psutil.Process()
        memory_info = process.memory_info()
        return {
            "rss_bytes": memory_info.rss,  # Resident Set Size
            "vms_bytes": memory_info.vms,  # Virtual Memory Size
            "percent": process.memory_percent(),  # Percentage of total system memory
        }
    except ImportError:
        return {
            "error": "psutil not installed. Install with 'pip install psutil'",
        }


def get_cpu_usage() -> Dict[str, Any]:
    """Get current CPU usage.

    Returns:
        A dictionary with CPU usage information
    """
    try:
        import psutil

        process = psutil.Process()
        return {
            "cpu_percent": process.cpu_percent(interval=0.1),  # CPU usage percentage
            "cpu_times": process.cpu_times()._asdict(),  # CPU times
            "num_threads": process.num_threads(),  # Number of threads
        }
    except ImportError:
        return {
            "error": "psutil not installed. Install with 'pip install psutil'",
        }


def get_system_info() -> Dict[str, Any]:
    """Get system information.

    Returns:
        A dictionary with system information
    """
    try:
        import psutil

        return {
            "cpu_count": psutil.cpu_count(logical=True),  # Number of logical CPUs
            "cpu_count_physical": psutil.cpu_count(
                logical=False
            ),  # Number of physical CPUs
            "memory_total_bytes": psutil.virtual_memory().total,  # Total memory
            "memory_available_bytes": psutil.virtual_memory().available,  # Available memory
            "disk_usage": {
                path.mountpoint: {
                    "total_bytes": usage.total,
                    "used_bytes": usage.used,
                    "free_bytes": usage.free,
                    "percent": usage.percent,
                }
                for path, usage in {
                    path: psutil.disk_usage(path.mountpoint)
                    for path in psutil.disk_partitions(all=False)
                }.items()
            },
        }
    except ImportError:
        return {
            "error": "psutil not installed. Install with 'pip install psutil'",
        }
