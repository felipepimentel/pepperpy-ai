#!/usr/bin/env python
"""Example demonstrating memory optimization for large document processing.

This example demonstrates the use of memory optimization strategies provided by
the PepperPy framework for processing large documents efficiently, including
streaming processing, memory mapping, and weak references.
"""

import os
import tempfile
import time
from typing import Any, Dict, Iterator, List

import numpy as np

from pepperpy.rag.memory_optimization import (
    DocumentChunk,
    StreamingProcessor,
    create_generator_pipeline,
    create_memory_efficient_document,
    create_memory_mapped_array,
    create_weak_cache,
    get_memory_usage,
    optimize_memory_usage,
)
from pepperpy.utils.logging import configure_logging, get_logger

# Configure logging
configure_logging(level="INFO")
logger = get_logger(__name__)


class SimpleTextProcessor(StreamingProcessor[Dict[str, int], str]):
    """A simple text processor that counts word frequencies.

    This class demonstrates how to implement a streaming processor for
    processing large text documents in a memory-efficient way.
    """

    def __init__(self, chunk_size: int = 4096):
        """Initialize the simple text processor.

        Args:
            chunk_size: The size of chunks to use when processing documents
        """
        super().__init__(chunk_size=chunk_size)
        self.total_words = 0
        self.total_chunks = 0

    def process_chunk(self, chunk: DocumentChunk[str]) -> Dict[str, int]:
        """Process a document chunk.

        Args:
            chunk: The document chunk to process

        Returns:
            A dictionary of word frequencies
        """
        # Simple word frequency counter
        content = chunk.content
        words = content.lower().split()
        self.total_words += len(words)
        self.total_chunks += 1

        # Count word frequencies
        word_counts: Dict[str, int] = {}
        for word in words:
            # Remove punctuation
            word = word.strip(".,!?;:\"'()[]{}")
            if word:
                word_counts[word] = word_counts.get(word, 0) + 1

        logger.info(
            f"Processed chunk {chunk.chunk_id} with {len(words)} words "
            f"({len(word_counts)} unique)"
        )
        return word_counts


def create_large_text_file(file_path: str, size_mb: int = 10) -> None:
    """Create a large text file for testing.

    Args:
        file_path: The path to create the file at
        size_mb: The approximate size of the file in megabytes
    """
    # Sample text to repeat
    sample_text = """
    The PepperPy library provides efficient tools for processing large documents.
    Memory optimization is crucial when working with large datasets to prevent
    out-of-memory errors and improve performance. Streaming processing, memory
    mapping, and weak references are some of the techniques used for memory
    optimization. This example demonstrates how to use these techniques to
    process large documents efficiently.
    """

    # Calculate how many times to repeat the sample text to reach the desired size
    bytes_per_mb = 1024 * 1024
    target_size = size_mb * bytes_per_mb
    repeats = target_size // len(sample_text) + 1

    logger.info(f"Creating a {size_mb}MB text file at {file_path}")
    with open(file_path, "w") as f:
        for i in range(repeats):
            f.write(f"{sample_text}\n")

    actual_size = os.path.getsize(file_path)
    logger.info(f"Created file of size {actual_size / bytes_per_mb:.2f}MB")


