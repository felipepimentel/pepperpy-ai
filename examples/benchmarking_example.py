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
import gc
import json
import os
import random
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from pepperpy.core.benchmarking import (
    Benchmark,
    BenchmarkResult,
    BenchmarkSuite,
    Profiler,
    benchmark,
    benchmark_context,
    get_cpu_usage,
    get_memory_usage,
    get_system_info,
    profile,
)
from pepperpy.utils.logging import configure_logging, get_logger

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


@profile(track_memory=True)
def cpu_intensive_task(size: int = 1000) -> float:
    """A CPU-intensive task for benchmarking.

    Args:
        size: The size of the array to process

    Returns:
        The sum of sines of the array elements
    """
    arr = np.linspace(0, 10, size)
    return float(np.sum(np.sin(arr)))


@profile(track_memory=True)
def memory_intensive_task(size: int = 1000000) -> List[float]:
    """A memory-intensive task for benchmarking.

    Args:
        size: The size of the list to create

    Returns:
        A list of random numbers
    """
    return [np.random.random() for _ in range(size)]


@profile(track_memory=True)
async def async_task(delay: float = 0.1) -> None:
    """An asynchronous task for benchmarking.

    Args:
        delay: The delay in seconds
    """
    await asyncio.sleep(delay)


def example_basic_benchmark() -> None:
    """Example of basic benchmarking."""
    logger.info("Running basic benchmark example")

    # Create a benchmark
    benchmark = Benchmark("Basic Example")

    # Run a simple benchmark
    result = benchmark.run(
        lambda: cpu_intensive_task(1000),
        iterations=5,
        warmup_iterations=1,
        track_memory=True,
    )

    # Print results
    logger.info("Basic benchmark results:")
    logger.info(f"  Mean execution time: {result.execution_time.mean:.4f} seconds")
    logger.info(f"  Mean memory usage: {result.memory_usage.mean / 1024:.2f} KB")
    logger.info(f"  Standard deviation: {result.execution_time.std:.4f} seconds")


def example_custom_metrics() -> None:
    """Example of using custom metrics in benchmarks."""
    logger.info("Running custom metrics example")

    # Create a benchmark with custom metrics
    benchmark = Benchmark("Custom Metrics Example")

    def task_with_metrics() -> Dict[str, Any]:
        start_memory = gc.get_stats()[0].size
        result = memory_intensive_task(100000)
        end_memory = gc.get_stats()[0].size
        return {
            "result_size": len(result),
            "memory_increase": end_memory - start_memory,
        }

    # Run benchmark with custom metrics
    result = benchmark.run(
        task_with_metrics,
        iterations=3,
        track_memory=True,
    )

    # Print results including custom metrics
    logger.info("Custom metrics benchmark results:")
    logger.info(f"  Mean execution time: {result.execution_time.mean:.4f} seconds")
    for metric, values in result.metrics.items():
        mean_value = sum(values) / len(values)
        logger.info(f"  Mean {metric}: {mean_value:.2f}")


async def example_async_benchmark() -> None:
    """Example of benchmarking asynchronous code."""
    logger.info("Running async benchmark example")

    # Create a benchmark for async code
    benchmark = Benchmark("Async Example")

    # Run async benchmark
    result = await benchmark.run_async(
        lambda: async_task(0.1),
        iterations=5,
    )

    # Print results
    logger.info("Async benchmark results:")
    logger.info(f"  Mean execution time: {result.execution_time.mean:.4f} seconds")
    logger.info(f"  Min execution time: {result.execution_time.min:.4f} seconds")
    logger.info(f"  Max execution time: {result.execution_time.max:.4f} seconds")


def example_comparative_benchmark() -> None:
    """Example of comparing different implementations."""
    logger.info("Running comparative benchmark example")

    # Create benchmarks for different implementations
    sizes = [100, 1000, 10000]
    results: Dict[str, List[BenchmarkResult]] = {
        "numpy": [],
        "python": [],
    }

    for size in sizes:
        # NumPy implementation
        numpy_bench = Benchmark(f"NumPy (size={size})")
        numpy_result = numpy_bench.run(
            lambda: np.sum(np.sin(np.linspace(0, 10, size))),
            iterations=5,
        )
        results["numpy"].append(numpy_result)

        # Pure Python implementation
        python_bench = Benchmark(f"Python (size={size})")
        python_result = python_bench.run(
            lambda: sum(np.sin(x) for x in np.linspace(0, 10, size)),
            iterations=5,
        )
        results["python"].append(python_result)

    # Print comparative results
    logger.info("Comparative benchmark results:")
    for size_idx, size in enumerate(sizes):
        logger.info(f"\nSize: {size}")
        for impl in ["numpy", "python"]:
            result = results[impl][size_idx]
            logger.info(
                f"  {impl:6s}: {result.execution_time.mean:.6f} seconds "
                f"(±{result.execution_time.std:.6f})"
            )


@profile(track_memory=True)
def example_profile_decorator() -> None:
    """Example of using the @profile decorator."""
    logger.info("Running profile decorator example")

    # Call the functions to see the profiling output
    cpu_intensive_task(1000)
    memory_intensive_task(1000)


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


def example_benchmark_context() -> None:
    """Example demonstrating the benchmark context manager."""
    logger.info("=== Benchmark Context Manager Example ===")

    # Benchmark sorting algorithms
    data_size = 1000
    data = generate_random_data(data_size)

    logger.info(f"Sorting {data_size} random numbers using different algorithms...")

    with benchmark_context("bubble_sort", track_memory=True):
        bubble_sort_result = bubble_sort(data)

    with benchmark_context("quick_sort", track_memory=True):
        quick_sort_result = quick_sort(data)

    with benchmark_context("python_sort", track_memory=True):
        python_sort_result = python_sort(data)

    # Verify results
    logger.info(
        f"All results match: {bubble_sort_result == quick_sort_result == python_sort_result}"
    )


