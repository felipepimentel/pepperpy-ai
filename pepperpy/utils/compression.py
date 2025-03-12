"""Data compression and optimization utilities.

This module provides utilities for compressing and optimizing data, including
various compression algorithms, serialization formats, and optimization
strategies for large datasets.
"""

import base64
import gzip
import json
import lzma
import pickle
import zlib
from enum import Enum
from io import BytesIO
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar, Union

import msgpack
import numpy as np

from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)

# Type variables for data types
T = TypeVar("T")
U = TypeVar("U")


class CompressionAlgorithm(Enum):
    """Compression algorithm.

    This enum defines the compression algorithm to use.
    """

    # GZIP compression (good balance of speed and compression ratio)
    GZIP = "gzip"
    # ZLIB compression (similar to GZIP but with different header/footer)
    ZLIB = "zlib"
    # LZMA compression (high compression ratio but slower)
    LZMA = "lzma"
    # No compression (useful for already compressed data)
    NONE = "none"


class SerializationFormat(Enum):
    """Serialization format.

    This enum defines the serialization format to use.
    """

    # JSON serialization (human-readable, widely supported)
    JSON = "json"
    # MessagePack serialization (binary, more compact than JSON)
    MSGPACK = "msgpack"
    # Pickle serialization (Python-specific, supports more types)
    PICKLE = "pickle"
    # Raw bytes (no serialization, for already serialized data)
    RAW = "raw"


class CompressionLevel(Enum):
    """Compression level.

    This enum defines the level of compression to apply.
    """

    # No compression
    NONE = 0
    # Fast compression (minimal CPU usage, lower compression ratio)
    FAST = 1
    # Default compression (balanced CPU usage and compression ratio)
    DEFAULT = 6
    # Best compression (maximum CPU usage, highest compression ratio)
    BEST = 9


