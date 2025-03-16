"""Example demonstrating the PepperPy metrics module.

This example shows how to use the metrics module to measure and track performance
metrics, including execution time, memory usage, and custom metrics.
"""

import asyncio
import random
from typing import Dict, List, Optional

import numpy as np

from pepperpy.infra.logging import configure_logging, get_logger
from pepperpy.infra.metrics import (
    MetricCategory,
    benchmark,
    get_memory_usage,
    get_system_info,
    measure_memory,
    measure_time,
    performance_tracker,
    report_custom_metric,
)

# Configure logging
configure_logging(level="INFO")
logger = get_logger(__name__)


# Example functions to benchmark
def fibonacci_recursive(n: int) -> int:
    """Calculate the nth Fibonacci number recursively.

    Args:
        n: The index of the Fibonacci number to calculate

    Returns:
        The nth Fibonacci number
    """
    if n <= 1:
        return n
    return fibonacci_recursive(n - 1) + fibonacci_recursive(n - 2)


def fibonacci_iterative(n: int) -> int:
    """Calculate the nth Fibonacci number iteratively.

    Args:
        n: The index of the Fibonacci number to calculate

    Returns:
        The nth Fibonacci number
    """
    if n <= 1:
        return n

    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b


def fibonacci_memoized(n: int, memo: Optional[Dict[int, int]] = None) -> int:
    """Calculate the nth Fibonacci number using memoization.

    Args:
        n: The index of the Fibonacci number to calculate
        memo: Memoization dictionary

    Returns:
        The nth Fibonacci number
    """
    if memo is None:
        memo = {}

    if n in memo:
        return memo[n]

    if n <= 1:
        return n

    memo[n] = fibonacci_memoized(n - 1, memo) + fibonacci_memoized(n - 2, memo)
    return memo[n]


def generate_random_data(size: int) -> List[float]:
    """Generate a list of random floats.

    Args:
        size: The size of the list to generate

    Returns:
        A list of random floats
    """
    return [random.random() for _ in range(size)]


def bubble_sort(data: List[float]) -> List[float]:
    """Sort a list using bubble sort.

    Args:
        data: The list to sort

    Returns:
        The sorted list
    """
    result = data.copy()
    n = len(result)
    for i in range(n):
        for j in range(0, n - i - 1):
            if result[j] > result[j + 1]:
                result[j], result[j + 1] = result[j + 1], result[j]
    return result


