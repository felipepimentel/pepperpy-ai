#!/usr/bin/env python
"""Example demonstrating memory-efficient collections for large data.

This example shows how to use the memory-efficient collections provided by
the PepperPy framework to handle large amounts of data without loading
everything into memory at once.

Purpose:
    Demonstrate how to use memory-efficient collections including:
    - Memory-mapped arrays
    - Memory-mapped dictionaries
    - Streaming sequences

Requirements:
    - Python 3.9+
    - PepperPy library
    - psutil (optional, for memory usage tracking)

Usage:
    1. Install dependencies:
       pip install -r requirements.txt

    2. Run the example:
       python memory_efficient_collections_example.py
"""

import asyncio
import json
import random
from pathlib import Path
from typing import List

from pepperpy.core.collections import (
    CollectionConfig,
    MemoryMappedArray,
    MemoryMappedDict,
    StorageStrategy,
    StreamingSequence,
    create_memory_efficient_collection,
)
from pepperpy.utils.logging import configure_logging, get_logger

# Configure logging
configure_logging(level="INFO")
logger = get_logger(__name__)

# Create output directory
output_dir = Path("outputs/memory_efficient_collections")
output_dir.mkdir(parents=True, exist_ok=True)


def generate_large_data(size: int = 1000000) -> List[float]:
    """Generate a large list of random numbers.

    Args:
        size: The size of the list to generate

    Returns:
        A list of random numbers
    """
    return [random.random() for _ in range(size)]