class DataCompressor:
    """Data compressor.

    This class provides methods for compressing and decompressing data using
    various algorithms and serialization formats.
    """

    def __init__(
        self,
        algorithm: CompressionAlgorithm = CompressionAlgorithm.GZIP,
        serialization: SerializationFormat = SerializationFormat.JSON,
        level: CompressionLevel = CompressionLevel.DEFAULT,
    ):
        """Initialize a data compressor.

        Args:
            algorithm: The compression algorithm to use
            serialization: The serialization format to use
            level: The compression level to apply
        """
        self.algorithm = algorithm
        self.serialization = serialization
        self.level = level

    def compress(self, data: Any) -> bytes:
        """Compress data.

        Args:
            data: The data to compress

        Returns:
            The compressed data as bytes

        Raises:
            ValueError: If the data cannot be serialized or compressed
        """
        # Serialize the data
        serialized = self._serialize(data)

        # Compress the serialized data
        compressed = self._compress(serialized)

        return compressed

    def decompress(self, data: bytes) -> Any:
        """Decompress data.

        Args:
            data: The compressed data as bytes

        Returns:
            The decompressed data

        Raises:
            ValueError: If the data cannot be decompressed or deserialized
        """
        # Decompress the data
        decompressed = self._decompress(data)

        # Deserialize the decompressed data
        deserialized = self._deserialize(decompressed)

        return deserialized

    def _serialize(self, data: Any) -> bytes:
        """Serialize data.

        Args:
            data: The data to serialize

        Returns:
            The serialized data as bytes

        Raises:
            ValueError: If the data cannot be serialized
        """
        try:
            if self.serialization == SerializationFormat.JSON:
                return json.dumps(data).encode("utf-8")
            elif self.serialization == SerializationFormat.MSGPACK:
                return msgpack.packb(data, use_bin_type=True)
            elif self.serialization == SerializationFormat.PICKLE:
                return pickle.dumps(data)
            elif self.serialization == SerializationFormat.RAW:
                if isinstance(data, bytes):
                    return data
                elif isinstance(data, str):
                    return data.encode("utf-8")
                else:
                    raise ValueError(
                        f"Raw serialization requires bytes or str, got {type(data)}"
                    )
            else:
                raise ValueError(
                    f"Unsupported serialization format: {self.serialization}"
                )
        except Exception as e:
            raise ValueError(f"Failed to serialize data: {e}")

    def _deserialize(self, data: bytes) -> Any:
        """Deserialize data.

        Args:
            data: The serialized data as bytes

        Returns:
            The deserialized data

        Raises:
            ValueError: If the data cannot be deserialized
        """
        try:
            if self.serialization == SerializationFormat.JSON:
                return json.loads(data.decode("utf-8"))
            elif self.serialization == SerializationFormat.MSGPACK:
                return msgpack.unpackb(data, raw=False)
            elif self.serialization == SerializationFormat.PICKLE:
                return pickle.loads(data)
            elif self.serialization == SerializationFormat.RAW:
                return data
            else:
                raise ValueError(
                    f"Unsupported serialization format: {self.serialization}"
                )
        except Exception as e:
            raise ValueError(f"Failed to deserialize data: {e}")

    def _compress(self, data: bytes) -> bytes:
        """Compress serialized data.

        Args:
            data: The serialized data as bytes

        Returns:
            The compressed data as bytes

        Raises:
            ValueError: If the data cannot be compressed
        """
        try:
            level = self.level.value
            if self.algorithm == CompressionAlgorithm.GZIP:
                return gzip.compress(data, compresslevel=level)
            elif self.algorithm == CompressionAlgorithm.ZLIB:
                return zlib.compress(data, level=level)
            elif self.algorithm == CompressionAlgorithm.LZMA:
                return lzma.compress(data, preset=level)
            elif self.algorithm == CompressionAlgorithm.NONE:
                return data
            else:
                raise ValueError(f"Unsupported compression algorithm: {self.algorithm}")
        except Exception as e:
            raise ValueError(f"Failed to compress data: {e}")

    def _decompress(self, data: bytes) -> bytes:
        """Decompress data.

        Args:
            data: The compressed data as bytes

        Returns:
            The decompressed data as bytes

        Raises:
            ValueError: If the data cannot be decompressed
        """
        try:
            if self.algorithm == CompressionAlgorithm.GZIP:
                return gzip.decompress(data)
            elif self.algorithm == CompressionAlgorithm.ZLIB:
                return zlib.decompress(data)
            elif self.algorithm == CompressionAlgorithm.LZMA:
                return lzma.decompress(data)
            elif self.algorithm == CompressionAlgorithm.NONE:
                return data
            else:
                raise ValueError(f"Unsupported compression algorithm: {self.algorithm}")
        except Exception as e:
            raise ValueError(f"Failed to decompress data: {e}")


