#!/usr/bin/env python
"""Example demonstrating parallel processing capabilities for CPU-bound tasks.

This example shows how to use the parallel processing utilities provided by
the PepperPy framework to efficiently process CPU-bound tasks using process
pools, thread pools, and adaptive strategies.
"""

import asyncio
import math
import time
from pathlib import Path
from typing import List

from pepperpy.core.parallel import (
    ProcessingStrategy,
    create_parallel_processor,
)
from pepperpy.utils.logging import configure_logging, get_logger

# Configure logging
configure_logging(level="INFO")
logger = get_logger(__name__)

# Create output directory
output_dir = Path("outputs/parallel_processing")
output_dir.mkdir(parents=True, exist_ok=True)


def cpu_intensive_task(n: int) -> float:
    """CPU-intensive task that calculates the sum of sines.

    Args:
        n: The number to process

    Returns:
        The sum of sines from 0 to n
    """
    return sum(math.sin(i) for i in range(n))


def io_intensive_task(n: int) -> int:
    """I/O-intensive task that simulates file operations.

    Args:
        n: The number to process

    Returns:
        The processed number
    """
    time.sleep(0.001)  # Simulate I/O operation
    return n * 2


async def example_process_pool():
    """Example demonstrating process pool for CPU-bound tasks."""
    logger.info("=== Process Pool Example ===")

    # Create processor with process pool strategy
    processor = create_parallel_processor(
        strategy=ProcessingStrategy.PROCESS_POOL,
        workers=4,
        chunk_size=25,
    )

    # Generate test data
    numbers = list(range(100, 1100, 100))
    logger.info(f"Processing {len(numbers)} numbers")

    # Process items
    start_time = time.time()
    results = await processor.process_items(numbers, cpu_intensive_task)
    end_time = time.time()

    # Log results
    logger.info(
        f"Processed {len(results)} items in {end_time - start_time:.2f} seconds"
    )

    # Save results
    result_path = output_dir / "process_pool_results.txt"
    with open(result_path, "w") as f:
        f.write("Process Pool Results\n")
        f.write("===================\n\n")
        for n, result in zip(numbers, results):
            f.write(f"n={n}: {result}\n")

    logger.info(f"Results saved to {result_path}")


async def example_thread_pool():
    """Example demonstrating thread pool for I/O-bound tasks."""
    logger.info("=== Thread Pool Example ===")

    # Create processor with thread pool strategy
    processor = create_parallel_processor(
        strategy=ProcessingStrategy.THREAD_POOL,
        workers=10,
        chunk_size=50,
    )

    # Generate test data
    numbers = list(range(1000))
    logger.info(f"Processing {len(numbers)} numbers")

    # Process items
    start_time = time.time()
    results = await processor.process_items(numbers, io_intensive_task)
    end_time = time.time()

    # Log results
    logger.info(
        f"Processed {len(results)} items in {end_time - start_time:.2f} seconds"
    )

    # Save results
    result_path = output_dir / "thread_pool_results.txt"
    with open(result_path, "w") as f:
        f.write("Thread Pool Results\n")
        f.write("==================\n\n")
        for n, result in zip(numbers[:10], results[:10]):
            f.write(f"n={n}: {result}\n")
        f.write("...\n")

    logger.info(f"Results saved to {result_path}")


async def example_adaptive_strategy():
    """Example demonstrating adaptive strategy selection."""
    logger.info("=== Adaptive Strategy Example ===")

    # Create processor with adaptive strategy
    processor = create_parallel_processor(
        strategy=ProcessingStrategy.ADAPTIVE,
        workers=4,
        chunk_size=25,
    )

    # Generate test data for both CPU and I/O bound tasks
    cpu_numbers = list(range(100, 600, 100))
    io_numbers = list(range(500))

    # Process CPU-bound tasks
    logger.info(f"Processing {len(cpu_numbers)} CPU-bound tasks")
    start_time = time.time()
    cpu_results = await processor.process_items(cpu_numbers, cpu_intensive_task)
    cpu_time = time.time() - start_time

    # Process I/O-bound tasks
    logger.info(f"Processing {len(io_numbers)} I/O-bound tasks")
    start_time = time.time()
    io_results = await processor.process_items(io_numbers, io_intensive_task)
    io_time = time.time() - start_time

    # Log results
    logger.info(f"CPU-bound tasks completed in {cpu_time:.2f} seconds")
    logger.info(f"I/O-bound tasks completed in {io_time:.2f} seconds")

    # Save results
    result_path = output_dir / "adaptive_results.txt"
    with open(result_path, "w") as f:
        f.write("Adaptive Strategy Results\n")
        f.write("=======================\n\n")
        f.write("CPU-bound Results:\n")
        for n, result in zip(cpu_numbers, cpu_results):
            f.write(f"n={n}: {result}\n")
        f.write("\nI/O-bound Results (first 10):\n")
        for n, result in zip(io_numbers[:10], io_results[:10]):
            f.write(f"n={n}: {result}\n")
        f.write("...\n")

    logger.info(f"Results saved to {result_path}")


async def example_custom_processor():
    """Example demonstrating custom processor strategy."""
    logger.info("=== Custom Processor Example ===")

    def custom_chunk_processor(chunk: List[int]) -> List[float]:
        """Process a chunk of numbers using a custom strategy.

        Args:
            chunk: The chunk of numbers to process

        Returns:
            The processed results
        """
        # Example: Calculate moving average for each number using its neighbors
        results = []
        for i, n in enumerate(chunk):
            # Get up to 2 numbers before and after the current number
            start = max(0, i - 2)
            end = min(len(chunk), i + 3)
            neighbors = chunk[start:end]
            avg = sum(neighbors) / len(neighbors)
            results.append(avg)
        return results

    # Create processor with custom strategy
    processor = create_parallel_processor(
        strategy=ProcessingStrategy.CUSTOM,
        workers=4,
        chunk_size=100,
        custom_processor=custom_chunk_processor,
    )

    # Generate test data
    numbers = list(range(1000))
    logger.info(f"Processing {len(numbers)} numbers")

    # Process items
    start_time = time.time()
    results = await processor.process_items(numbers, lambda x: x)  # Processor not used
    end_time = time.time()

    # Log results
    logger.info(
        f"Processed {len(results)} items in {end_time - start_time:.2f} seconds"
    )

    # Save results
    result_path = output_dir / "custom_processor_results.txt"
    with open(result_path, "w") as f:
        f.write("Custom Processor Results\n")
        f.write("=======================\n\n")
        f.write("First 20 results:\n")
        for n, result in zip(numbers[:20], results[:20]):
            f.write(f"n={n}: {result}\n")
        f.write("...\n")

    logger.info(f"Results saved to {result_path}")


async def main():
    """Run all parallel processing examples."""
    logger.info("Starting parallel processing examples")

    # Run examples
    await example_process_pool()
    await example_thread_pool()
    await example_adaptive_strategy()
    await example_custom_processor()

    logger.info("All examples completed")


if __name__ == "__main__":
    asyncio.run(main())