def example_memory_mapped_array() -> None:
    """Example demonstrating memory-mapped array usage."""
    logger.info("=== Memory-Mapped Array Example ===")

    # Create configuration
    config = CollectionConfig(
        strategy=StorageStrategy.MEMORY_MAPPED,
        chunk_size=1024 * 1024,  # 1MB chunks
        storage_dir=output_dir,
    )

    # Generate test data
    data_size = 1000000
    logger.info(f"Generating {data_size} random numbers...")
    data = generate_large_data(data_size)

    # Create memory-mapped array
    logger.info("Creating memory-mapped array...")
    array = MemoryMappedArray(data, config)

    # Access elements
    logger.info("Accessing elements...")
    first = array[0]
    middle = array[len(array) // 2]
    last = array[len(array) - 1]

    logger.info(f"First element: {first}")
    logger.info(f"Middle element: {middle}")
    logger.info(f"Last element: {last}")

    # Modify elements
    logger.info("Modifying elements...")
    array[0] = 0.0
    array[len(array) // 2] = 0.5
    array[len(array) - 1] = 1.0

    # Iterate over elements
    logger.info("Calculating statistics...")
    total = 0.0
    count = 0
    for value in array:
        total += value
        count += 1

    average = total / count
    logger.info(f"Average value: {average}")

    # Clean up
    array.close()


def example_memory_mapped_dict() -> None:
    """Example demonstrating memory-mapped dictionary usage."""
    logger.info("=== Memory-Mapped Dictionary Example ===")

    # Create configuration
    config = CollectionConfig(
        strategy=StorageStrategy.MEMORY_MAPPED,
        storage_dir=output_dir,
    )

    # Generate test data
    data_size = 100000
    logger.info(f"Generating {data_size} key-value pairs...")
    data = {f"key_{i}": random.random() for i in range(data_size)}

    # Create memory-mapped dictionary
    logger.info("Creating memory-mapped dictionary...")
    dictionary = MemoryMappedDict(data, config)

    # Access values
    logger.info("Accessing values...")
    first_key = "key_0"
    middle_key = f"key_{data_size // 2}"
    last_key = f"key_{data_size - 1}"

    logger.info(f"{first_key}: {dictionary[first_key]}")
    logger.info(f"{middle_key}: {dictionary[middle_key]}")
    logger.info(f"{last_key}: {dictionary[last_key]}")

    # Modify values
    logger.info("Modifying values...")
    dictionary[first_key] = 0.0
    dictionary[middle_key] = 0.5
    dictionary[last_key] = 1.0

    # Iterate over items
    logger.info("Calculating statistics...")
    total = 0.0
    count = 0
    for key, value in dictionary.items():
        total += value
        count += 1

    average = total / count
    logger.info(f"Average value: {average}")

    # Clean up
    dictionary.close()


def example_streaming_sequence() -> None:
    """Example demonstrating streaming sequence usage."""
    logger.info("=== Streaming Sequence Example ===")

    # Create configuration
    config = CollectionConfig(
        strategy=StorageStrategy.STREAMING,
        chunk_size=1000,  # Small chunks for demonstration
        storage_dir=output_dir,
    )

    # Generate test data
    data_size = 100000
    logger.info(f"Generating {data_size} numbers...")
    data = generate_large_data(data_size)

    # Create streaming sequence
    logger.info("Creating streaming sequence...")
    sequence = StreamingSequence(data, config)

    # Process sequence in chunks
    logger.info("Processing sequence in chunks...")
    chunk_sums: List[float] = []
    current_sum = 0.0
    current_count = 0

    for value in sequence:
        current_sum += value
        current_count += 1

        if current_count % 1000 == 0:
            chunk_sums.append(current_sum / 1000)
            current_sum = 0.0

    # Calculate overall statistics
    average = sum(chunk_sums) / len(chunk_sums)
    logger.info(f"Average chunk value: {average}")

    # Append new values
    logger.info("Appending new values...")
    for i in range(1000):
        sequence.append(random.random())

    logger.info(f"New sequence size: {len(sequence)}")

    # Clean up
    sequence.close()


def example_factory_function() -> None:
    """Example demonstrating the collection factory function."""
    logger.info("=== Collection Factory Example ===")

    # Create configuration
    config = CollectionConfig(
        strategy=StorageStrategy.MEMORY_MAPPED,
        storage_dir=output_dir,
    )

    # Create different types of collections
    logger.info("Creating collections using factory function...")

    # Array
    array_data = generate_large_data(1000)
    array = create_memory_efficient_collection(
        collection_type="array",
        data=array_data,
        config=config,
    )
    logger.info(f"Created array with {len(array)} elements")

    # Dictionary
    dict_data = {str(i): i for i in range(1000)}
    dictionary = create_memory_efficient_collection(
        collection_type="dict",
        data=dict_data,
        config=config,
    )
    logger.info(f"Created dictionary with {len(dictionary)} items")

    # Stream
    stream_data = generate_large_data(1000)
    stream = create_memory_efficient_collection(
        collection_type="stream",
        data=stream_data,
        config=config,
    )
    logger.info(f"Created stream with {len(stream)} elements")

    # Clean up
    array.close()
    dictionary.close()
    stream.close()


def example_performance_comparison() -> None:
    """Example comparing performance of different collection types."""
    logger.info("=== Performance Comparison Example ===")

    # Test parameters
    data_size = 1000000
    config = CollectionConfig(storage_dir=output_dir)

    # Generate test data
    logger.info(f"Generating {data_size} random numbers...")
    data = generate_large_data(data_size)

    # Test regular list
    logger.info("Testing regular list...")
    regular_list = list(data)
    total = sum(regular_list)
    logger.info(f"Regular list sum: {total}")

    # Test memory-mapped array
    logger.info("Testing memory-mapped array...")
    with MemoryMappedArray(data, config) as mmap_array:
        total = sum(value for value in mmap_array)
        logger.info(f"Memory-mapped array sum: {total}")

    # Test streaming sequence
    logger.info("Testing streaming sequence...")
    with StreamingSequence(data, config) as stream:
        total = sum(value for value in stream)
        logger.info(f"Streaming sequence sum: {total}")

    # Save memory usage statistics
    result_path = output_dir / "performance_comparison.json"
    with open(result_path, "w") as f:
        json.dump(
            {
                "data_size": data_size,
                "collection_types": [
                    "regular_list",
                    "memory_mapped_array",
                    "streaming_sequence",
                ],
                "notes": (
                    "Memory-mapped and streaming collections use disk storage "
                    "to reduce memory usage at the cost of slower access times"
                ),
            },
            f,
            indent=2,
        )
    logger.info(f"Results saved to {result_path}")


async def main() -> None:
    """Run all memory-efficient collections examples."""
    logger.info("Starting memory-efficient collections examples...")

    # Run examples
    example_memory_mapped_array()
    example_memory_mapped_dict()
    example_streaming_sequence()
    example_factory_function()
    example_performance_comparison()

    logger.info("All examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
