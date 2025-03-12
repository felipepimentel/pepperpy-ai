"""Memory optimization for large document processing.

This module provides strategies and utilities for optimizing memory usage
when processing large documents, including streaming processing, chunking,
and memory-efficient data structures.
"""

import gc
import mmap
import os
import time
import weakref
from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import (
    Any,
    BinaryIO,
    Callable,
    Dict,
    Generator,
    Generic,
    Iterable,
    Iterator,
    List,
    Optional,
    TextIO,
    Tuple,
    TypeVar,
    Union,
    cast,
)

from pepperpy.core.resource_tracker import ResourceType, track_resource
from pepperpy.errors import PepperpyError
from pepperpy.utils.logging import get_logger

logger = get_logger(__name__)

# Type variables for generic memory optimization
T = TypeVar("T")  # Document type
C = TypeVar("C")  # Chunk type


class MemoryOptimizationStrategy(Enum):
    """Enum representing different memory optimization strategies."""

    STREAMING = auto()  # Process documents in a streaming fashion
    CHUNKING = auto()  # Process documents in chunks
    MEMORY_MAPPING = auto()  # Use memory-mapped files
    GENERATOR_PIPELINE = auto()  # Use generator pipelines
    WEAK_REFERENCES = auto()  # Use weak references for caching
    CUSTOM = auto()  # Custom strategy


