#!/usr/bin/env python
"""Example demonstrating the data compression and optimization utilities.

This example shows how to use the data compression and optimization utilities
to compress and optimize data, including various compression algorithms,
serialization formats, and optimization strategies for large datasets.
"""

import json
import time
from typing import Any, Dict, List

import numpy as np

from pepperpy.utils.compression import (
    CompressedData,
    CompressionAlgorithm,
    CompressionLevel,
    DataCompressor,
    DatasetOptimizer,
    SerializationFormat,
    compress_data,
    compress_json,
    compress_numpy,
    decompress_data,
    decompress_json,
    decompress_numpy,
    optimize_dataset,
)


def format_size(size_bytes: int) -> str:
    """Format a size in bytes as a human-readable string.

    Args:
        size_bytes: The size in bytes

    Returns:
        A human-readable string representation of the size
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def benchmark_compression(
    data: Any,
    algorithms: List[CompressionAlgorithm],
    serialization_formats: List[SerializationFormat],
    levels: List[CompressionLevel],
) -> None:
    """Benchmark different compression algorithms, serialization formats, and levels.

    Args:
        data: The data to compress
        algorithms: The compression algorithms to benchmark
        serialization_formats: The serialization formats to benchmark
        levels: The compression levels to benchmark
    """
    print("Benchmarking compression algorithms, serialization formats, and levels...")
    print(
        f"{'Algorithm':<10} {'Format':<10} {'Level':<10} {'Size':<10} {'Ratio':<10} {'Time (ms)':<10}"
    )
    print("-" * 60)

    for algorithm in algorithms:
        for serialization in serialization_formats:
            for level in levels:
                # Skip incompatible combinations
                if (
                    algorithm == CompressionAlgorithm.NONE
                    and level != CompressionLevel.NONE
                ):
                    continue

                # Compress the data
                compressor = DataCompressor(
                    algorithm=algorithm,
                    serialization=serialization,
                    level=level,
                )

                # Measure compression time
                start_time = time.time()
                compressed = compressor.compress(data)
                end_time = time.time()
                compression_time = (
                    end_time - start_time
                ) * 1000  # Convert to milliseconds

                # Compute compression ratio
                serialized = compressor._serialize(data)
                original_size = len(serialized)
                compressed_size = len(compressed)
                ratio = original_size / compressed_size if compressed_size > 0 else 0

                # Print results
                print(
                    f"{algorithm.value:<10} {serialization.value:<10} {level.name:<10} "
                    f"{format_size(compressed_size):<10} {ratio:.2f}x{'':<5} {compression_time:.2f}"
                )


def example_basic_compression() -> None:
    """Example of basic data compression."""
    print("\n=== Basic Data Compression ===\n")

    # Create some sample data
    data = {
        "name": "John Doe",
        "age": 30,
        "email": "john.doe@example.com",
        "address": {
            "street": "123 Main St",
            "city": "Anytown",
            "state": "CA",
            "zip": "12345",
        },
        "phone_numbers": [
            {"type": "home", "number": "555-1234"},
            {"type": "work", "number": "555-5678"},
        ],
    }

    print(f"Original data: {json.dumps(data, indent=2)}")

    # Compress the data using different algorithms
    print("\nCompressing data using different algorithms...")

    # GZIP compression
    gzip_compressed = compress_data(
        data,
        algorithm=CompressionAlgorithm.GZIP,
        serialization=SerializationFormat.JSON,
        level=CompressionLevel.DEFAULT,
    )
    print(f"GZIP compressed size: {format_size(len(gzip_compressed))}")

    # ZLIB compression
    zlib_compressed = compress_data(
        data,
        algorithm=CompressionAlgorithm.ZLIB,
        serialization=SerializationFormat.JSON,
        level=CompressionLevel.DEFAULT,
    )
    print(f"ZLIB compressed size: {format_size(len(zlib_compressed))}")

    # LZMA compression
    lzma_compressed = compress_data(
        data,
        algorithm=CompressionAlgorithm.LZMA,
        serialization=SerializationFormat.JSON,
        level=CompressionLevel.DEFAULT,
    )
    print(f"LZMA compressed size: {format_size(len(lzma_compressed))}")

    # Decompress the data
    print("\nDecompressing data...")
    decompressed = decompress_data(
        gzip_compressed,
        algorithm=CompressionAlgorithm.GZIP,
        serialization=SerializationFormat.JSON,
        level=CompressionLevel.DEFAULT,
    )
    print(f"Decompressed data matches original: {decompressed == data}")

    # Benchmark different compression options
    print("\nBenchmarking different compression options...")
    benchmark_compression(
        data=data,
        algorithms=[
            CompressionAlgorithm.GZIP,
            CompressionAlgorithm.ZLIB,
            CompressionAlgorithm.LZMA,
            CompressionAlgorithm.NONE,
        ],
        serialization_formats=[
            SerializationFormat.JSON,
            SerializationFormat.MSGPACK,
            SerializationFormat.PICKLE,
        ],
        levels=[
            CompressionLevel.NONE,
            CompressionLevel.FAST,
            CompressionLevel.DEFAULT,
            CompressionLevel.BEST,
        ],
    )


def example_json_compression() -> None:
    """Example of JSON-specific compression."""
    print("\n=== JSON Compression ===\n")

    # Create a list of similar JSON objects (with repeated keys)
    data = []
    for i in range(100):
        data.append({
            "id": f"user{i}",
            "name": f"User {i}",
            "email": f"user{i}@example.com",
            "age": 20 + (i % 50),
            "active": i % 3 == 0,
            "created_at": f"2023-01-{1 + (i % 28):02d}",
            "updated_at": f"2023-02-{1 + (i % 28):02d}",
            "address": {
                "street": f"{i} Main St",
                "city": "Anytown",
                "state": "CA",
                "zip": "12345",
            },
            "preferences": {
                "theme": "dark" if i % 2 == 0 else "light",
                "notifications": True,
                "language": "en",
            },
        })

    print(f"Original data: {len(data)} JSON objects")
    print(f"First object: {json.dumps(data[0], indent=2)}")

    # Compress with and without key optimization
    print("\nCompressing JSON data...")

    # With key optimization
    optimized_compressed = compress_json(
        data,
        algorithm=CompressionAlgorithm.GZIP,
        level=CompressionLevel.DEFAULT,
        optimize_keys=True,
    )
    print(
        f"Compressed size (with key optimization): {format_size(len(optimized_compressed))}"
    )

    # Without key optimization
    unoptimized_compressed = compress_json(
        data,
        algorithm=CompressionAlgorithm.GZIP,
        level=CompressionLevel.DEFAULT,
        optimize_keys=False,
    )
    print(
        f"Compressed size (without key optimization): {format_size(len(unoptimized_compressed))}"
    )
    print(
        f"Size reduction from key optimization: {(1 - len(optimized_compressed) / len(unoptimized_compressed)) * 100:.2f}%"
    )

    # Decompress the data
    print("\nDecompressing JSON data...")
    decompressed = decompress_json(
        optimized_compressed,
        algorithm=CompressionAlgorithm.GZIP,
        level=CompressionLevel.DEFAULT,
        optimize_keys=True,
    )
    print(f"Decompressed data matches original: {decompressed == data}")


def example_numpy_compression() -> None:
    """Example of NumPy array compression."""
    print("\n=== NumPy Array Compression ===\n")

    # Create a large NumPy array
    array = np.random.rand(1000, 1000)
    print(f"Original array shape: {array.shape}")
    print(f"Original array size: {format_size(array.nbytes)}")

    # Compress the array
    print("\nCompressing NumPy array...")
    compressed = compress_numpy(
        array,
        algorithm=CompressionAlgorithm.GZIP,
        level=CompressionLevel.DEFAULT,
    )
    print(f"Compressed size: {format_size(len(compressed))}")
    print(f"Compression ratio: {array.nbytes / len(compressed):.2f}x")

    # Decompress the array
    print("\nDecompressing NumPy array...")
    decompressed = decompress_numpy(
        compressed,
        algorithm=CompressionAlgorithm.GZIP,
        level=CompressionLevel.DEFAULT,
    )
    print(f"Decompressed array shape: {decompressed.shape}")
    print(f"Arrays are equal: {np.array_equal(array, decompressed)}")


def example_dataset_optimization() -> None:
    """Example of dataset optimization."""
    print("\n=== Dataset Optimization ===\n")

    # Create a large dataset
    dataset = []
    for i in range(10000):
        dataset.append({
            "id": i,
            "value": i * 2,
            "name": f"Item {i}",
            "tags": [f"tag{j}" for j in range(i % 5 + 1)],
        })

    print(f"Original dataset size: {len(dataset)} items")

    # Define a processor function
    def process_chunk(chunk: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process a chunk of the dataset.

        Args:
            chunk: A chunk of the dataset

        Returns:
            The processed chunk
        """
        # Filter items with even IDs
        filtered = [item for item in chunk if item["id"] % 2 == 0]
        # Transform the filtered items
        transformed = [
            {
                "id": item["id"],
                "value": item["value"] * 2,
                "name": item["name"].upper(),
                "tag_count": len(item["tags"]),
            }
            for item in filtered
        ]
        return transformed

    # Create a dataset optimizer
    optimizer = DatasetOptimizer(chunk_size=1000)

    # Process the dataset in chunks
    print("\nProcessing dataset in chunks...")
    start_time = time.time()
    processed = optimizer.process_large_dataset(
        dataset=dataset,
        processor=process_chunk,
        compress_result=False,
    )
    end_time = time.time()
    processing_time = end_time - start_time

    print(f"Processed dataset size: {len(processed)} items")
    print(f"Processing time: {processing_time:.2f} seconds")
    print(f"First processed item: {processed[0]}")

    # Compress the processed dataset
    print("\nCompressing processed dataset...")
    compressed_data = optimizer.compress_dataset(processed)
    print(f"Compressed size: {format_size(len(compressed_data.data))}")
    print(f"Compression ratio: {compressed_data.compression_ratio:.2f}x")

    # Decompress the dataset
    print("\nDecompressing dataset...")
    decompressed = optimizer.decompress_dataset(compressed_data)
    print(f"Decompressed dataset size: {len(decompressed)} items")
    print(f"Decompressed data matches processed: {decompressed == processed}")

    # Use the convenience function
    print("\nUsing the optimize_dataset convenience function...")
    result = optimize_dataset(
        dataset=dataset,
        chunk_size=1000,
        processor=process_chunk,
        compress=True,
        algorithm=CompressionAlgorithm.GZIP,
        serialization=SerializationFormat.JSON,
        level=CompressionLevel.DEFAULT,
    )

    # Check if the result is compressed data
    if isinstance(result, CompressedData):
        compressed_result = result  # Explicit type assignment
        print(
            f"Optimized dataset compressed size: {format_size(len(compressed_result.data))}"
        )
        # Decompress to verify
        decompressed_result = compressed_result.decompress()
        if isinstance(decompressed_result, list):
            print(f"Decompressed result size: {len(decompressed_result)} items")
    else:
        # Result is a list
        processed_list = result  # type: List[Any]
        print(f"Optimized dataset size: {len(processed_list)} items")