class CompressedData:
    """Compressed data container.

    This class represents compressed data, including metadata about the
    compression algorithm, serialization format, and compression level.
    """

    def __init__(
        self,
        data: bytes,
        algorithm: CompressionAlgorithm,
        serialization: SerializationFormat,
        level: CompressionLevel,
        original_size: Optional[int] = None,
    ):
        """Initialize compressed data.

        Args:
            data: The compressed data as bytes
            algorithm: The compression algorithm used
            serialization: The serialization format used
            level: The compression level applied
            original_size: The size of the original data in bytes, or None if unknown
        """
        self.data = data
        self.algorithm = algorithm
        self.serialization = serialization
        self.level = level
        self.original_size = original_size
        self.compressed_size = len(data)

    @property
    def compression_ratio(self) -> Optional[float]:
        """Get the compression ratio.

        Returns:
            The compression ratio (original size / compressed size),
            or None if the original size is unknown
        """
        if self.original_size is None:
            return None
        return self.original_size / self.compressed_size

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary.

        Returns:
            A dictionary representation of the compressed data
        """
        return {
            "data": base64.b64encode(self.data).decode("ascii"),
            "algorithm": self.algorithm.value,
            "serialization": self.serialization.value,
            "level": self.level.value,
            "original_size": self.original_size,
            "compressed_size": self.compressed_size,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CompressedData":
        """Create from a dictionary.

        Args:
            data: A dictionary representation of compressed data

        Returns:
            A CompressedData object

        Raises:
            ValueError: If the dictionary is invalid
        """
        try:
            return cls(
                data=base64.b64decode(data["data"]),
                algorithm=CompressionAlgorithm(data["algorithm"]),
                serialization=SerializationFormat(data["serialization"]),
                level=CompressionLevel(data["level"]),
                original_size=data.get("original_size"),
            )
        except Exception as e:
            raise ValueError(f"Invalid compressed data dictionary: {e}")

    def decompress(self) -> Any:
        """Decompress the data.

        Returns:
            The decompressed data

        Raises:
            ValueError: If the data cannot be decompressed
        """
        compressor = DataCompressor(
            algorithm=self.algorithm,
            serialization=self.serialization,
            level=self.level,
        )
        return compressor.decompress(self.data)

    def __len__(self) -> int:
        """Return the length of the compressed data.

        Returns:
            The length of the compressed data in bytes
        """
        return len(self.data)


class DatasetOptimizer:
    """Dataset optimizer.

    This class provides methods for optimizing large datasets, including
    compression, chunking, and filtering.
    """

    def __init__(
        self,
        compressor: Optional[DataCompressor] = None,
        chunk_size: int = 1000,
    ):
        """Initialize a dataset optimizer.

        Args:
            compressor: The data compressor to use, or None to use the default
            chunk_size: The number of items per chunk for chunked operations
        """
        self.compressor = compressor or DataCompressor()
        self.chunk_size = chunk_size

    def compress_dataset(
        self, dataset: List[Any], compute_original_size: bool = True
    ) -> CompressedData:
        """Compress a dataset.

        Args:
            dataset: The dataset to compress
            compute_original_size: Whether to compute the original size of the dataset

        Returns:
            The compressed dataset
        """
        # Compute the original size if requested
        original_size = None
        if compute_original_size:
            # Serialize the dataset to compute its size
            serialized = self.compressor._serialize(dataset)
            original_size = len(serialized)

        # Compress the dataset
        compressed = self.compressor.compress(dataset)

        # Create a CompressedData object
        return CompressedData(
            data=compressed,
            algorithm=self.compressor.algorithm,
            serialization=self.compressor.serialization,
            level=self.compressor.level,
            original_size=original_size,
        )

    def decompress_dataset(self, compressed_data: CompressedData) -> List[Any]:
        """Decompress a dataset.

        Args:
            compressed_data: The compressed dataset

        Returns:
            The decompressed dataset
        """
        # Decompress the dataset
        decompressed = compressed_data.decompress()

        # Ensure the result is a list
        if not isinstance(decompressed, list):
            raise ValueError(f"Expected a list, got {type(decompressed)}")

        return decompressed

    def chunk_dataset(self, dataset: List[Any]) -> List[List[Any]]:
        """Split a dataset into chunks.

        Args:
            dataset: The dataset to chunk

        Returns:
            A list of dataset chunks
        """
        return [
            dataset[i : i + self.chunk_size]
            for i in range(0, len(dataset), self.chunk_size)
        ]

    def filter_dataset(
        self, dataset: List[Any], predicate: Callable[[Any], bool]
    ) -> List[Any]:
        """Filter a dataset.

        Args:
            dataset: The dataset to filter
            predicate: A function that returns True for items to keep

        Returns:
            The filtered dataset
        """
        return [item for item in dataset if predicate(item)]

    def map_dataset(
        self, dataset: List[Any], mapper: Callable[[Any], Any]
    ) -> List[Any]:
        """Apply a function to each item in a dataset.

        Args:
            dataset: The dataset to map
            mapper: A function to apply to each item

        Returns:
            The mapped dataset
        """
        return [mapper(item) for item in dataset]

    def process_large_dataset(
        self,
        dataset: List[Any],
        processor: Callable[[List[Any]], List[Any]],
        compress_result: bool = True,
    ) -> Union[List[Any], CompressedData]:
        """Process a large dataset in chunks.

        Args:
            dataset: The dataset to process
            processor: A function that processes a chunk of the dataset
            compress_result: Whether to compress the result

        Returns:
            The processed dataset, either as a list or as compressed data
        """
        # Split the dataset into chunks
        chunks = self.chunk_dataset(dataset)

        # Process each chunk
        processed_chunks = []
        for chunk in chunks:
            processed_chunk = processor(chunk)
            processed_chunks.extend(processed_chunk)

        # Compress the result if requested
        if compress_result:
            return self.compress_dataset(processed_chunks)
        else:
            return processed_chunks


class NumpyCompressor:
    """NumPy array compressor.

    This class provides methods for compressing and decompressing NumPy arrays,
    which can be more efficient than general-purpose compression for numerical data.
    """

    def __init__(
        self,
        algorithm: CompressionAlgorithm = CompressionAlgorithm.GZIP,
        level: CompressionLevel = CompressionLevel.DEFAULT,
    ):
        """Initialize a NumPy array compressor.

        Args:
            algorithm: The compression algorithm to use
            level: The compression level to apply
        """
        self.algorithm = algorithm
        self.level = level

    def compress(self, array: np.ndarray) -> bytes:
        """Compress a NumPy array.

        Args:
            array: The NumPy array to compress

        Returns:
            The compressed array as bytes

        Raises:
            ValueError: If the array cannot be compressed
        """
        # Save the array to a BytesIO object
        buffer = BytesIO()
        np.save(buffer, array)
        buffer.seek(0)
        data = buffer.read()

        # Compress the data
        compressor = DataCompressor(
            algorithm=self.algorithm,
            serialization=SerializationFormat.RAW,
            level=self.level,
        )
        return compressor.compress(data)

    def decompress(self, data: bytes) -> np.ndarray:
        """Decompress a NumPy array.

        Args:
            data: The compressed array as bytes

        Returns:
            The decompressed NumPy array

        Raises:
            ValueError: If the data cannot be decompressed
        """
        # Decompress the data
        compressor = DataCompressor(
            algorithm=self.algorithm,
            serialization=SerializationFormat.RAW,
            level=self.level,
        )
        decompressed = compressor.decompress(data)

        # Load the array from the decompressed data
        buffer = BytesIO(decompressed)
        return np.load(buffer)


class JsonCompressor:
    """JSON compressor.

    This class provides methods for compressing and decompressing JSON data,
    with optimizations specific to JSON structure.
    """

    def __init__(
        self,
        algorithm: CompressionAlgorithm = CompressionAlgorithm.GZIP,
        level: CompressionLevel = CompressionLevel.DEFAULT,
        optimize_keys: bool = True,
    ):
        """Initialize a JSON compressor.

        Args:
            algorithm: The compression algorithm to use
            level: The compression level to apply
            optimize_keys: Whether to optimize repeated keys in the JSON data
        """
        self.algorithm = algorithm
        self.level = level
        self.optimize_keys = optimize_keys

    def compress(self, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> bytes:
        """Compress JSON data.

        Args:
            data: The JSON data to compress

        Returns:
            The compressed data as bytes

        Raises:
            ValueError: If the data cannot be compressed
        """
        # Optimize the JSON data if requested
        if self.optimize_keys:
            optimized_data, key_map = self._optimize_json(data)
            # Combine the optimized data and key map
            combined_data = {"data": optimized_data, "key_map": key_map}
        else:
            combined_data = {"data": data, "key_map": None}

        # Compress the data
        compressor = DataCompressor(
            algorithm=self.algorithm,
            serialization=SerializationFormat.JSON,
            level=self.level,
        )
        return compressor.compress(combined_data)

    def decompress(self, data: bytes) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Decompress JSON data.

        Args:
            data: The compressed data as bytes

        Returns:
            The decompressed JSON data

        Raises:
            ValueError: If the data cannot be decompressed
        """
        # Decompress the data
        compressor = DataCompressor(
            algorithm=self.algorithm,
            serialization=SerializationFormat.JSON,
            level=self.level,
        )
        combined_data = compressor.decompress(data)

        # Extract the data and key map
        json_data = combined_data["data"]
        key_map = combined_data["key_map"]

        # Restore the original keys if optimized
        if key_map is not None:
            return self._restore_json(json_data, key_map)
        else:
            return json_data

    def _optimize_json(
        self, data: Union[Dict[str, Any], List[Dict[str, Any]]]
    ) -> Tuple[Union[Dict[int, Any], List[Dict[int, Any]]], Dict[int, str]]:
        """Optimize JSON data by replacing repeated keys with integer IDs.

        Args:
            data: The JSON data to optimize

        Returns:
            A tuple of (optimized_data, key_map), where optimized_data has integer
            keys instead of string keys, and key_map maps integer IDs to original keys
        """
        # Extract all keys from the JSON data
        keys = set()
        if isinstance(data, dict):
            keys.update(data.keys())
        else:
            for item in data:
                if isinstance(item, dict):
                    keys.update(item.keys())

        # Create a mapping from keys to integer IDs
        key_map = {i: key for i, key in enumerate(sorted(keys))}
        reverse_map = {key: i for i, key in key_map.items()}

        # Replace keys with integer IDs
        if isinstance(data, dict):
            optimized_data = {reverse_map[key]: value for key, value in data.items()}
        else:
            optimized_data = []
            for item in data:
                if isinstance(item, dict):
                    optimized_item = {
                        reverse_map[key]: value for key, value in item.items()
                    }
                    optimized_data.append(optimized_item)
                else:
                    optimized_data.append(item)

        return optimized_data, key_map

    def _restore_json(
        self,
        data: Union[Dict[Any, Any], List[Dict[Any, Any]]],
        key_map: Dict[int, str],
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Restore original keys in optimized JSON data.

        Args:
            data: The optimized JSON data with integer keys
            key_map: A mapping from integer IDs to original keys

        Returns:
            The JSON data with original string keys
        """
        # Replace integer IDs with original keys
        if isinstance(data, dict):
            restored_data = {}
            for key, value in data.items():
                if isinstance(key, int):
                    restored_data[key_map[key]] = value
                elif isinstance(key, str) and key.isdigit():
                    restored_data[key_map[int(key)]] = value
        else:
            restored_data = []
            for item in data:
                if isinstance(item, dict):
                    restored_item = {}
                    for key, value in item.items():
                        if isinstance(key, int):
                            restored_item[key_map[key]] = value
                        elif isinstance(key, str) and key.isdigit():
                            restored_item[key_map[int(key)]] = value
                    restored_data.append(restored_item)
                else:
                    restored_data.append(item)

        return restored_data


# Convenience functions


def compress_data(
    data: Any,
    algorithm: CompressionAlgorithm = CompressionAlgorithm.GZIP,
    serialization: SerializationFormat = SerializationFormat.JSON,
    level: CompressionLevel = CompressionLevel.DEFAULT,
) -> bytes:
    """Compress data using the specified algorithm and serialization format.

    Args:
        data: The data to compress
        algorithm: The compression algorithm to use
        serialization: The serialization format to use
        level: The compression level to apply

    Returns:
        The compressed data as bytes

    Raises:
        ValueError: If the data cannot be serialized or compressed
    """
    compressor = DataCompressor(
        algorithm=algorithm,
        serialization=serialization,
        level=level,
    )
    return compressor.compress(data)


def decompress_data(
    data: bytes,
    algorithm: CompressionAlgorithm = CompressionAlgorithm.GZIP,
    serialization: SerializationFormat = SerializationFormat.JSON,
    level: CompressionLevel = CompressionLevel.DEFAULT,
) -> Any:
    """Decompress data using the specified algorithm and serialization format.

    Args:
        data: The compressed data as bytes
        algorithm: The compression algorithm used
        serialization: The serialization format used
        level: The compression level applied

    Returns:
        The decompressed data

    Raises:
        ValueError: If the data cannot be decompressed or deserialized
    """
    compressor = DataCompressor(
        algorithm=algorithm,
        serialization=serialization,
        level=level,
    )
    return compressor.decompress(data)


def compress_json(
    data: Union[Dict[str, Any], List[Dict[str, Any]]],
    algorithm: CompressionAlgorithm = CompressionAlgorithm.GZIP,
    level: CompressionLevel = CompressionLevel.DEFAULT,
    optimize_keys: bool = True,
) -> bytes:
    """Compress JSON data with optimizations specific to JSON structure.

    Args:
        data: The JSON data to compress
        algorithm: The compression algorithm to use
        level: The compression level to apply
        optimize_keys: Whether to optimize repeated keys in the JSON data

    Returns:
        The compressed data as bytes

    Raises:
        ValueError: If the data cannot be compressed
    """
    compressor = JsonCompressor(
        algorithm=algorithm,
        level=level,
        optimize_keys=optimize_keys,
    )
    return compressor.compress(data)


def decompress_json(
    data: bytes,
    algorithm: CompressionAlgorithm = CompressionAlgorithm.GZIP,
    level: CompressionLevel = CompressionLevel.DEFAULT,
    optimize_keys: bool = True,
) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """Decompress JSON data with optimizations specific to JSON structure.

    Args:
        data: The compressed data as bytes
        algorithm: The compression algorithm used
        level: The compression level applied
        optimize_keys: Whether the data was compressed with key optimization

    Returns:
        The decompressed JSON data

    Raises:
        ValueError: If the data cannot be decompressed
    """
    compressor = JsonCompressor(
        algorithm=algorithm,
        level=level,
        optimize_keys=optimize_keys,
    )
    return compressor.decompress(data)


def compress_numpy(
    array: np.ndarray,
    algorithm: CompressionAlgorithm = CompressionAlgorithm.GZIP,
    level: CompressionLevel = CompressionLevel.DEFAULT,
) -> bytes:
    """Compress a NumPy array.

    Args:
        array: The NumPy array to compress
        algorithm: The compression algorithm to use
        level: The compression level to apply

    Returns:
        The compressed array as bytes

    Raises:
        ValueError: If the array cannot be compressed
    """
    compressor = NumpyCompressor(
        algorithm=algorithm,
        level=level,
    )
    return compressor.compress(array)


def decompress_numpy(
    data: bytes,
    algorithm: CompressionAlgorithm = CompressionAlgorithm.GZIP,
    level: CompressionLevel = CompressionLevel.DEFAULT,
) -> np.ndarray:
    """Decompress a NumPy array.

    Args:
        data: The compressed array as bytes
        algorithm: The compression algorithm used
        level: The compression level applied

    Returns:
        The decompressed NumPy array

    Raises:
        ValueError: If the data cannot be decompressed
    """
    compressor = NumpyCompressor(
        algorithm=algorithm,
        level=level,
    )
    return compressor.decompress(data)


def optimize_dataset(
    dataset: List[Any],
    chunk_size: int = 1000,
    processor: Optional[Callable[[List[Any]], List[Any]]] = None,
    compress: bool = True,
    algorithm: CompressionAlgorithm = CompressionAlgorithm.GZIP,
    serialization: SerializationFormat = SerializationFormat.JSON,
    level: CompressionLevel = CompressionLevel.DEFAULT,
) -> Union[List[Any], CompressedData]:
    """Optimize a dataset by processing it in chunks and optionally compressing it.

    Args:
        dataset: The dataset to optimize
        chunk_size: The size of each chunk
        processor: A function to process each chunk
        compress: Whether to compress the result
        algorithm: The compression algorithm to use
        serialization: The serialization format to use
        level: The compression level to use

    Returns:
        The optimized dataset, either as a list or as compressed data
    """
    optimizer = DatasetOptimizer(
        compressor=DataCompressor(
            algorithm=algorithm,
            serialization=serialization,
            level=level,
        ),
        chunk_size=chunk_size,
    )

    if processor:
        result = optimizer.process_large_dataset(
            dataset=dataset,
            processor=processor,
            compress_result=compress,
        )
        return result
    elif compress:
        return optimizer.compress_dataset(dataset)
    else:
        return dataset
