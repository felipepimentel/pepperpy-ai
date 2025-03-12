#!/usr/bin/env python
"""Example demonstrating batching strategies for bulk operations.

This example demonstrates the use of batching strategies provided by the PepperPy
framework for processing large datasets efficiently, including fixed-size batching,
adaptive batching, size-based batching, and priority-based batching.
"""

import asyncio
import json
import os
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from pepperpy.core.batching import (
    BatchConfig,
    BatchingStrategy,
    BatchProcessor,
    KeyedBatchProcessor,
    create_batches,
    process_in_batches,
    process_keyed_items_in_batches,
)
from pepperpy.utils.logging import configure_logging, get_logger

# Configure logging
configure_logging(level="INFO")
logger = get_logger(__name__)

# Create output directory
output_dir = Path("outputs/batching_example")
os.makedirs(output_dir, exist_ok=True)


@dataclass
class Item:
    """Example item for batch processing."""

    id: int
    name: str
    value: float
    data: Dict[str, Any]


@dataclass
class ProcessedItem:
    """Example processed item."""

    id: int
    name: str
    original_value: float
    processed_value: float
    metadata: Dict[str, Any]


class ExampleBatchProcessor(BatchProcessor[Item, ProcessedItem]):
    """Example batch processor implementation."""

    def __init__(
        self, config: Optional[BatchConfig] = None, processing_time: float = 0.01
    ):
        """Initialize the example batch processor.

        Args:
            config: The batch configuration
            processing_time: The simulated processing time per item (in seconds)
        """
        super().__init__(config)
        self.processing_time = processing_time

    async def process_batch(self, batch: List[Item]) -> List[ProcessedItem]:
        """Process a batch of items.

        Args:
            batch: The batch of items to process

        Returns:
            The processed results
        """
        logger.info(f"Processing batch of {len(batch)} items")

        # Simulate processing time
        await asyncio.sleep(self.processing_time * len(batch))

        # Process each item
        results = []
        for item in batch:
            processed_value = item.value * 2  # Simple transformation
            processed_item = ProcessedItem(
                id=item.id,
                name=f"Processed {item.name}",
                original_value=item.value,
                processed_value=processed_value,
                metadata={
                    "processing_time": self.processing_time,
                    "batch_size": len(batch),
                    "original_data": item.data,
                },
            )
            results.append(processed_item)

        logger.info(f"Processed {len(results)} items")
        return results


class ExampleKeyedBatchProcessor(KeyedBatchProcessor[int, Item, ProcessedItem]):
    """Example keyed batch processor implementation."""

    def __init__(
        self, config: Optional[BatchConfig] = None, processing_time: float = 0.01
    ):
        """Initialize the example keyed batch processor.

        Args:
            config: The batch configuration
            processing_time: The simulated processing time per item (in seconds)
        """
        super().__init__(config)
        self.processing_time = processing_time

    async def process_keyed_batch(
        self, batch: Dict[int, Item]
    ) -> Dict[int, ProcessedItem]:
        """Process a batch of keyed items.

        Args:
            batch: The batch of keyed items to process

        Returns:
            The processed results with keys
        """
        logger.info(f"Processing keyed batch of {len(batch)} items")

        # Simulate processing time
        await asyncio.sleep(self.processing_time * len(batch))

        # Process each item
        results = {}
        for key, item in batch.items():
            processed_value = item.value * 2  # Simple transformation
            processed_item = ProcessedItem(
                id=item.id,
                name=f"Processed {item.name}",
                original_value=item.value,
                processed_value=processed_value,
                metadata={
                    "processing_time": self.processing_time,
                    "batch_size": len(batch),
                    "original_data": item.data,
                },
            )
            results[key] = processed_item

        logger.info(f"Processed {len(results)} items")
        return results


def generate_test_items(count: int) -> List[Item]:
    """Generate test items for batch processing.

    Args:
        count: The number of items to generate

    Returns:
        The generated items
    """
    items = []
    for i in range(count):
        item = Item(
            id=i,
            name=f"Item {i}",
            value=random.uniform(1.0, 100.0),
            data={
                "timestamp": time.time(),
                "tags": [f"tag{j}" for j in range(random.randint(1, 5))],
                "priority": random.randint(1, 10),
                "size": random.randint(100, 10000),
            },
        )
        items.append(item)
    return items