class DocumentChunk(Generic[T]):
    """A chunk of a document with metadata.

    This class represents a chunk of a document with associated metadata,
    designed for memory-efficient processing of large documents.
    """

    def __init__(
        self,
        content: T,
        chunk_id: str,
        document_id: str,
        start_pos: int,
        end_pos: int,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Initialize a document chunk.

        Args:
            content: The content of the chunk
            chunk_id: The ID of the chunk
            document_id: The ID of the document this chunk belongs to
            start_pos: The start position of the chunk in the document
            end_pos: The end position of the chunk in the document
            metadata: Additional metadata about the chunk
        """
        self.content = content
        self.chunk_id = chunk_id
        self.document_id = document_id
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.metadata = metadata or {}

    def __len__(self) -> int:
        """Get the length of the chunk.

        Returns:
            The length of the chunk
        """
        if isinstance(self.content, (str, bytes, list)):
            return len(self.content)
        return self.end_pos - self.start_pos

    def __str__(self) -> str:
        """Get a string representation of the chunk.

        Returns:
            A string representation of the chunk
        """
        content_preview = str(self.content)
        if len(content_preview) > 50:
            content_preview = content_preview[:47] + "..."
        return (
            f"DocumentChunk(id={self.chunk_id}, doc={self.document_id}, "
            f"pos={self.start_pos}-{self.end_pos}, content={content_preview})"
        )


class MemoryEfficientDocument(Generic[C]):
    """A memory-efficient document representation.

    This class provides a memory-efficient representation of a document,
    designed for processing large documents without loading the entire
    document into memory at once.
    """

    def __init__(
        self,
        document_id: str,
        source: Union[str, BinaryIO, TextIO],
        chunk_size: int = 4096,
        metadata: Optional[Dict[str, Any]] = None,
        encoding: str = "utf-8",
    ):
        """Initialize a memory-efficient document.

        Args:
            document_id: The ID of the document
            source: The source of the document (file path or file-like object)
            chunk_size: The size of chunks to use when processing the document
            metadata: Additional metadata about the document
            encoding: The encoding to use when reading text files
        """
        self.document_id = document_id
        self.source = source
        self.chunk_size = chunk_size
        self.metadata = metadata or {}
        self.encoding = encoding
        self._file_obj: Optional[Union[BinaryIO, TextIO]] = None
        self._mmap_obj: Optional[mmap.mmap] = None
        self._size: Optional[int] = None
        self._is_binary = isinstance(source, BinaryIO) or (
            isinstance(source, str)
            and not source.endswith((".txt", ".md", ".json", ".csv"))
        )

    def __enter__(self) -> "MemoryEfficientDocument[C]":
        """Enter the context manager.

        Returns:
            The memory-efficient document
        """
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the context manager.

        Args:
            exc_type: The exception type, if an exception was raised
            exc_val: The exception value, if an exception was raised
            exc_tb: The exception traceback, if an exception was raised
        """
        self.close()

    def open(self) -> None:
        """Open the document for reading."""
        if self._file_obj is not None:
            return

        if isinstance(self.source, str):
            # Source is a file path
            mode = "rb" if self._is_binary else "r"
            if self._is_binary:
                self._file_obj = open(self.source, mode)  # type: ignore
            else:
                self._file_obj = open(self.source, mode, encoding=self.encoding)  # type: ignore
        else:
            # Source is a file-like object
            self._file_obj = self.source

        # Get the file size
        if (
            self._file_obj is not None
            and hasattr(self._file_obj, "seek")
            and hasattr(self._file_obj, "tell")
        ):
            current_pos = self._file_obj.tell()
            self._file_obj.seek(0, os.SEEK_END)
            self._size = self._file_obj.tell()
            self._file_obj.seek(current_pos, os.SEEK_SET)

    def close(self) -> None:
        """Close the document."""
        if self._mmap_obj is not None:
            self._mmap_obj.close()
            self._mmap_obj = None

        if self._file_obj is not None and isinstance(self.source, str):
            # Only close if we opened the file ourselves
            self._file_obj.close()
            self._file_obj = None

    def memory_map(self) -> None:
        """Memory-map the document for efficient random access."""
        if self._mmap_obj is not None:
            return

        if self._file_obj is None:
            self.open()

        if self._file_obj is None or not hasattr(self._file_obj, "fileno"):
            raise PepperpyError(
                "Cannot memory-map a file-like object without a file descriptor"
            )

        # Memory-map the file
        self._mmap_obj = mmap.mmap(
            self._file_obj.fileno(),
            0,
            access=mmap.ACCESS_READ,
        )

    def get_size(self) -> int:
        """Get the size of the document in bytes.

        Returns:
            The size of the document in bytes
        """
        if self._size is None:
            if self._file_obj is None:
                self.open()
            if self._size is None:
                raise PepperpyError("Could not determine document size")
        return self._size

    def read_chunk(self, start_pos: int, end_pos: int) -> C:
        """Read a chunk of the document.

        Args:
            start_pos: The start position of the chunk
            end_pos: The end position of the chunk

        Returns:
            The chunk content
        """
        if self._file_obj is None:
            self.open()

        if self._mmap_obj is not None:
            # Use memory-mapped file for efficient random access
            data = self._mmap_obj[start_pos:end_pos]
        else:
            # Use file seek/read
            if self._file_obj is None:
                raise PepperpyError("File object is not initialized")
            self._file_obj.seek(start_pos)
            data = self._file_obj.read(end_pos - start_pos)

        # Convert to the appropriate type
        if self._is_binary:
            return cast(C, data)
        else:
            if isinstance(data, bytes):
                return cast(C, data.decode(self.encoding))
            return cast(C, data)

    def iter_chunks(self) -> Generator[DocumentChunk[C], None, None]:
        """Iterate over chunks of the document.

        Yields:
            Document chunks
        """
        if self._file_obj is None:
            self.open()

        size = self.get_size()
        for i in range(0, size, self.chunk_size):
            start_pos = i
            end_pos = min(i + self.chunk_size, size)
            content = self.read_chunk(start_pos, end_pos)
            chunk_id = f"{self.document_id}_{start_pos}_{end_pos}"
            yield DocumentChunk(
                content=content,
                chunk_id=chunk_id,
                document_id=self.document_id,
                start_pos=start_pos,
                end_pos=end_pos,
                metadata=self.metadata.copy(),
            )


class StreamingProcessor(Generic[T, C], ABC):
    """Base class for streaming document processors.

    This class provides the foundation for implementing streaming document
    processors that can process documents in a memory-efficient way.
    """

    def __init__(self, chunk_size: int = 4096):
        """Initialize the streaming processor.

        Args:
            chunk_size: The size of chunks to use when processing documents
        """
        self.chunk_size = chunk_size

    @abstractmethod
    def process_chunk(self, chunk: DocumentChunk[C]) -> T:
        """Process a document chunk.

        Args:
            chunk: The document chunk to process

        Returns:
            The processed result
        """
        pass

    def process_document(
        self, document: MemoryEfficientDocument[C]
    ) -> Generator[T, None, None]:
        """Process a document in a streaming fashion.

        Args:
            document: The document to process

        Yields:
            Processed results for each chunk
        """
        with document:
            for chunk in document.iter_chunks():
                yield self.process_chunk(chunk)

    def process_documents(
        self, documents: Iterable[MemoryEfficientDocument[C]]
    ) -> Generator[Tuple[str, T], None, None]:
        """Process multiple documents in a streaming fashion.

        Args:
            documents: The documents to process

        Yields:
            Tuples of (document_id, processed_result) for each chunk
        """
        for document in documents:
            with document:
                for chunk in document.iter_chunks():
                    yield document.document_id, self.process_chunk(chunk)


class MemoryMappedArray(Generic[T]):
    """A memory-mapped array for efficient storage and access.

    This class provides a memory-mapped array implementation for efficient
    storage and access of large arrays without loading the entire array
    into memory at once.
    """

    def __init__(
        self,
        file_path: str,
        dtype: Any,
        shape: Tuple[int, ...],
        mode: str = "r+",
    ):
        """Initialize a memory-mapped array.

        Args:
            file_path: The path to the file to use for memory mapping
            dtype: The data type of the array
            shape: The shape of the array
            mode: The mode to open the file in ('r' for read-only, 'r+' for read-write)
        """
        self.file_path = file_path
        self.dtype = dtype
        self.shape = shape
        self.mode = mode
        self._array = None

        # Import numpy lazily to avoid dependency if not used
        try:
            import numpy as np

            self._np = np
        except ImportError:
            raise PepperpyError(
                "NumPy is required for MemoryMappedArray. "
                "Install it with 'pip install numpy'."
            )

        # Create the memory-mapped array
        self._array = self._np.memmap(
            file_path,
            dtype=dtype,
            mode=mode if mode in ("r", "r+", "c", "w+") else "r+",
            shape=shape,
        )

        # Track the resource for cleanup
        track_resource(
            resource=self,
            resource_type=ResourceType.MEMORY,
            cleanup_func=lambda x: x.close(),
            metadata={"file_path": file_path, "shape": shape},
        )

    def __getitem__(self, index: Any) -> Any:
        """Get an item from the array.

        Args:
            index: The index to get

        Returns:
            The item at the specified index
        """
        if self._array is None:
            raise PepperpyError("Array is closed")
        return self._array[index]

    def __setitem__(self, index: Any, value: Any) -> None:
        """Set an item in the array.

        Args:
            index: The index to set
            value: The value to set
        """
        if self._array is None:
            raise PepperpyError("Array is closed")
        if self.mode == "r":
            raise PepperpyError("Array is read-only")
        self._array[index] = value

    def __len__(self) -> int:
        """Get the length of the array.

        Returns:
            The length of the array
        """
        if self._array is None:
            raise PepperpyError("Array is closed")
        return len(self._array)

    def flush(self) -> None:
        """Flush changes to disk."""
        if self._array is None:
            raise PepperpyError("Array is closed")
        self._array.flush()

    def close(self) -> None:
        """Close the array and release resources."""
        if self._array is not None:
            self._array.flush()
            # Delete the memmap object to close the file
            del self._array
            self._array = None
            # Force garbage collection to ensure the file is closed
            gc.collect()


class WeakCache(Generic[T]):
    """A cache that uses weak references to avoid memory leaks.

    This class provides a cache implementation that uses weak references
    to avoid memory leaks when caching large objects.
    """

    def __init__(self, max_size: Optional[int] = None):
        """Initialize a weak cache.

        Args:
            max_size: The maximum number of items to store in the cache
        """
        self.max_size = max_size
        self._cache: Dict[str, weakref.ref] = {}
        self._access_times: Dict[str, float] = {}

    def get(self, key: str) -> Optional[T]:
        """Get an item from the cache.

        Args:
            key: The key to get

        Returns:
            The item if it exists and has not been garbage collected, None otherwise
        """
        ref = self._cache.get(key)
        if ref is None:
            return None

        # Get the object from the weak reference
        obj = ref()
        if obj is None:
            # Object has been garbage collected
            del self._cache[key]
            if key in self._access_times:
                del self._access_times[key]
            return None

        # Update access time
        self._access_times[key] = time.time()
        return obj

    def put(self, key: str, value: T) -> None:
        """Put an item in the cache.

        Args:
            key: The key to store the item under
            value: The item to store
        """
        # If we've reached the maximum size, remove the least recently used item
        if self.max_size is not None and len(self._cache) >= self.max_size:
            self._remove_lru()

        # Store a weak reference to the value
        self._cache[key] = weakref.ref(value, self._on_delete)
        self._access_times[key] = time.time()

    def _remove_lru(self) -> None:
        """Remove the least recently used item from the cache."""
        if not self._access_times:
            return

        # Find the least recently used key
        lru_key = min(self._access_times.items(), key=lambda x: x[1])[0]
        del self._cache[lru_key]
        del self._access_times[lru_key]

    def _on_delete(self, ref: weakref.ref) -> None:
        """Callback when a weak reference is deleted.

        Args:
            ref: The weak reference that was deleted
        """
        # Find and remove the key for this reference
        for key, val_ref in list(self._cache.items()):
            if val_ref is ref:
                del self._cache[key]
                if key in self._access_times:
                    del self._access_times[key]
                break

    def clear(self) -> None:
        """Clear the cache."""
        self._cache.clear()
        self._access_times.clear()


class GeneratorPipeline(Generic[T, C]):
    """A pipeline for processing data using generators.

    This class provides a pipeline implementation that uses generators
    to process data in a memory-efficient way.
    """

    def __init__(self):
        """Initialize a generator pipeline."""
        self._stages: List[Callable[[Iterator[Any]], Iterator[Any]]] = []

    def add_stage(self, stage: Callable[[Iterator[Any]], Iterator[Any]]) -> None:
        """Add a stage to the pipeline.

        Args:
            stage: A function that takes an iterator and returns an iterator
        """
        self._stages.append(stage)

    def process(self, data: Iterable[T]) -> Iterator[C]:
        """Process data through the pipeline.

        Args:
            data: The data to process

        Returns:
            An iterator over the processed results
        """
        iterator = iter(data)
        for stage in self._stages:
            iterator = stage(iterator)
        return cast(Iterator[C], iterator)


class MemoryOptimizer:
    """Utility class for memory optimization.

    This class provides utility methods for optimizing memory usage
    when processing large documents.
    """

    @staticmethod
    def create_memory_efficient_document(
        document_id: str,
        source: Union[str, BinaryIO, TextIO],
        chunk_size: int = 4096,
        metadata: Optional[Dict[str, Any]] = None,
        encoding: str = "utf-8",
    ) -> MemoryEfficientDocument:
        """Create a memory-efficient document.

        Args:
            document_id: The ID of the document
            source: The source of the document (file path or file-like object)
            chunk_size: The size of chunks to use when processing the document
            metadata: Additional metadata about the document
            encoding: The encoding to use when reading text files

        Returns:
            A memory-efficient document
        """
        return MemoryEfficientDocument(
            document_id=document_id,
            source=source,
            chunk_size=chunk_size,
            metadata=metadata,
            encoding=encoding,
        )

    @staticmethod
    def create_memory_mapped_array(
        file_path: str,
        dtype: Any,
        shape: Tuple[int, ...],
        mode: str = "r+",
    ) -> MemoryMappedArray:
        """Create a memory-mapped array.

        Args:
            file_path: The path to the file to use for memory mapping
            dtype: The data type of the array
            shape: The shape of the array
            mode: The mode to open the file in ('r' for read-only, 'r+' for read-write)

        Returns:
            A memory-mapped array
        """
        return MemoryMappedArray(
            file_path=file_path,
            dtype=dtype,
            shape=shape,
            mode=mode,
        )

    @staticmethod
    def create_weak_cache(max_size: Optional[int] = None) -> WeakCache:
        """Create a weak cache.

        Args:
            max_size: The maximum number of items to store in the cache

        Returns:
            A weak cache
        """
        return WeakCache(max_size=max_size)

    @staticmethod
    def create_generator_pipeline() -> GeneratorPipeline:
        """Create a generator pipeline.

        Returns:
            A generator pipeline
        """
        return GeneratorPipeline()

    @staticmethod
    def optimize_memory_usage() -> None:
        """Optimize memory usage by running garbage collection."""
        gc.collect()

    @staticmethod
    def get_memory_usage() -> Dict[str, Any]:
        """Get memory usage statistics.

        Returns:
            A dictionary of memory usage statistics
        """
        try:
            import psutil

            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            return {
                "rss": memory_info.rss,  # Resident Set Size
                "vms": memory_info.vms,  # Virtual Memory Size
                "shared": getattr(memory_info, "shared", 0),  # Shared memory
                "text": getattr(memory_info, "text", 0),  # Text (code)
                "data": getattr(memory_info, "data", 0),  # Data + stack
                "lib": getattr(memory_info, "lib", 0),  # Library
                "dirty": getattr(memory_info, "dirty", 0),  # Dirty pages
                "percent": process.memory_percent(),  # Percentage of total system memory
            }
        except ImportError:
            # Fallback if psutil is not available
            return {
                "rss": 0,
                "vms": 0,
                "percent": 0,
                "available": False,
                "message": "psutil not installed. Install with 'pip install psutil'",
            }


# Convenience functions


def create_memory_efficient_document(
    document_id: str,
    source: Union[str, BinaryIO, TextIO],
    chunk_size: int = 4096,
    metadata: Optional[Dict[str, Any]] = None,
    encoding: str = "utf-8",
) -> MemoryEfficientDocument:
    """Create a memory-efficient document.

    Args:
        document_id: The ID of the document
        source: The source of the document (file path or file-like object)
        chunk_size: The size of chunks to use when processing the document
        metadata: Additional metadata about the document
        encoding: The encoding to use when reading text files

    Returns:
        A memory-efficient document
    """
    return MemoryOptimizer.create_memory_efficient_document(
        document_id=document_id,
        source=source,
        chunk_size=chunk_size,
        metadata=metadata,
        encoding=encoding,
    )


def create_memory_mapped_array(
    file_path: str,
    dtype: Any,
    shape: Tuple[int, ...],
    mode: str = "r+",
) -> MemoryMappedArray:
    """Create a memory-mapped array.

    Args:
        file_path: The path to the file to use for memory mapping
        dtype: The data type of the array
        shape: The shape of the array
        mode: The mode to open the file in ('r' for read-only, 'r+' for read-write)

    Returns:
        A memory-mapped array
    """
    return MemoryOptimizer.create_memory_mapped_array(
        file_path=file_path,
        dtype=dtype,
        shape=shape,
        mode=mode,
    )


def create_weak_cache(max_size: Optional[int] = None) -> WeakCache:
    """Create a weak cache.

    Args:
        max_size: The maximum number of items to store in the cache

    Returns:
        A weak cache
    """
    return MemoryOptimizer.create_weak_cache(max_size=max_size)


def create_generator_pipeline() -> GeneratorPipeline:
    """Create a generator pipeline.

    Returns:
        A generator pipeline
    """
    return MemoryOptimizer.create_generator_pipeline()


def optimize_memory_usage() -> None:
    """Optimize memory usage by running garbage collection."""
    MemoryOptimizer.optimize_memory_usage()


def get_memory_usage() -> Dict[str, Any]:
    """Get memory usage statistics.

    Returns:
        A dictionary of memory usage statistics
    """
    return MemoryOptimizer.get_memory_usage()