def example_compressed_data_serialization() -> None:
    """Example of CompressedData serialization."""
    print("\n=== CompressedData Serialization ===\n")

    # Create some sample data
    data = {
        "name": "John Doe",
        "age": 30,
        "email": "john.doe@example.com",
    }

    # Compress the data
    compressor = DataCompressor(
        algorithm=CompressionAlgorithm.GZIP,
        serialization=SerializationFormat.JSON,
        level=CompressionLevel.DEFAULT,
    )
    compressed = compressor.compress(data)

    # Create a CompressedData object
    compressed_data = CompressedData(
        data=compressed,
        algorithm=CompressionAlgorithm.GZIP,
        serialization=SerializationFormat.JSON,
        level=CompressionLevel.DEFAULT,
        original_size=len(json.dumps(data).encode("utf-8")),
    )

    print(f"CompressedData object: {compressed_data}")
    print(f"Compression ratio: {compressed_data.compression_ratio:.2f}x")

    # Convert to a dictionary
    print("\nConverting to a dictionary...")
    data_dict = compressed_data.to_dict()
    print(f"Dictionary representation: {data_dict}")

    # Create from a dictionary
    print("\nCreating from a dictionary...")
    restored_data = CompressedData.from_dict(data_dict)
    print(f"Restored CompressedData object: {restored_data}")
    print(f"Data matches: {restored_data.data == compressed_data.data}")

    # Decompress the data
    print("\nDecompressing the data...")
    decompressed = restored_data.decompress()
    print(f"Decompressed data: {decompressed}")
    print(f"Data matches original: {decompressed == data}")


def main() -> None:
    """Run the example."""
    print("Data Compression and Optimization Example")
    print("========================================\n")

    # Run the examples
    example_basic_compression()
    example_json_compression()
    example_numpy_compression()
    example_dataset_optimization()
    example_compressed_data_serialization()


if __name__ == "__main__":
    main()