async def example_fixed_size_batching():
    """Example demonstrating fixed-size batching."""
    logger.info("=== Fixed-Size Batching Example ===")

    # Generate test items
    items = generate_test_items(100)
    logger.info(f"Generated {len(items)} test items")

    # Create batch processor with fixed-size batching
    config = BatchConfig(
        strategy=BatchingStrategy.FIXED_SIZE,
        max_batch_size=20,
        min_batch_size=5,
    )
    processor = ExampleBatchProcessor(config, processing_time=0.01)

    # Process items
    start_time = time.time()
    results = await processor.process_items(items)
    end_time = time.time()

    # Log results
    logger.info(
        f"Processed {len(results)} items in {end_time - start_time:.2f} seconds"
    )
    logger.info(
        f"Average processing time per batch: {sum(processor._processing_times) / len(processor._processing_times):.4f} seconds"
    )
    logger.info(
        f"Average batch size: {sum(processor._batch_sizes) / len(processor._batch_sizes):.1f} items"
    )

    # Save results
    result_path = output_dir / "fixed_size_results.json"
    with open(result_path, "w") as f:
        json.dump(
            {
                "strategy": "FIXED_SIZE",
                "config": {
                    "max_batch_size": config.max_batch_size,
                    "min_batch_size": config.min_batch_size,
                },
                "total_items": len(items),
                "total_time": end_time - start_time,
                "average_batch_time": sum(processor._processing_times)
                / len(processor._processing_times),
                "average_batch_size": sum(processor._batch_sizes)
                / len(processor._batch_sizes),
                "batch_count": len(processor._batch_sizes),
            },
            f,
            indent=2,
        )
    logger.info(f"Results saved to {result_path}")


async def example_adaptive_batching():
    """Example demonstrating adaptive batching."""
    logger.info("=== Adaptive Batching Example ===")

    # Generate test items
    items = generate_test_items(200)
    logger.info(f"Generated {len(items)} test items")

    # Create batch processor with adaptive batching
    config = BatchConfig(
        strategy=BatchingStrategy.ADAPTIVE,
        max_batch_size=50,
        min_batch_size=5,
        target_processing_time=0.5,
    )
    processor = ExampleBatchProcessor(config, processing_time=0.01)

    # Process items
    start_time = time.time()
    results = await processor.process_items(items)
    end_time = time.time()

    # Log results
    logger.info(
        f"Processed {len(results)} items in {end_time - start_time:.2f} seconds"
    )
    logger.info(
        f"Average processing time per batch: {sum(processor._processing_times) / len(processor._processing_times):.4f} seconds"
    )
    logger.info(
        f"Average batch size: {sum(processor._batch_sizes) / len(processor._batch_sizes):.1f} items"
    )
    logger.info(f"Final adaptive batch size: {processor._current_batch_size}")

    # Save results
    result_path = output_dir / "adaptive_results.json"
    with open(result_path, "w") as f:
        json.dump(
            {
                "strategy": "ADAPTIVE",
                "config": {
                    "max_batch_size": config.max_batch_size,
                    "min_batch_size": config.min_batch_size,
                    "target_processing_time": config.target_processing_time,
                },
                "total_items": len(items),
                "total_time": end_time - start_time,
                "average_batch_time": sum(processor._processing_times)
                / len(processor._processing_times),
                "average_batch_size": sum(processor._batch_sizes)
                / len(processor._batch_sizes),
                "batch_count": len(processor._batch_sizes),
                "final_batch_size": processor._current_batch_size,
            },
            f,
            indent=2,
        )
    logger.info(f"Results saved to {result_path}")


async def example_size_based_batching():
    """Example demonstrating size-based batching."""
    logger.info("=== Size-Based Batching Example ===")

    # Generate test items
    items = generate_test_items(150)
    logger.info(f"Generated {len(items)} test items")

    # Create batch processor with size-based batching
    def size_calculator(item: Item) -> int:
        """Calculate the size of an item.

        Args:
            item: The item to calculate the size of

        Returns:
            The size of the item
        """
        return item.data.get("size", 1000)

    config = BatchConfig(
        strategy=BatchingStrategy.SIZE_BASED,
        max_batch_size=30,
        min_batch_size=1,
        max_batch_total_size=50000,
        size_calculator=size_calculator,
    )
    processor = ExampleBatchProcessor(config, processing_time=0.01)

    # Process items
    start_time = time.time()
    results = await processor.process_items(items)
    end_time = time.time()

    # Log results
    logger.info(
        f"Processed {len(results)} items in {end_time - start_time:.2f} seconds"
    )
    logger.info(
        f"Average processing time per batch: {sum(processor._processing_times) / len(processor._processing_times):.4f} seconds"
    )
    logger.info(
        f"Average batch size: {sum(processor._batch_sizes) / len(processor._batch_sizes):.1f} items"
    )

    # Save results
    result_path = output_dir / "size_based_results.json"
    with open(result_path, "w") as f:
        json.dump(
            {
                "strategy": "SIZE_BASED",
                "config": {
                    "max_batch_size": config.max_batch_size,
                    "min_batch_size": config.min_batch_size,
                    "max_batch_total_size": config.max_batch_total_size,
                },
                "total_items": len(items),
                "total_time": end_time - start_time,
                "average_batch_time": sum(processor._processing_times)
                / len(processor._processing_times),
                "average_batch_size": sum(processor._batch_sizes)
                / len(processor._batch_sizes),
                "batch_count": len(processor._batch_sizes),
            },
            f,
            indent=2,
        )
    logger.info(f"Results saved to {result_path}")