def example_memory_efficient_document() -> None:
    """Example demonstrating memory-efficient document processing."""
    print("\n=== Memory-Efficient Document Example ===")

    # Create a temporary large text file
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp_file:
        temp_path = temp_file.name

    try:
        # Create a large text file (10MB)
        create_large_text_file(temp_path, size_mb=10)

        # Create a memory-efficient document
        document = create_memory_efficient_document(
            document_id="large_doc_1",
            source=temp_path,
            chunk_size=1024 * 64,  # 64KB chunks
            metadata={"description": "Large test document"},
        )

        # Create a text processor
        processor = SimpleTextProcessor(chunk_size=1024 * 64)

        # Process the document and collect results
        print("\nProcessing document in chunks...")
        start_time = time.time()
        word_counts: Dict[str, int] = {}
        for chunk_result in processor.process_document(document):
            # Merge chunk results into overall results
            for word, count in chunk_result.items():
                word_counts[word] = word_counts.get(word, 0) + count

        # Print statistics
        elapsed_time = time.time() - start_time
        print(
            f"\nProcessed {processor.total_chunks} chunks with {processor.total_words} words"
        )
        print(f"Found {len(word_counts)} unique words")
        print(f"Processing time: {elapsed_time:.2f} seconds")

        # Print memory usage
        memory_usage = get_memory_usage()
        print(f"\nMemory usage: {memory_usage['rss'] / (1024 * 1024):.2f}MB RSS")

        # Print top 10 most frequent words
        top_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        print("\nTop 10 most frequent words:")
        for word, count in top_words:
            print(f"  {word}: {count}")

    finally:
        # Clean up the temporary file
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def example_memory_mapping() -> None:
    """Example demonstrating memory-mapped arrays."""
    print("\n=== Memory-Mapped Array Example ===")

    # Create a temporary file for the memory-mapped array
    with tempfile.NamedTemporaryFile(suffix=".dat", delete=False) as temp_file:
        temp_path = temp_file.name

    try:
        # Create a large array (100MB)
        array_size = (25000, 1000)  # 25,000 x 1,000 array of float32 = ~100MB
        print(f"\nCreating a memory-mapped array of size {array_size}...")

        # Create a memory-mapped array
        mmap_array = create_memory_mapped_array(
            file_path=temp_path,
            dtype=np.float32,
            shape=array_size,
            mode="w+",  # Write mode to create the file
        )

        # Fill the array with some data
        print("Filling the array with data...")
        start_time = time.time()
        for i in range(0, array_size[0], 1000):
            mmap_array[i : i + 1000] = np.random.random((1000, array_size[1])).astype(
                np.float32
            )
        mmap_array.flush()
        elapsed_time = time.time() - start_time
        print(f"Array filled in {elapsed_time:.2f} seconds")

        # Print memory usage
        memory_usage = get_memory_usage()
        print(
            f"\nMemory usage after creating and filling array: {memory_usage['rss'] / (1024 * 1024):.2f}MB RSS"
        )

        # Close the array to release resources
        mmap_array.close()

        # Reopen the array in read mode
        print("\nReopening the array in read mode...")
        mmap_array = create_memory_mapped_array(
            file_path=temp_path,
            dtype=np.float32,
            shape=array_size,
            mode="r",  # Read-only mode
        )

        # Perform some calculations on the array
        print("Performing calculations on the array...")
        start_time = time.time()
        row_means = np.zeros(array_size[0], dtype=np.float32)
        for i in range(0, array_size[0], 1000):
            row_means[i : i + 1000] = np.mean(mmap_array[i : i + 1000], axis=1)
        elapsed_time = time.time() - start_time
        print(f"Calculations completed in {elapsed_time:.2f} seconds")

        # Print memory usage
        memory_usage = get_memory_usage()
        print(
            f"\nMemory usage after calculations: {memory_usage['rss'] / (1024 * 1024):.2f}MB RSS"
        )

        # Print some statistics
        print("\nArray statistics:")
        print(f"  Mean: {np.mean(row_means):.6f}")
        print(f"  Min: {np.min(row_means):.6f}")
        print(f"  Max: {np.max(row_means):.6f}")

        # Close the array
        mmap_array.close()

    finally:
        # Clean up the temporary file
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def example_weak_cache() -> None:
    """Example demonstrating weak caching."""
    print("\n=== Weak Cache Example ===")

    # Create a weak cache
    cache = create_weak_cache(max_size=100)

    # Create some large objects to cache
    print("\nCreating and caching large objects...")
    for i in range(10):
        # Create a large array (10MB each)
        large_array = np.random.random((2500, 1000)).astype(np.float32)
        cache.put(f"array_{i}", large_array)
        print(f"  Cached array_{i} of size {large_array.nbytes / (1024 * 1024):.2f}MB")

    # Print memory usage
    memory_usage = get_memory_usage()
    print(
        f"\nMemory usage after caching: {memory_usage['rss'] / (1024 * 1024):.2f}MB RSS"
    )

    # Access some cached objects
    print("\nAccessing cached objects...")
    for i in range(5):
        array = cache.get(f"array_{i}")
        if array is not None:
            print(f"  Retrieved array_{i} of size {array.nbytes / (1024 * 1024):.2f}MB")
        else:
            print(f"  array_{i} not found in cache")

    # Delete references to some arrays to allow garbage collection
    print("\nDeleting references to allow garbage collection...")
    for i in range(5, 10):
        array = cache.get(f"array_{i}")
        if array is not None:
            print(f"  Deleting reference to array_{i}")
            del array

    # Run garbage collection
    print("\nRunning garbage collection...")
    optimize_memory_usage()

    # Check cache after garbage collection
    print("\nChecking cache after garbage collection...")
    for i in range(10):
        array = cache.get(f"array_{i}")
        if array is not None:
            print(
                f"  array_{i} still in cache, size: {array.nbytes / (1024 * 1024):.2f}MB"
            )
        else:
            print(f"  array_{i} was garbage collected")

    # Print memory usage
    memory_usage = get_memory_usage()
    print(
        f"\nMemory usage after garbage collection: {memory_usage['rss'] / (1024 * 1024):.2f}MB RSS"
    )


