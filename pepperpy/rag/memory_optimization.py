"""Memory optimization module for RAG.

This module provides memory optimization strategies for processing large documents.
"""

import logging
import os
import weakref
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Generic, Iterator, List, Literal, Optional, TypeVar, Union

import numpy as np
from numpy.typing import NDArray

from .document import Document

logger = logging.getLogger(__name__)

T = TypeVar("T")
U = TypeVar("U")
ContentType = TypeVar("ContentType")

# Type for numpy memmap modes
MemMapMode = Literal["r", "r+", "w+", "c"]


@dataclass
class DocumentChunk(Generic[ContentType]):
    """Chunk of a document for streaming processing.

    Args:
        content: Chunk content
        metadata: Optional chunk metadata
        index: Chunk index
        total_chunks: Total number of chunks
    """

    content: ContentType
    metadata: Dict[str, Any]
    index: int
    total_chunks: int


class StreamingProcessor(Generic[T, U], ABC):
    """Base class for streaming document processors.

    This class provides the interface for processing documents in a streaming
    fashion to optimize memory usage.
    """

    @abstractmethod
    def process_chunk(self, chunk: DocumentChunk[T]) -> T:
        """Process a document chunk.

        Args:
            chunk: Document chunk to process

        Returns:
            Processed chunk result
        """
        ...

    @abstractmethod
    def merge_results(self, results: List[T]) -> U:
        """Merge chunk processing results.

        Args:
            results: List of chunk processing results

        Returns:
            Merged result
        """
        ...


def get_memory_usage() -> Dict[str, float]:
    """Get current memory usage in bytes.

    Returns:
        Dictionary with memory usage statistics
    """
    import psutil

    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    return {
        "rss": memory_info.rss,
        "vms": memory_info.vms,
        "shared": memory_info.shared,
        "text": memory_info.text,
        "lib": memory_info.lib,
        "data": memory_info.data,
        "dirty": memory_info.dirty,
    }


def optimize_memory_usage(func: Any) -> Any:
    """Decorator to optimize memory usage of a function.

    Args:
        func: Function to optimize

    Returns:
        Optimized function
    """

    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Record initial memory usage
        initial_memory = get_memory_usage()

        try:
            # Call function
            result = func(*args, **kwargs)

            # Clean up memory
            import gc

            gc.collect()

            return result
        finally:
            # Log memory usage
            final_memory = get_memory_usage()
            memory_diff = final_memory["rss"] - initial_memory["rss"]
            logger.debug(f"Memory usage for {func.__name__}: {memory_diff} bytes")

    return wrapper


def stream_document(
    document: Document, chunk_size: int = 1024
) -> Iterator[DocumentChunk]:
    """Stream a document in chunks.

    Args:
        document: Document to stream
        chunk_size: Size of each chunk in bytes

    Yields:
        Document chunks
    """
    content = document.content
    total_size = len(content)
    total_chunks = (total_size + chunk_size - 1) // chunk_size

    for i in range(total_chunks):
        start = i * chunk_size
        end = min(start + chunk_size, total_size)
        chunk_content = content[start:end]

        yield DocumentChunk(
            content=chunk_content,
            metadata=document.metadata,
            index=i,
            total_chunks=total_chunks,
        )


def process_document_streaming(
    document: Document,
    processor: StreamingProcessor[T, U],
    chunk_size: int = 1024,
) -> U:
    """Process a document using streaming.

    Args:
        document: Document to process
        processor: Streaming processor to use
        chunk_size: Size of each chunk in bytes

    Returns:
        Processing result
    """
    results: List[T] = []

    for chunk in stream_document(document, chunk_size):
        result = processor.process_chunk(chunk)
        results.append(result)

    return processor.merge_results(results)


def create_memory_efficient_document(
    document_id: str,
    source: str,
    chunk_size: int = 1024,
    metadata: Optional[Dict[str, Any]] = None,
) -> Document:
    """Create a memory-efficient document from a file.

    Args:
        document_id: Document ID
        source: Path to source file
        chunk_size: Size of chunks to read
        metadata: Optional document metadata

    Returns:
        Memory-efficient document
    """
    # Read file in chunks to avoid loading it all into memory
    content = []
    with open(source, "r") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            content.append(chunk)

    return Document(
        id=document_id,
        content="".join(content),
        metadata=metadata or {},
    )


def create_memory_mapped_array(
    file_path: str,
    dtype: Any,
    shape: tuple,
    mode: MemMapMode = "r",
) -> NDArray:
    """Create a memory-mapped array.

    Args:
        file_path: Path to file for memory mapping
        dtype: NumPy data type
        shape: Array shape
        mode: File mode ("r" for read-only, "r+" for read/write)

    Returns:
        Memory-mapped array
    """
    return np.memmap(file_path, dtype=dtype, mode=mode, shape=shape)


class WeakCache(weakref.WeakValueDictionary[str, Any]):
    """Weak reference cache that maps strings to any value."""

    pass


def create_weak_cache(maxsize: int = 1000) -> WeakCache:
    """Create a weak reference cache.

    Args:
        maxsize: Maximum cache size

    Returns:
        Weak reference cache
    """
    return WeakCache()


def create_generator_pipeline(*funcs: Any) -> Any:
    """Create a pipeline of generator functions.

    Args:
        *funcs: Generator functions to chain

    Returns:
        Chained generator function
    """

    def pipeline(data: Iterator[Any]) -> Iterator[Any]:
        result = data
        for func in funcs:
            result = func(result)
        return result

    return pipeline