async def example_priority_batching():
    """Example demonstrating priority-based batching."""
    logger.info("=== Priority-Based Batching Example ===")

    # Generate test items
    items = generate_test_items(120)
    logger.info(f"Generated {len(items)} test items")

    # Create batch processor with priority-based batching
    def priority_calculator(item: Item) -> int:
        """Calculate the priority of an item.

        Args:
            item: The item to calculate the priority of

        Returns:
            The priority of the item
        """
        return item.data.get("priority", 5)

    config = BatchConfig(
        strategy=BatchingStrategy.PRIORITY,
        max_batch_size=25,
        min_batch_size=5,
        priority_calculator=priority_calculator,
    )
    processor = ExampleBatchProcessor(config, processing_time=0.01)

    # Process items
    start_time = time.time()
    results = await processor.process_items(items)
    end_time = time.time()

    # Log results
    logger.info(
        f"Processed {len(results)} items in {end_time - start_time:.2f} seconds"
    )
    logger.info(
        f"Average processing time per batch: {sum(processor._processing_times) / len(processor._processing_times):.4f} seconds"
    )
    logger.info(
        f"Average batch size: {sum(processor._batch_sizes) / len(processor._batch_sizes):.1f} items"
    )

    # Save results
    result_path = output_dir / "priority_results.json"
    with open(result_path, "w") as f:
        json.dump(
            {
                "strategy": "PRIORITY",
                "config": {
                    "max_batch_size": config.max_batch_size,
                    "min_batch_size": config.min_batch_size,
                },
                "total_items": len(items),
                "total_time": end_time - start_time,
                "average_batch_time": sum(processor._processing_times)
                / len(processor._processing_times),
                "average_batch_size": sum(processor._batch_sizes)
                / len(processor._batch_sizes),
                "batch_count": len(processor._batch_sizes),
            },
            f,
            indent=2,
        )
    logger.info(f"Results saved to {result_path}")


async def example_keyed_batching():
    """Example demonstrating keyed batching."""
    logger.info("=== Keyed Batching Example ===")

    # Generate test items
    items = generate_test_items(80)
    keyed_items = {item.id: item for item in items}
    logger.info(f"Generated {len(keyed_items)} keyed test items")

    # Create keyed batch processor
    config = BatchConfig(
        strategy=BatchingStrategy.FIXED_SIZE,
        max_batch_size=15,
        min_batch_size=5,
    )
    processor = ExampleKeyedBatchProcessor(config, processing_time=0.01)

    # Process items
    start_time = time.time()
    results = await processor.process_dict(keyed_items)
    end_time = time.time()

    # Log results
    logger.info(
        f"Processed {len(results)} keyed items in {end_time - start_time:.2f} seconds"
    )
    logger.info(
        f"Average processing time per batch: {sum(processor._processing_times) / len(processor._processing_times):.4f} seconds"
    )
    logger.info(
        f"Average batch size: {sum(processor._batch_sizes) / len(processor._batch_sizes):.1f} items"
    )

    # Save results
    result_path = output_dir / "keyed_results.json"
    with open(result_path, "w") as f:
        json.dump(
            {
                "strategy": "KEYED",
                "config": {
                    "max_batch_size": config.max_batch_size,
                    "min_batch_size": config.min_batch_size,
                },
                "total_items": len(keyed_items),
                "total_time": end_time - start_time,
                "average_batch_time": sum(processor._processing_times)
                / len(processor._processing_times),
                "average_batch_size": sum(processor._batch_sizes)
                / len(processor._batch_sizes),
                "batch_count": len(processor._batch_sizes),
            },
            f,
            indent=2,
        )
    logger.info(f"Results saved to {result_path}")