def quick_sort(data: List[float]) -> List[float]:
    """Sort a list using quick sort.

    Args:
        data: The list to sort

    Returns:
        The sorted list
    """
    result = data.copy()
    if len(result) <= 1:
        return result
    pivot = result[len(result) // 2]
    left = [x for x in result if x < pivot]
    middle = [x for x in result if x == pivot]
    right = [x for x in result if x > pivot]
    return quick_sort(left) + middle + quick_sort(right)


def python_sort(data: List[float]) -> List[float]:
    """Sort a list using Python's built-in sort.

    Args:
        data: The list to sort

    Returns:
        The sorted list
    """
    result = data.copy()
    result.sort()
    return result


def cpu_intensive_task(size: int = 1000) -> float:
    """Perform a CPU-intensive task.

    Args:
        size: The size of the data to process

    Returns:
        The result of the computation
    """
    result = 0.0
    for i in range(size):
        result += np.sin(i) * np.cos(i)
    return result


def memory_intensive_task(size: int = 1000000) -> List[float]:
    """Perform a memory-intensive task.

    Args:
        size: The size of the data to generate

    Returns:
        The generated data
    """
    return [random.random() for _ in range(size)]


async def async_task(delay: float = 0.1) -> None:
    """Perform an asynchronous task.

    Args:
        delay: The delay in seconds
    """
    await asyncio.sleep(delay)


def example_measure_time() -> None:
    """Example demonstrating the measure_time context manager."""
    logger.info("=== Measure Time Example ===")

    # Measure execution time of different Fibonacci implementations
    n = 30

    with measure_time("fibonacci_recursive") as timer:
        result = fibonacci_recursive(n)
    logger.info(
        f"Recursive Fibonacci({n}) = {result}, took {timer.elapsed_time:.6f} seconds"
    )

    with measure_time("fibonacci_iterative") as timer:
        result = fibonacci_iterative(n)
    logger.info(
        f"Iterative Fibonacci({n}) = {result}, took {timer.elapsed_time:.6f} seconds"
    )

    with measure_time("fibonacci_memoized") as timer:
        result = fibonacci_memoized(n)
    logger.info(
        f"Memoized Fibonacci({n}) = {result}, took {timer.elapsed_time:.6f} seconds"
    )


def example_measure_memory() -> None:
    """Example demonstrating the measure_memory context manager."""
    logger.info("=== Measure Memory Example ===")

    # Measure memory usage of different operations
    with measure_memory("small_list") as tracker:
        data = [i for i in range(10000)]
    logger.info(f"Creating a small list used {tracker.memory_used} bytes")

    with measure_memory("large_list") as tracker:
        data = [i for i in range(1000000)]
    logger.info(f"Creating a large list used {tracker.memory_used} bytes")

    with measure_memory("numpy_array") as tracker:
        data = np.arange(1000000)
    logger.info(f"Creating a NumPy array used {tracker.memory_used} bytes")


def example_performance_tracker() -> None:
    """Example demonstrating the performance_tracker context manager."""
    logger.info("=== Performance Tracker Example ===")

    # Track performance of sorting algorithms
    data_size = 1000
    data = generate_random_data(data_size)

    logger.info(f"Sorting {data_size} random numbers using different algorithms...")

    with performance_tracker("bubble_sort", track_memory=True) as perf:
        result = bubble_sort(data)
        perf.add_custom_metric("data_size", data_size)

    with performance_tracker("quick_sort", track_memory=True) as perf:
        result = quick_sort(data)
        perf.add_custom_metric("data_size", data_size)

    with performance_tracker("python_sort", track_memory=True) as perf:
        result = python_sort(data)
        perf.add_custom_metric("data_size", data_size)


def example_benchmark_decorator() -> None:
    """Example demonstrating the benchmark decorator."""
    logger.info("=== Benchmark Decorator Example ===")

    n = 30

    @benchmark(iterations=3, warmup_iterations=1, track_memory=True)
    def calculate_fibonacci_recursive(n: int) -> int:
        return fibonacci_recursive(n)

    @benchmark(iterations=3, warmup_iterations=1, track_memory=True)
    def calculate_fibonacci_iterative(n: int) -> int:
        return fibonacci_iterative(n)

    @benchmark(iterations=3, warmup_iterations=1, track_memory=True)
    def calculate_fibonacci_memoized(n: int) -> int:
        return fibonacci_memoized(n)

    logger.info(f"Benchmarking Fibonacci({n}) implementations...")

    recursive_result = calculate_fibonacci_recursive(n)
    logger.info(f"Recursive result: {recursive_result}")

    iterative_result = calculate_fibonacci_iterative(n)
    logger.info(f"Iterative result: {iterative_result}")

    memoized_result = calculate_fibonacci_memoized(n)
    logger.info(f"Memoized result: {memoized_result}")


def example_custom_metrics() -> None:
    """Example demonstrating custom metrics."""
    logger.info("=== Custom Metrics Example ===")

    # Report custom metrics
    report_custom_metric(
        name="api_requests",
        value=1250,
        unit="requests",
        category=MetricCategory.BUSINESS,
        tags={"endpoint": "/api/v1/users"},
    )

    report_custom_metric(
        name="response_time",
        value=0.125,
        unit="seconds",
        category=MetricCategory.PERFORMANCE,
        tags={"endpoint": "/api/v1/users"},
    )

    report_custom_metric(
        name="error_rate",
        value=0.02,
        unit="percent",
        category=MetricCategory.SYSTEM,
        tags={"endpoint": "/api/v1/users"},
    )

    logger.info("Custom metrics reported to telemetry")


def example_system_info() -> None:
    """Example demonstrating system information retrieval."""
    logger.info("=== System Information Example ===")

    # Get memory usage
    memory_usage = get_memory_usage()
    logger.info(f"Current memory usage: {memory_usage['current_formatted']}")
    logger.info(f"Peak memory usage: {memory_usage['peak_formatted']}")

    # Get system information
    system_info = get_system_info()
    logger.info(f"Platform: {system_info['platform']}")
    logger.info(f"Processor: {system_info['processor']}")
    logger.info(f"Python version: {system_info['python_version']}")
    logger.info(
        f"Memory total: {system_info['memory_total_bytes'] / (1024 * 1024 * 1024):.2f} GB"
    )
    logger.info(
        f"Memory available: {system_info['memory_available_bytes'] / (1024 * 1024 * 1024):.2f} GB"
    )
    logger.info(f"Memory used: {system_info['memory_used_percent']}%")
    logger.info(f"CPU count: {system_info['cpu_count']}")
    logger.info(f"CPU usage: {system_info['cpu_percent']}%")


async def main() -> None:
    """Run all examples."""
    logger.info("Starting metrics examples")

    example_measure_time()
    example_measure_memory()
    example_performance_tracker()
    example_benchmark_decorator()
    example_custom_metrics()
    example_system_info()

    logger.info("All examples completed")


if __name__ == "__main__":
    asyncio.run(main())
