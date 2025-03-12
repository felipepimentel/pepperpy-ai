"""Memory-efficient data structures for large collections.

This module provides memory-efficient data structures for working with large
collections of data, including disk-backed arrays, memory-mapped dictionaries,
and streaming collections.
"""

import mmap
import os
import pickle
import tempfile
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import (
    Any,
    Dict,
    Generic,
    Iterator,
    List,
    Optional,
    Sequence,
    TypeVar,
    Union,
    cast,
)

from pepperpy.errors import PepperpyError
from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)

# Type variables
T = TypeVar("T")  # Value type
K = TypeVar("K")  # Key type


class StorageStrategy(Enum):
    """Enum representing different storage strategies."""

    MEMORY_MAPPED = auto()  # Use memory-mapped files
    DISK_BACKED = auto()  # Use disk-backed storage
    STREAMING = auto()  # Use streaming storage
    CHUNKED = auto()  # Use chunked storage
    CUSTOM = auto()  # Custom storage strategy


@dataclass
class CollectionConfig:
    """Configuration for memory-efficient collections.

    This class defines the configuration for memory-efficient collections,
    including storage strategy, chunk size, and file paths.
    """

    # The strategy to use for storage
    strategy: StorageStrategy = StorageStrategy.MEMORY_MAPPED
    # The size of chunks for chunked storage
    chunk_size: int = 1024 * 1024  # 1MB
    # The directory to store data files
    storage_dir: Optional[Path] = None
    # Whether to compress stored data
    compress: bool = False
    # Custom storage function (for CUSTOM strategy)
    custom_storage: Optional[Any] = None