def example_generator_pipeline() -> None:
    """Example demonstrating generator pipelines."""
    print("\n=== Generator Pipeline Example ===")

    # Create a generator pipeline
    pipeline = create_generator_pipeline()

    # Define pipeline stages that work with iterators
    def tokenize(texts_iter: Iterator[Any]) -> Iterator[List[str]]:
        """Tokenize texts into words."""
        for text in texts_iter:
            yield text.lower().split()

    def filter_stopwords(tokens_iter: Iterator[List[str]]) -> Iterator[List[str]]:
        """Filter out stopwords."""
        stopwords = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "with",
            "by",
        }
        for tokens in tokens_iter:
            yield [token for token in tokens if token not in stopwords]

    def count_tokens(tokens_iter: Iterator[List[str]]) -> Iterator[Dict[str, int]]:
        """Count token frequencies."""
        for tokens in tokens_iter:
            token_counts = {}
            for token in tokens:
                token_counts[token] = token_counts.get(token, 0) + 1
            yield token_counts

    # Add stages to the pipeline
    pipeline.add_stage(tokenize)
    pipeline.add_stage(filter_stopwords)
    pipeline.add_stage(count_tokens)

    # Create some sample texts
    texts = [
        "The quick brown fox jumps over the lazy dog.",
        "A fast yellow fox leaps above a sleepy canine.",
        "The rapid orange fox hops over the lethargic hound.",
        "A swift auburn fox bounds over the idle dog.",
        "The speedy red fox jumps over the lazy dog.",
    ]

    # Process the texts through the pipeline
    print("\nProcessing texts through the pipeline...")
    results = list(pipeline.process(texts))

    # Print the results
    print("\nResults:")
    for i, (text, result) in enumerate(zip(texts, results)):
        print(f"\nText {i + 1}: {text}")
        print("Token frequencies:")
        for token, count in sorted(result.items(), key=lambda x: x[1], reverse=True):
            print(f"  {token}: {count}")


def main() -> None:
    """Run the memory optimization examples."""
    print("=== Memory Optimization Examples ===")
    print("\nInitial memory usage:")
    memory_usage = get_memory_usage()
    print(f"  RSS: {memory_usage['rss'] / (1024 * 1024):.2f}MB")
    print(f"  VMS: {memory_usage['vms'] / (1024 * 1024):.2f}MB")

    # Run the examples
    example_memory_efficient_document()
    example_memory_mapping()
    example_weak_cache()
    example_generator_pipeline()

    # Final memory usage
    print("\n=== Final Memory Usage ===")
    memory_usage = get_memory_usage()
    print(f"  RSS: {memory_usage['rss'] / (1024 * 1024):.2f}MB")
    print(f"  VMS: {memory_usage['vms'] / (1024 * 1024):.2f}MB")


if __name__ == "__main__":
    main()
