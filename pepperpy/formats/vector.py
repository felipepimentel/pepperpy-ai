"""Vector format handlers for the unified format handling system.

This module provides format handlers for vector data:
- NumpyFormat: NumPy array format
- JSONVectorFormat: JSON-based vector format
- BinaryVectorFormat: Binary vector format
- FaissIndexFormat: FAISS index format
"""

import json
import struct
from typing import Any, Dict, Optional, Tuple

try:
    import numpy as np

    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    import faiss

    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

from .base import FormatError, FormatHandler


class VectorData:
    """Container for vector data."""

    def __init__(
        self,
        vectors: Any,  # NDArray if numpy is available, else List[List[float]]
        dimensions: int,
        count: int,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize vector data.

        Args:
            vectors: Vector data (numpy array or list of lists)
            dimensions: Number of dimensions per vector
            count: Number of vectors
            metadata: Optional metadata

        """
        self.vectors = vectors
        self.dimensions = dimensions
        self.count = count
        self.metadata = metadata or {}

    @property
    def shape(self) -> Tuple[int, int]:
        """Get vector data shape (count, dimensions).

        Returns:
            Tuple of (count, dimensions)

        """
        return (self.count, self.dimensions)


class NumpyFormat(FormatHandler[VectorData]):
    """Handler for NumPy array format."""

    @property
    def mime_type(self) -> str:
        """Get the MIME type for this format.

        Returns:
            MIME type string

        """
        return "application/x-numpy-array"

    @property
    def file_extensions(self) -> list[str]:
        """Get the file extensions for this format.

        Returns:
            List of file extensions (without dot)

        """
        return ["npy"]

    def serialize(self, data: VectorData) -> bytes:
        """Serialize VectorData to NumPy bytes.

        Args:
            data: VectorData to serialize

        Returns:
            Serialized data as bytes

        Raises:
            FormatError: If serialization fails or NumPy is not available

        """
        if not NUMPY_AVAILABLE:
            raise FormatError("NumPy is required for NumpyFormat")

        try:
            # Convert to numpy array if not already
            if isinstance(data.vectors, np.ndarray):
                array = data.vectors
            else:
                array = np.array(data.vectors, dtype=np.float32)

            # Use numpy's save function to a bytes buffer
            import io

            buffer = io.BytesIO()
            np.save(buffer, array)
            return buffer.getvalue()
        except Exception as e:
            raise FormatError(f"Failed to serialize NumPy array: {e!s}") from e

    def deserialize(self, data: bytes) -> VectorData:
        """Deserialize bytes to VectorData.

        Args:
            data: Bytes to deserialize

        Returns:
            Deserialized VectorData

        Raises:
            FormatError: If deserialization fails or NumPy is not available

        """
        if not NUMPY_AVAILABLE:
            raise FormatError("NumPy is required for NumpyFormat")

        try:
            import io

            buffer = io.BytesIO(data)
            array = np.load(buffer)

            # Ensure it's a 2D array
            if array.ndim == 1:
                array = array.reshape(1, -1)
            elif array.ndim > 2:
                raise FormatError(f"Expected 1D or 2D array, got {array.ndim}D")

            return VectorData(
                vectors=array,
                dimensions=array.shape[1],
                count=array.shape[0],
                metadata={"format": "numpy"},
            )
        except Exception as e:
            if not isinstance(e, FormatError):
                e = FormatError(f"Failed to deserialize NumPy array: {e!s}")
            raise e


class JSONVectorFormat(FormatHandler[VectorData]):
    """Handler for JSON-based vector format."""

    @property
    def mime_type(self) -> str:
        """Get the MIME type for this format.

        Returns:
            MIME type string

        """
        return "application/json"

    @property
    def file_extensions(self) -> list[str]:
        """Get the file extensions for this format.

        Returns:
            List of file extensions (without dot)

        """
        return ["json"]

    def serialize(self, data: VectorData) -> bytes:
        """Serialize VectorData to JSON bytes.

        Args:
            data: VectorData to serialize

        Returns:
            Serialized data as bytes

        Raises:
            FormatError: If serialization fails

        """
        try:
            # Convert numpy array to list if needed
            if NUMPY_AVAILABLE and isinstance(data.vectors, np.ndarray):
                vectors = data.vectors.tolist()
            else:
                vectors = data.vectors

            # Create JSON structure
            json_data = {
                "vectors": vectors,
                "dimensions": data.dimensions,
                "count": data.count,
                "metadata": data.metadata,
            }

            # Serialize to JSON bytes
            return json.dumps(json_data).encode("utf-8")
        except Exception as e:
            raise FormatError(f"Failed to serialize to JSON: {e!s}") from e

    def deserialize(self, data: bytes) -> VectorData:
        """Deserialize bytes to VectorData.

        Args:
            data: Bytes to deserialize

        Returns:
            Deserialized VectorData

        Raises:
            FormatError: If deserialization fails

        """
        try:
            # Parse JSON
            json_data = json.loads(data.decode("utf-8"))

            # Extract fields
            vectors = json_data.get("vectors", [])
            dimensions = json_data.get("dimensions", len(vectors[0]) if vectors else 0)
            count = json_data.get("count", len(vectors) if vectors else 0)
            metadata = json_data.get("metadata", {})

            # Convert to numpy if available
            if NUMPY_AVAILABLE:
                vectors = np.array(vectors, dtype=np.float32)

            return VectorData(
                vectors=vectors,
                dimensions=dimensions,
                count=count,
                metadata=metadata,
            )
        except Exception as e:
            raise FormatError(f"Failed to deserialize from JSON: {e!s}") from e


class BinaryVectorFormat(FormatHandler[VectorData]):
    """Handler for binary vector format.

    Format specification:
    - 4 bytes: Magic number (0x56454354)
    - 4 bytes: Format version (uint32)
    - 4 bytes: Number of vectors (uint32)
    - 4 bytes: Dimensions per vector (uint32)
    - 4 bytes: Data type (0=float32, 1=float64, 2=int32, 3=int64)
    - 4 bytes: Metadata length (uint32)
    - N bytes: Metadata (JSON encoded)
    - M bytes: Vector data (binary encoded based on data type)
    """

    MAGIC = 0x56454354  # "VECT" in ASCII hex
    VERSION = 1

    @property
    def mime_type(self) -> str:
        """Get the MIME type for this format.

        Returns:
            MIME type string

        """
        return "application/x-binary-vector"

    @property
    def file_extensions(self) -> list[str]:
        """Get the file extensions for this format.

        Returns:
            List of file extensions (without dot)

        """
        return ["bvec"]

    def serialize(self, data: VectorData) -> bytes:
        """Serialize VectorData to binary format.

        Args:
            data: VectorData to serialize

        Returns:
            Serialized data as bytes

        Raises:
            FormatError: If serialization fails

        """
        try:
            # Determine data type and convert if needed
            if NUMPY_AVAILABLE and isinstance(data.vectors, np.ndarray):
                vectors = data.vectors
                if vectors.dtype == np.float32:
                    data_type = 0
                elif vectors.dtype == np.float64:
                    data_type = 1
                elif vectors.dtype == np.int32:
                    data_type = 2
                elif vectors.dtype == np.int64:
                    data_type = 3
                else:
                    # Convert to float32 by default
                    vectors = vectors.astype(np.float32)
                    data_type = 0

                # Get binary data
                vector_data = vectors.tobytes()
            else:
                # Convert list to float32 binary data
                if NUMPY_AVAILABLE:
                    vectors = np.array(data.vectors, dtype=np.float32)
                    vector_data = vectors.tobytes()
                else:
                    # Manual conversion to float32 binary
                    vector_data = bytearray()
                    for vector in data.vectors:
                        for value in vector:
                            vector_data.extend(struct.pack("f", float(value)))
                data_type = 0  # float32

            # Serialize metadata to JSON
            metadata_json = json.dumps(data.metadata).encode("utf-8")
            metadata_length = len(metadata_json)

            # Create header
            header = struct.pack(
                ">IIIIII",  # big-endian format
                self.MAGIC,
                self.VERSION,
                data.count,
                data.dimensions,
                data_type,
                metadata_length,
            )

            # Combine all parts
            return header + metadata_json + vector_data
        except Exception as e:
            raise FormatError(f"Failed to serialize to binary format: {e!s}") from e

    def deserialize(self, data: bytes) -> VectorData:
        """Deserialize bytes to VectorData.

        Args:
            data: Bytes to deserialize

        Returns:
            Deserialized VectorData

        Raises:
            FormatError: If deserialization fails

        """
        try:
            # Check minimum length
            if len(data) < 24:  # Header size
                raise FormatError("Invalid binary vector data: too short")

            # Parse header
            magic, version, count, dimensions, data_type, metadata_length = (
                struct.unpack(
                    ">IIIIII",  # big-endian format
                    data[:24],
                )
            )

            # Validate magic number
            if magic != self.MAGIC:
                raise FormatError("Invalid binary vector data: incorrect magic number")

            # Check version
            if version > self.VERSION:
                raise FormatError(
                    f"Unsupported binary vector format version: {version}",
                )

            # Parse metadata
            metadata_start = 24
            metadata_end = metadata_start + metadata_length
            if metadata_end > len(data):
                raise FormatError(
                    "Invalid binary vector data: metadata length exceeds data size",
                )

            metadata_json = data[metadata_start:metadata_end]
            metadata = json.loads(metadata_json.decode("utf-8"))

            # Parse vector data
            vector_data = data[metadata_end:]

            # Determine data type
            dtype_map = {0: np.float32, 1: np.float64, 2: np.int32, 3: np.int64}

            if NUMPY_AVAILABLE:
                dtype = dtype_map.get(data_type, np.float32)
                vectors = np.frombuffer(vector_data, dtype=dtype)
                vectors = vectors.reshape(count, dimensions)
            else:
                # Manual parsing based on data type
                item_size = {
                    0: 4,  # float32
                    1: 8,  # float64
                    2: 4,  # int32
                    3: 8,  # int64
                }[data_type]

                expected_size = count * dimensions * item_size
                if len(vector_data) != expected_size:
                    raise FormatError(
                        f"Invalid binary vector data: expected {expected_size} bytes, got {len(vector_data)}",
                    )

                # Parse as list of lists
                vectors = []
                for i in range(count):
                    vector = []
                    for j in range(dimensions):
                        offset = (i * dimensions + j) * item_size
                        if data_type == 0:  # float32
                            value = struct.unpack(
                                "f",
                                vector_data[offset : offset + 4],
                            )[0]
                        elif data_type == 1:  # float64
                            value = struct.unpack(
                                "d",
                                vector_data[offset : offset + 8],
                            )[0]
                        elif data_type == 2:  # int32
                            value = struct.unpack(
                                "i",
                                vector_data[offset : offset + 4],
                            )[0]
                        elif data_type == 3:  # int64
                            value = struct.unpack(
                                "q",
                                vector_data[offset : offset + 8],
                            )[0]
                        vector.append(value)
                    vectors.append(vector)

            return VectorData(
                vectors=vectors,
                dimensions=dimensions,
                count=count,
                metadata=metadata,
            )
        except Exception as e:
            if not isinstance(e, FormatError):
                e = FormatError(f"Failed to deserialize from binary format: {e!s}")
            raise e


class FaissIndexFormat(FormatHandler[VectorData]):
    """Handler for FAISS index format."""

    @property
    def mime_type(self) -> str:
        """Get the MIME type for this format.

        Returns:
            MIME type string

        """
        return "application/x-faiss-index"

    @property
    def file_extensions(self) -> list[str]:
        """Get the file extensions for this format.

        Returns:
            List of file extensions (without dot)

        """
        return ["faiss"]

    def serialize(self, data: VectorData) -> bytes:
        """Serialize VectorData to FAISS index bytes.

        Args:
            data: VectorData to serialize

        Returns:
            Serialized data as bytes

        Raises:
            FormatError: If serialization fails or FAISS is not available

        """
        if not FAISS_AVAILABLE:
            raise FormatError("FAISS is required for FaissIndexFormat")

        if not NUMPY_AVAILABLE:
            raise FormatError("NumPy is required for FaissIndexFormat")

        try:
            # Convert to numpy array if not already
            if isinstance(data.vectors, np.ndarray):
                vectors = data.vectors
            else:
                vectors = np.array(data.vectors, dtype=np.float32)

            # Ensure correct data type
            if vectors.dtype != np.float32:
                vectors = vectors.astype(np.float32)

            # Create a FAISS index
            index = faiss.IndexFlatL2(data.dimensions)
            index.add(vectors)

            # Serialize the index
            import io

            buffer = io.BytesIO()
            faiss.write_index(
                index,
                faiss.PyCallbackIOWriter(lambda x: buffer.write(x)),
            )
            return buffer.getvalue()
        except Exception as e:
            raise FormatError(f"Failed to serialize FAISS index: {e!s}") from e

    def deserialize(self, data: bytes) -> VectorData:
        """Deserialize bytes to VectorData.

        Args:
            data: Bytes to deserialize

        Returns:
            Deserialized VectorData

        Raises:
            FormatError: If deserialization fails or FAISS is not available

        """
        if not FAISS_AVAILABLE:
            raise FormatError("FAISS is required for FaissIndexFormat")

        if not NUMPY_AVAILABLE:
            raise FormatError("NumPy is required for FaissIndexFormat")

        try:
            # Load the FAISS index
            import io

            buffer = io.BytesIO(data)
            index = faiss.read_index(
                faiss.PyCallbackIOReader(lambda size: buffer.read(size)),
            )

            # Extract dimensions
            dimensions = index.d

            # For flat indexes, we can extract the vectors
            if isinstance(index, faiss.IndexFlat):
                vectors = faiss.vector_to_array(index.xb).reshape(-1, dimensions)
                count = index.ntotal
            else:
                # For other index types, we can't easily extract the vectors
                # Return empty vectors with correct dimensions
                vectors = np.zeros((0, dimensions), dtype=np.float32)
                count = index.ntotal

            return VectorData(
                vectors=vectors,
                dimensions=dimensions,
                count=count,
                metadata={"format": "faiss", "index_type": type(index).__name__},
            )
        except Exception as e:
            if not isinstance(e, FormatError):
                e = FormatError(f"Failed to deserialize FAISS index: {e!s}")
            raise e


class VectorProcessor:
    """Processor for vector data.

    This class provides methods for processing vector data, including:
    - Loading vectors from files
    - Saving vectors to files
    - Converting between formats
    - Basic vector operations
    """

    def __init__(self) -> None:
        """Initialize the vector processor."""
        self.formats = {
            "numpy": NumpyFormat(),
            "json": JSONVectorFormat(),
            "binary": BinaryVectorFormat(),
            "faiss": FaissIndexFormat(),
        }

    def load_file(self, file_path: str) -> VectorData:
        """Load vector data from a file.

        Args:
            file_path: Path to the vector file

        Returns:
            VectorData object

        Raises:
            FormatError: If the file format is not supported or loading fails
        """
        extension = file_path.split(".")[-1].lower()
        if extension not in self.get_supported_extensions():
            raise FormatError(f"Unsupported vector format: {extension}")

        format_handler = self._get_format_for_extension(extension)
        with open(file_path, "rb") as f:
            data = f.read()

        return format_handler.deserialize(data)

    def save_file(self, vector_data: VectorData, file_path: str) -> None:
        """Save vector data to a file.

        Args:
            vector_data: VectorData object
            file_path: Path to save the vector file

        Raises:
            FormatError: If the file format is not supported or saving fails
        """
        extension = file_path.split(".")[-1].lower()
        if extension not in self.get_supported_extensions():
            raise FormatError(f"Unsupported vector format: {extension}")

        format_handler = self._get_format_for_extension(extension)
        data = format_handler.serialize(vector_data)

        with open(file_path, "wb") as f:
            f.write(data)

    def convert_format(self, vector_data: VectorData, target_format: str) -> bytes:
        """Convert vector data to a different format.

        Args:
            vector_data: VectorData object
            target_format: Target format extension (e.g., 'npy', 'json')

        Returns:
            Serialized vector data in the target format

        Raises:
            FormatError: If the target format is not supported
        """
        if target_format not in self.get_supported_extensions():
            raise FormatError(f"Unsupported target format: {target_format}")

        format_handler = self._get_format_for_extension(target_format)
        return format_handler.serialize(vector_data)

    def create_vector_data(
        self,
        vectors: Any,
        dimensions: Optional[int] = None,
        count: Optional[int] = None,
    ) -> VectorData:
        """Create a VectorData object from raw vectors.

        Args:
            vectors: Vector data (numpy array or list of lists)
            dimensions: Number of dimensions per vector (optional, inferred if not provided)
            count: Number of vectors (optional, inferred if not provided)

        Returns:
            VectorData object

        Raises:
            FormatError: If the vector data is invalid
        """
        # Infer dimensions and count if not provided
        if NUMPY_AVAILABLE and isinstance(vectors, np.ndarray):
            if vectors.ndim == 1:
                inferred_count = 1
                inferred_dimensions = vectors.shape[0]
                # Reshape to 2D for consistency
                vectors = vectors.reshape(1, -1)
            else:
                inferred_count = vectors.shape[0]
                inferred_dimensions = vectors.shape[1]
        elif isinstance(vectors, list):
            inferred_count = len(vectors)
            if inferred_count > 0 and isinstance(vectors[0], list):
                inferred_dimensions = len(vectors[0])
            else:
                inferred_dimensions = 1
                # Reshape to 2D for consistency
                vectors = [[v] for v in vectors]
        else:
            raise FormatError("Unsupported vector data type")

        # Use provided values or inferred ones
        final_dimensions = dimensions or inferred_dimensions
        final_count = count or inferred_count

        return VectorData(
            vectors=vectors,
            dimensions=final_dimensions,
            count=final_count,
        )

    def get_supported_formats(self) -> Dict[str, FormatHandler]:
        """Get all supported vector formats.

        Returns:
            Dictionary of format handlers
        """
        return self.formats

    def get_supported_extensions(self) -> list[str]:
        """Get all supported file extensions.

        Returns:
            List of supported file extensions
        """
        extensions = []
        for format_handler in self.formats.values():
            extensions.extend(format_handler.file_extensions)
        return extensions

    def _get_format_for_extension(self, extension: str) -> FormatHandler:
        """Get the format handler for a file extension.

        Args:
            extension: File extension

        Returns:
            Format handler

        Raises:
            FormatError: If no handler is found for the extension
        """
        for format_name, format_handler in self.formats.items():
            if extension in format_handler.file_extensions:
                return format_handler

        raise FormatError(f"No handler found for extension: {extension}")