class MemoryEfficientCollection(Generic[T], ABC):
    """Base class for memory-efficient collections.

    This class provides the foundation for implementing memory-efficient
    collections that can handle large amounts of data without loading
    everything into memory at once.
    """

    def __init__(self, config: Optional[CollectionConfig] = None):
        """Initialize the collection.

        Args:
            config: The collection configuration
        """
        self.config = config or CollectionConfig()
        self.storage_dir = self.config.storage_dir or Path(tempfile.gettempdir())
        self._size = 0
        self._file_path: Optional[Path] = None
        self._mmap: Optional[mmap.mmap] = None

    def __len__(self) -> int:
        """Get the length of the collection.

        Returns:
            The number of items in the collection
        """
        return self._size

    @abstractmethod
    def __iter__(self) -> Iterator[T]:
        """Get an iterator over the collection.

        Returns:
            An iterator over the collection
        """
        pass

    def __enter__(self) -> "MemoryEfficientCollection[T]":
        """Enter the context manager.

        Returns:
            The collection
        """
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit the context manager.

        Args:
            exc_type: The exception type
            exc_val: The exception value
            exc_tb: The exception traceback
        """
        self.close()

    def close(self) -> None:
        """Close the collection and release resources."""
        if self._mmap is not None:
            self._mmap.close()
            self._mmap = None
        if (
            self._file_path is not None
            and self.config.strategy != StorageStrategy.DISK_BACKED
        ):
            try:
                os.unlink(str(self._file_path))
            except OSError:
                pass
            self._file_path = None


class MemoryMappedArray(MemoryEfficientCollection[T]):
    """Memory-mapped array for efficient storage of large sequences.

    This class provides a memory-mapped array implementation that can handle
    large sequences without loading everything into memory at once.
    """

    def __init__(
        self,
        data: Optional[Sequence[T]] = None,
        config: Optional[CollectionConfig] = None,
    ):
        """Initialize the memory-mapped array.

        Args:
            data: Initial data to store
            config: The collection configuration
        """
        super().__init__(config)
        if not self.storage_dir.exists():
            self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._file_path = self.storage_dir / f"mmap_array_{id(self)}.bin"
        self._initialize(data)

    def _initialize(self, data: Optional[Sequence[T]] = None) -> None:
        """Initialize the memory-mapped array.

        Args:
            data: Initial data to store
        """
        if not self._file_path:
            raise PepperpyError("File path not initialized")

        if data is not None:
            # Write data to file
            with open(str(self._file_path), "wb") as f:
                for item in data:
                    pickle.dump(item, f)
            self._size = len(data)
        else:
            # Create empty file
            with open(str(self._file_path), "wb") as f:
                pass
            self._size = 0

        # Memory map the file
        self._mmap = mmap.mmap(
            os.open(str(self._file_path), os.O_RDWR),
            0,
            access=mmap.ACCESS_WRITE,
        )

    def __getitem__(self, index: int) -> T:
        """Get an item from the array.

        Args:
            index: The index of the item

        Returns:
            The item at the index

        Raises:
            IndexError: If the index is out of range
        """
        if not 0 <= index < self._size:
            raise IndexError("Index out of range")

        if self._mmap is None:
            raise PepperpyError("Array is closed")

        # Seek to the start of the file
        self._mmap.seek(0)

        # Skip to the desired index
        for _ in range(index):
            pickle.load(self._mmap)

        # Load the item at the index
        return cast(T, pickle.load(self._mmap))

    def __setitem__(self, index: int, value: T) -> None:
        """Set an item in the array.

        Args:
            index: The index to set
            value: The value to set

        Raises:
            IndexError: If the index is out of range
        """
        if not 0 <= index < self._size:
            raise IndexError("Index out of range")

        if self._mmap is None:
            raise PepperpyError("Array is closed")

        if not self._file_path:
            raise PepperpyError("File path not initialized")

        # Create a temporary file for the new data
        temp_path = self._file_path.with_suffix(".tmp")
        with open(str(temp_path), "wb") as f:
            # Copy items before the index
            self._mmap.seek(0)
            for _ in range(index):
                item = pickle.load(self._mmap)
                pickle.dump(item, f)

            # Write the new value
            pickle.dump(value, f)

            # Skip the old value
            pickle.load(self._mmap)

            # Copy remaining items
            while self._mmap.tell() < self._mmap.size():
                try:
                    item = pickle.load(self._mmap)
                    pickle.dump(item, f)
                except EOFError:
                    break

        # Close the current memory map
        self._mmap.close()

        # Replace the old file with the new one
        os.replace(str(temp_path), str(self._file_path))

        # Memory map the new file
        self._mmap = mmap.mmap(
            os.open(str(self._file_path), os.O_RDWR),
            0,
            access=mmap.ACCESS_WRITE,
        )

    def append(self, value: T) -> None:
        """Append an item to the array.

        Args:
            value: The value to append
        """
        if self._mmap is None:
            raise PepperpyError("Array is closed")

        # Seek to the end of the file
        self._mmap.seek(0, os.SEEK_END)

        # Write the new value
        pickle.dump(value, self._mmap)
        self._size += 1

    def __iter__(self) -> Iterator[T]:
        """Get an iterator over the array.

        Returns:
            An iterator over the array
        """
        if self._mmap is None:
            raise PepperpyError("Array is closed")

        # Seek to the start of the file
        self._mmap.seek(0)

        # Yield each item
        for _ in range(self._size):
            yield cast(T, pickle.load(self._mmap))


class MemoryMappedDict(MemoryEfficientCollection[Dict[K, T]]):
    """Memory-mapped dictionary for efficient storage of large mappings.

    This class provides a memory-mapped dictionary implementation that can
    handle large mappings without loading everything into memory at once.
    """

    def __init__(
        self,
        data: Optional[Dict[K, T]] = None,
        config: Optional[CollectionConfig] = None,
    ):
        """Initialize the memory-mapped dictionary.

        Args:
            data: Initial data to store
            config: The collection configuration
        """
        super().__init__(config)
        if not self.storage_dir.exists():
            self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._file_path = self.storage_dir / f"mmap_dict_{id(self)}.bin"
        self._initialize(data)

    def _initialize(self, data: Optional[Dict[K, T]] = None) -> None:
        """Initialize the memory-mapped dictionary.

        Args:
            data: Initial data to store
        """
        if not self._file_path:
            raise PepperpyError("File path not initialized")

        if data is not None:
            # Write data to file
            with open(str(self._file_path), "wb") as f:
                pickle.dump(data, f)
            self._size = len(data)
        else:
            # Create empty dictionary
            with open(str(self._file_path), "wb") as f:
                pickle.dump({}, f)
            self._size = 0

        # Memory map the file
        self._mmap = mmap.mmap(
            os.open(str(self._file_path), os.O_RDWR),
            0,
            access=mmap.ACCESS_WRITE,
        )

    def __getitem__(self, key: K) -> T:
        """Get a value from the dictionary.

        Args:
            key: The key to get

        Returns:
            The value for the key

        Raises:
            KeyError: If the key doesn't exist
        """
        if self._mmap is None:
            raise PepperpyError("Dictionary is closed")

        # Seek to the start of the file
        self._mmap.seek(0)

        # Load the entire dictionary (this could be optimized)
        data = cast(Dict[K, T], pickle.load(self._mmap))
        if key not in data:
            raise KeyError(key)

        return data[key]

    def __setitem__(self, key: K, value: T) -> None:
        """Set a value in the dictionary.

        Args:
            key: The key to set
            value: The value to set
        """
        if self._mmap is None:
            raise PepperpyError("Dictionary is closed")

        # Seek to the start of the file
        self._mmap.seek(0)

        # Load the entire dictionary
        data = cast(Dict[K, T], pickle.load(self._mmap))

        # Update the dictionary
        if key not in data:
            self._size += 1
        data[key] = value

        # Write the updated dictionary
        self._mmap.seek(0)
        pickle.dump(data, self._mmap)

    def __iter__(self) -> Iterator[K]:
        """Get an iterator over the dictionary keys.

        Returns:
            An iterator over the dictionary keys
        """
        if self._mmap is None:
            raise PepperpyError("Dictionary is closed")

        # Seek to the start of the file
        self._mmap.seek(0)

        # Load the entire dictionary
        data = cast(Dict[K, T], pickle.load(self._mmap))
        return iter(data)

    def items(self) -> Iterator[tuple[K, T]]:
        """Get an iterator over the dictionary items.

        Returns:
            An iterator over the dictionary items
        """
        if self._mmap is None:
            raise PepperpyError("Dictionary is closed")

        # Seek to the start of the file
        self._mmap.seek(0)

        # Load the entire dictionary
        data = cast(Dict[K, T], pickle.load(self._mmap))
        return iter(data.items())


class StreamingSequence(MemoryEfficientCollection[T]):
    """Streaming sequence for efficient processing of large sequences.

    This class provides a streaming sequence implementation that can process
    large sequences without loading everything into memory at once.
    """

    def __init__(
        self,
        data: Optional[Sequence[T]] = None,
        config: Optional[CollectionConfig] = None,
    ):
        """Initialize the streaming sequence.

        Args:
            data: Initial data to store
            config: The collection configuration
        """
        super().__init__(config)
        if not self.storage_dir.exists():
            self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._file_path = self.storage_dir / f"stream_seq_{id(self)}.bin"
        self._initialize(data)

    def _initialize(self, data: Optional[Sequence[T]] = None) -> None:
        """Initialize the streaming sequence.

        Args:
            data: Initial data to store
        """
        if not self._file_path:
            raise PepperpyError("File path not initialized")

        if data is not None:
            # Write data to file in chunks
            with open(str(self._file_path), "wb") as f:
                chunk: List[T] = []
                for item in data:
                    chunk.append(item)
                    if len(chunk) >= self.config.chunk_size:
                        pickle.dump(chunk, f)
                        chunk = []
                if chunk:
                    pickle.dump(chunk, f)
            self._size = len(data)
        else:
            # Create empty file
            with open(str(self._file_path), "wb") as f:
                pass
            self._size = 0

    def __iter__(self) -> Iterator[T]:
        """Get an iterator over the sequence.

        Returns:
            An iterator over the sequence
        """
        if not self._file_path or not self._file_path.exists():
            return iter([])

        with open(str(self._file_path), "rb") as f:
            while True:
                try:
                    chunk = pickle.load(f)
                    yield from chunk
                except EOFError:
                    break

    def append(self, value: T) -> None:
        """Append an item to the sequence.

        Args:
            value: The value to append
        """
        if not self._file_path:
            raise PepperpyError("File path not initialized")

        # Load the last chunk if it exists
        last_chunk: List[T] = []
        if self._file_path.exists():
            with open(str(self._file_path), "rb") as f:
                while True:
                    try:
                        last_chunk = pickle.load(f)
                    except EOFError:
                        break

        # Add the new value to the chunk
        last_chunk.append(value)
        self._size += 1

        # Write the chunk if it's full
        if len(last_chunk) >= self.config.chunk_size:
            with open(str(self._file_path), "ab") as f:
                pickle.dump(last_chunk, f)
            last_chunk = []
        else:
            # Write the partial chunk
            with open(str(self._file_path), "wb") as f:
                pickle.dump(last_chunk, f)


def create_memory_efficient_collection(
    collection_type: str = "array",
    data: Optional[Union[Sequence[T], Dict[K, T]]] = None,
    config: Optional[CollectionConfig] = None,
) -> MemoryEfficientCollection:
    """Create a memory-efficient collection.

    Args:
        collection_type: The type of collection to create
        data: Initial data to store
        config: The collection configuration

    Returns:
        A memory-efficient collection

    Raises:
        ValueError: If the collection type is invalid
    """
    if collection_type == "array":
        return MemoryMappedArray(cast(Optional[Sequence[T]], data), config)
    elif collection_type == "dict":
        return MemoryMappedDict(cast(Optional[Dict[K, T]], data), config)
    elif collection_type == "stream":
        return StreamingSequence(cast(Optional[Sequence[T]], data), config)
    else:
        raise ValueError(f"Invalid collection type: {collection_type}")
