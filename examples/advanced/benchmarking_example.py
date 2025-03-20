#!/usr/bin/env python
"""Example demonstrating performance benchmarking and profiling tools.

This example demonstrates the usage of PepperPy's benchmarking and profiling tools
for measuring code performance, including execution time, memory usage, and custom
metrics. It shows how to use different benchmarking features and analyze results.

Purpose:
    Demonstrate how to use benchmarking and profiling tools to measure and
    optimize code performance, including execution time, memory usage, and
    function call statistics.

Requirements:
    - Python 3.9+
    - PepperPy library
    - psutil (optional, for memory usage tracking)

Usage:
    1. Install dependencies:
       pip install -r requirements.txt

    2. Run the example:
       python benchmarking_example.py
"""

import asyncio
import json
import os
import random
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

from pepperpy.infra.logging import configure_logging, get_logger
from pepperpy.infra.metrics import (
    PerformanceResult,
    PerformanceTracker,
    benchmark,
    get_memory_usage,
    get_system_info,
    measure_time,
)

# Configure logging
configure_logging(level="INFO")
logger = get_logger(__name__)

# Create output directory
output_dir = Path("outputs/benchmarking_example")
os.makedirs(output_dir, exist_ok=True)


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
        memo: A dictionary to store previously calculated values

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
    """Generate random data for sorting.

    Args:
        size: The size of the data to generate

    Returns:
        A list of random floats
    """
    return [random.random() for _ in range(size)]


def bubble_sort(data: List[float]) -> List[float]:
    """Sort data using bubble sort.

    Args:
        data: The data to sort

    Returns:
        The sorted data
    """
    result = data.copy()
    n = len(result)
    for i in range(n):
        for j in range(0, n - i - 1):
            if result[j] > result[j + 1]:
                result[j], result[j + 1] = result[j + 1], result[j]
    return result