def example_benchmark_class() -> None:
    """Example demonstrating the Benchmark class."""
    logger.info("=== Benchmark Class Example ===")

    # Create benchmarks for sorting algorithms
    data_size = 1000
    data = generate_random_data(data_size)

    logger.info(f"Benchmarking sorting algorithms with {data_size} random numbers...")

    # Benchmark bubble sort
    bubble_benchmark = Benchmark("bubble_sort")
    bubble_result = bubble_benchmark.run(
        lambda: bubble_sort(data),
        iterations=3,
        warmup_iterations=1,
        track_memory=True,
    )

    # Benchmark quick sort
    quick_benchmark = Benchmark("quick_sort")
    quick_result = quick_benchmark.run(
        lambda: quick_sort(data),
        iterations=3,
        warmup_iterations=1,
        track_memory=True,
    )

    # Benchmark Python's built-in sort
    python_benchmark = Benchmark("python_sort")
    python_result = python_benchmark.run(
        lambda: python_sort(data),
        iterations=3,
        warmup_iterations=1,
        track_memory=True,
    )

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
                    "execution_time": bubble_result.execution_time.mean,
                    "time_per_iteration": bubble_result.time_per_iteration,
                    "memory_usage": bubble_result.memory_usage.mean,
                },
                "quick_sort": {
                    "execution_time": quick_result.execution_time.mean,
                    "time_per_iteration": quick_result.time_per_iteration,
                    "memory_usage": quick_result.memory_usage.mean,
                },
                "python_sort": {
                    "execution_time": python_result.execution_time.mean,
                    "time_per_iteration": python_result.time_per_iteration,
                    "memory_usage": python_result.memory_usage.mean,
                },
            },
            f,
            indent=2,
        )
    logger.info(f"Results saved to {result_path}")


def example_benchmark_suite() -> None:
    """Example demonstrating the BenchmarkSuite class."""
    logger.info("=== Benchmark Suite Example ===")

    # Create benchmark suite for Fibonacci algorithms
    suite = BenchmarkSuite("fibonacci_algorithms")

    n = 30
    suite.add_benchmark("recursive", lambda: fibonacci_recursive(n))
    suite.add_benchmark("iterative", lambda: fibonacci_iterative(n))
    suite.add_benchmark("memoized", lambda: fibonacci_memoized(n))

    # Run all benchmarks
    logger.info(f"Running benchmark suite for Fibonacci({n})...")
    results = suite.run_all(iterations=3, warmup_iterations=1, track_memory=True)

    # Print results
    suite.print_results()

    # Print comparison (using iterative as baseline)
    suite.print_comparison(baseline="iterative")

    # Save results
    result_path = output_dir / "fibonacci_benchmark_suite.json"
    with open(result_path, "w") as f:
        json.dump(
            {
                name: {
                    "execution_time": result.execution_time.mean,
                    "time_per_iteration": result.time_per_iteration,
                    "memory_usage": result.memory_usage.mean,
                }
                for name, result in results.items()
            },
            f,
            indent=2,
        )
    logger.info(f"Results saved to {result_path}")


def example_profiler_class() -> None:
    """Example demonstrating the Profiler class."""
    logger.info("=== Profiler Class Example ===")

    # Create profilers for sorting algorithms
    data_size = 1000
    data = generate_random_data(data_size)

    logger.info(f"Profiling sorting algorithms with {data_size} random numbers...")

    # Profile bubble sort
    bubble_profiler = Profiler("bubble_sort")
    bubble_result = bubble_profiler.run(
        lambda: bubble_sort(data),
        track_memory=True,
    )

    # Profile quick sort
    quick_profiler = Profiler("quick_sort")
    quick_result = quick_profiler.run(
        lambda: quick_sort(data),
        track_memory=True,
    )

    # Print results
    logger.info("Bubble sort profile:")
    bubble_result.print_stats(limit=10)

    logger.info("Quick sort profile:")
    quick_result.print_stats(limit=10)

    # Save profile results
    bubble_profile_path = output_dir / "bubble_sort_profile.txt"
    with open(bubble_profile_path, "w") as f:
        f.write(bubble_result.get_stats_as_string(limit=20))

    quick_profile_path = output_dir / "quick_sort_profile.txt"
    with open(quick_profile_path, "w") as f:
        f.write(quick_result.get_stats_as_string(limit=20))

    logger.info(
        f"Profile results saved to {bubble_profile_path} and {quick_profile_path}"
    )


def example_system_info() -> None:
    """Example demonstrating system information utilities."""
    logger.info("=== System Information Example ===")

    # Get memory usage
    memory_usage = get_memory_usage()
    logger.info(f"Memory usage: {memory_usage}")

    # Get CPU usage
    cpu_usage = get_cpu_usage()
    logger.info(f"CPU usage: {cpu_usage}")

    # Get system information
    system_info = get_system_info()
    logger.info(f"System information: {system_info}")

    # Save system information
    info_path = output_dir / "system_info.json"
    with open(info_path, "w") as f:
        json.dump(
            {
                "memory_usage": memory_usage,
                "cpu_usage": cpu_usage,
                "system_info": system_info,
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
    example_profile_decorator()
    example_benchmark_decorator()
    example_benchmark_context()
    example_benchmark_class()
    example_benchmark_suite()
    example_profiler_class()
    example_system_info()

    logger.info("All benchmarking and profiling examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