async def example_utility_functions():
    """Example demonstrating utility functions for batching."""
    logger.info("=== Batching Utility Functions Example ===")

    # Generate test items
    items = generate_test_items(50)
    logger.info(f"Generated {len(items)} test items")

    # Create batches using utility function
    batches = create_batches(items, batch_size=10, min_batch_size=5)
    logger.info(
        f"Created {len(batches)} batches with sizes: {[len(batch) for batch in batches]}"
    )

    # Process items in batches using utility function
    async def process_batch(batch: List[Item]) -> List[ProcessedItem]:
        """Process a batch of items.

        Args:
            batch: The batch of items to process

        Returns:
            The processed results
        """
        logger.info(f"Processing batch of {len(batch)} items")
        await asyncio.sleep(0.01 * len(batch))  # Simulate processing time
        return [
            ProcessedItem(
                id=item.id,
                name=f"Processed {item.name}",
                original_value=item.value,
                processed_value=item.value * 2,
                metadata={"batch_size": len(batch)},
            )
            for item in batch
        ]

    start_time = time.time()
    results = await process_in_batches(
        items, process_batch, batch_size=10, concurrency=2
    )
    end_time = time.time()

    logger.info(
        f"Processed {len(results)} items in {end_time - start_time:.2f} seconds"
    )

    # Process keyed items in batches
    keyed_items = {item.id: item for item in items}

    async def process_keyed_batch(batch: Dict[int, Item]) -> Dict[int, ProcessedItem]:
        """Process a batch of keyed items.

        Args:
            batch: The batch of keyed items to process

        Returns:
            The processed results with keys
        """
        logger.info(f"Processing keyed batch of {len(batch)} items")
        await asyncio.sleep(0.01 * len(batch))  # Simulate processing time
        return {
            key: ProcessedItem(
                id=item.id,
                name=f"Processed {item.name}",
                original_value=item.value,
                processed_value=item.value * 2,
                metadata={"batch_size": len(batch)},
            )
            for key, item in batch.items()
        }

    start_time = time.time()
    keyed_results = await process_keyed_items_in_batches(
        keyed_items, process_keyed_batch, batch_size=10, concurrency=2
    )
    end_time = time.time()

    logger.info(
        f"Processed {len(keyed_results)} keyed items in {end_time - start_time:.2f} seconds"
    )

    # Save results
    result_path = output_dir / "utility_results.json"
    with open(result_path, "w") as f:
        json.dump(
            {
                "batches": [len(batch) for batch in batches],
                "total_items": len(items),
                "total_time": end_time - start_time,
                "concurrency": 2,
            },
            f,
            indent=2,
        )
    logger.info(f"Results saved to {result_path}")


async def example_performance_comparison():
    """Example comparing performance with and without batching."""
    logger.info("=== Performance Comparison Example ===")

    # Generate test items
    items = generate_test_items(500)
    logger.info(f"Generated {len(items)} test items")

    # Process items one by one
    logger.info("Processing items one by one...")
    start_time = time.time()
    individual_results = []
    for item in items:
        # Simulate processing
        await asyncio.sleep(0.01)
        processed_value = item.value * 2
        processed_item = ProcessedItem(
            id=item.id,
            name=f"Processed {item.name}",
            original_value=item.value,
            processed_value=processed_value,
            metadata={"processing_time": 0.01},
        )
        individual_results.append(processed_item)
    individual_time = time.time() - start_time
    logger.info(
        f"Processed {len(individual_results)} items individually in {individual_time:.2f} seconds"
    )

    # Process items in batches
    logger.info("Processing items in batches...")
    config = BatchConfig(
        strategy=BatchingStrategy.FIXED_SIZE,
        max_batch_size=50,
        min_batch_size=10,
    )
    processor = ExampleBatchProcessor(config, processing_time=0.01)

    start_time = time.time()
    batch_results = await processor.process_items(items)
    batch_time = time.time() - start_time
    logger.info(
        f"Processed {len(batch_results)} items in batches in {batch_time:.2f} seconds"
    )

    # Calculate speedup
    speedup = individual_time / batch_time
    logger.info(f"Batching speedup: {speedup:.2f}x faster")

    # Save results
    result_path = output_dir / "performance_comparison.json"
    with open(result_path, "w") as f:
        json.dump(
            {
                "individual_processing": {
                    "total_items": len(items),
                    "total_time": individual_time,
                    "time_per_item": individual_time / len(items),
                },
                "batch_processing": {
                    "total_items": len(items),
                    "total_time": batch_time,
                    "time_per_item": batch_time / len(items),
                    "average_batch_size": sum(processor._batch_sizes)
                    / len(processor._batch_sizes),
                    "batch_count": len(processor._batch_sizes),
                },
                "speedup": speedup,
            },
            f,
            indent=2,
        )
    logger.info(f"Results saved to {result_path}")


async def main():
    """Run the batching examples."""
    logger.info("Starting batching examples...")

    # Run examples
    await example_fixed_size_batching()
    await example_adaptive_batching()
    await example_size_based_batching()
    await example_priority_batching()
    await example_keyed_batching()
    await example_utility_functions()
    await example_performance_comparison()

    logger.info("All batching examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