def quick_sort(data: List[float]) -> List[float]:
    """Sort data using quick sort.

    Args:
        data: The data to sort

    Returns:
        The sorted data
    """
    if len(data) <= 1:
        return data
    result = data.copy()
    pivot = result[len(result) // 2]
    left = [x for x in result if x < pivot]
    middle = [x for x in result if x == pivot]
    right = [x for x in result if x > pivot]
    return quick_sort(left) + middle + quick_sort(right)


def python_sort(data: List[float]) -> List[float]:
    """Sort data using Python's built-in sort.

    Args:
        data: The data to sort

    Returns:
        The sorted data
    """
    result = data.copy()
    result.sort()
    return result


@benchmark(track_memory=True)
def cpu_intensive_task(size: int = 1000) -> float:
    """A CPU-intensive task for benchmarking.

    Args:
        size: The size of the array to process

    Returns:
        The sum of sines of the array elements
    """
    arr = np.linspace(0, 10, size)
    return float(np.sum(np.sin(arr)))


@benchmark(track_memory=True)
def memory_intensive_task(size: int = 1000000) -> List[float]:
    """A memory-intensive task for benchmarking.

    Args:
        size: The size of the list to create

    Returns:
        A list of random numbers
    """
    return [np.random.random() for _ in range(size)]


@benchmark(track_memory=True)
async def async_task(delay: float = 0.1) -> None:
    """An asynchronous task for benchmarking.

    Args:
        delay: The delay in seconds
    """
    await asyncio.sleep(delay)


def example_basic_benchmark() -> None:
    """Example of basic benchmarking."""
    logger.info("Running basic benchmark example")

    # Create a performance tracker
    tracker = PerformanceTracker("Basic Example")

    # Run a simple benchmark
    tracker.start(track_memory=True)
    for _ in range(5):  # 5 iterations
        cpu_intensive_task(1000)
    result = tracker.stop(track_memory=True)

    # Print results
    logger.info("Basic benchmark results:")
    logger.info(f"  Execution time: {result.execution_time:.4f} seconds")
    if result.memory_usage:
        logger.info(f"  Memory usage: {result.memory_usage / 1024:.2f} KB")
    logger.info(f"  Time per iteration: {result.time_per_iteration:.4f} seconds")


def example_custom_metrics() -> None:
    """Example of using custom metrics in benchmarks."""
    logger.info("Running custom metrics example")

    # Create a performance tracker with custom metrics
    tracker = PerformanceTracker("Custom Metrics Example")

    # Start tracking
    tracker.start(track_memory=True)

    # Run task
    result = memory_intensive_task(100000)

    # Add custom metrics
    tracker.add_custom_metric("result_size", len(result))

    # Stop tracking
    perf_result = tracker.stop(track_memory=True)

    # Print results including custom metrics
    logger.info("Custom metrics benchmark results:")
    logger.info(f"  Execution time: {perf_result.execution_time:.4f} seconds")
    for metric_name, metric_value in perf_result.custom_metrics.items():
        logger.info(f"  {metric_name}: {metric_value}")


async def example_async_benchmark() -> None:
    """Example of benchmarking asynchronous code."""
    logger.info("Running async benchmark example")

    # Create a performance tracker for async code
    tracker = PerformanceTracker("Async Example")

    # Run async benchmark
    tracker.start()
    for _ in range(5):  # 5 iterations
        await async_task(0.1)
    result = tracker.stop()

    # Print results
    logger.info("Async benchmark results:")
    logger.info(f"  Execution time: {result.execution_time:.4f} seconds")
    logger.info(f"  Time per iteration: {result.time_per_iteration:.4f} seconds")


def example_comparative_benchmark() -> None:
    """Example of comparing different implementations."""
    logger.info("Running comparative benchmark example")

    # Create benchmarks for different implementations
    sizes = [100, 1000, 10000]
    results: Dict[str, List[PerformanceResult]] = {
        "numpy": [],
        "python": [],
    }

    for size in sizes:
        # NumPy implementation
        numpy_tracker = PerformanceTracker(f"NumPy (size={size})")
        numpy_tracker.start()
        for _ in range(5):  # 5 iterations
            np.sum(np.sin(np.linspace(0, 10, size)))
        numpy_result = numpy_tracker.stop()
        results["numpy"].append(numpy_result)

        # Pure Python implementation
        python_tracker = PerformanceTracker(f"Python (size={size})")
        python_tracker.start()
        for _ in range(5):  # 5 iterations
            sum(np.sin(x) for x in np.linspace(0, 10, size))
        python_result = python_tracker.stop()
        results["python"].append(python_result)

    # Print comparative results
    logger.info("Comparative benchmark results:")
    for size_idx, size in enumerate(sizes):
        logger.info(f"\nSize: {size}")
        for impl in ["numpy", "python"]:
            result = results[impl][size_idx]
            logger.info(
                f"  {impl:6s}: {result.execution_time:.6f} seconds "
                f"(per iteration: {result.time_per_iteration:.6f})"
            )


def example_benchmark_decorator() -> None:
    """Example demonstrating the benchmark decorator."""
    logger.info("=== Benchmark Decorator Example ===")

    @benchmark(iterations=3, warmup_iterations=1, track_memory=True)
    def calculate_fibonacci_recursive(n: int) -> int:
        """Calculate Fibonacci number recursively with benchmarking."""
        return fibonacci_recursive(n)

    @benchmark(iterations=3, warmup_iterations=1, track_memory=True)
    def calculate_fibonacci_iterative(n: int) -> int:
        """Calculate Fibonacci number iteratively with benchmarking."""
        return fibonacci_iterative(n)

    @benchmark(iterations=3, warmup_iterations=1, track_memory=True)
    def calculate_fibonacci_memoized(n: int) -> int:
        """Calculate Fibonacci number with memoization and benchmarking."""
        return fibonacci_memoized(n)

    # Run benchmarks
    n = 30
    logger.info(f"Calculating Fibonacci({n}) using different algorithms...")

    recursive_result = calculate_fibonacci_recursive(n)
    logger.info(f"Recursive result: {recursive_result}")

    iterative_result = calculate_fibonacci_iterative(n)
    logger.info(f"Iterative result: {iterative_result}")

    memoized_result = calculate_fibonacci_memoized(n)
    logger.info(f"Memoized result: {memoized_result}")


def example_context_managers() -> None:
    """Example demonstrating the context managers."""
    logger.info("=== Context Managers Example ===")

    # Benchmark sorting algorithms
    data_size = 1000
    data = generate_random_data(data_size)

    logger.info(f"Sorting {data_size} random numbers using different algorithms...")

    with measure_time("bubble_sort") as timer:
        bubble_sort_result = bubble_sort(data)
    logger.info(f"Bubble sort took {timer.elapsed_time:.6f} seconds")

    with measure_time("quick_sort") as timer:
        quick_sort_result = quick_sort(data)
    logger.info(f"Quick sort took {timer.elapsed_time:.6f} seconds")

    with measure_time("python_sort") as timer:
        python_sort_result = python_sort(data)
    logger.info(f"Python sort took {timer.elapsed_time:.6f} seconds")

    # Verify results
    logger.info(
        f"All results match: {bubble_sort_result == quick_sort_result == python_sort_result}"
    )


def example_performance_tracker() -> None:
    """Example demonstrating the PerformanceTracker class."""
    logger.info("=== Performance Tracker Example ===")

    # Create performance trackers for sorting algorithms
    data_size = 1000
    data = generate_random_data(data_size)

    logger.info(f"Benchmarking sorting algorithms with {data_size} random numbers...")

    # Track bubble sort performance
    bubble_tracker = PerformanceTracker("bubble_sort")
    bubble_tracker.start(track_memory=True)
    bubble_sort(data)
    bubble_result = bubble_tracker.stop(track_memory=True)

    # Track quick sort performance
    quick_tracker = PerformanceTracker("quick_sort")
    quick_tracker.start(track_memory=True)
    quick_sort(data)
    quick_result = quick_tracker.stop(track_memory=True)

    # Track Python's built-in sort performance
    python_tracker = PerformanceTracker("python_sort")
    python_tracker.start(track_memory=True)
    python_sort(data)
    python_result = python_tracker.stop(track_memory=True)

    # Print results
    logger.info(f"Bubble sort: {bubble_result}")
    logger.info(f"Quick sort: {quick_result}")
    logger.info(f"Python sort: {python_result}")

    # Save results
    result_path = output_dir / "sorting_benchmark_results.json"
    with open(result_path, "w") as f:
        json.dump(
            {
                "bubble_sort": {
                    "execution_time": bubble_result.execution_time,
                    "time_per_iteration": bubble_result.time_per_iteration,
                    "memory_usage": bubble_result.memory_usage,
                },
                "quick_sort": {
                    "execution_time": quick_result.execution_time,
                    "time_per_iteration": quick_result.time_per_iteration,
                    "memory_usage": quick_result.memory_usage,
                },
                "python_sort": {
                    "execution_time": python_result.execution_time,
                    "time_per_iteration": python_result.time_per_iteration,
                    "memory_usage": python_result.memory_usage,
                },
            },
            f,
            indent=2,
        )
    logger.info(f"Results saved to {result_path}")


def example_system_info() -> None:
    """Example demonstrating system information utilities."""
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

    # Save system information
    info_path = output_dir / "system_info.json"
    with open(info_path, "w") as f:
        json.dump(
            {
                "memory_usage": {
                    "current_bytes": memory_usage["current_bytes"],
                    "peak_bytes": memory_usage["peak_bytes"],
                    "current_formatted": memory_usage["current_formatted"],
                    "peak_formatted": memory_usage["peak_formatted"],
                },
                "system_info": {
                    "platform": system_info["platform"],
                    "processor": system_info["processor"],
                    "python_version": system_info["python_version"],
                    "memory_total_bytes": system_info["memory_total_bytes"],
                    "memory_available_bytes": system_info["memory_available_bytes"],
                    "memory_used_percent": system_info["memory_used_percent"],
                    "cpu_count": system_info["cpu_count"],
                    "cpu_percent": system_info["cpu_percent"],
                },
            },
            f,
            indent=2,
        )
    logger.info(f"System information saved to {info_path}")


async def main() -> None:
    """Run all benchmarking examples."""
    logger.info("Starting benchmarking and profiling examples...")

    # Run examples
    example_basic_benchmark()
    example_custom_metrics()
    await example_async_benchmark()
    example_comparative_benchmark()
    example_benchmark_decorator()
    example_context_managers()
    example_performance_tracker()
    example_system_info()

    logger.info("All benchmarking and profiling examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
