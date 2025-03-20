#!/usr/bin/env python3
"""
Example demonstrating the PepperPy Storage module.
"""

import asyncio
import json
import os
import tempfile
import uuid
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class StorageType(str, Enum):
    """Types of storage supported by the storage module."""

    LOCAL = "local"
    S3 = "s3"
    GCS = "gcs"
    AZURE = "azure"
    VECTOR = "vector"


class StorageError(Exception):
    """Base class for storage-related errors."""

    pass


class StorageNotFoundError(StorageError):
    """Raised when a requested resource is not found."""

    pass


class StoragePermissionError(StorageError):
    """Raised when permission is denied for a storage operation."""

    pass


class StorageProvider(ABC):
    """Base class for storage providers."""

    def __init__(self, name: str, storage_type: StorageType) -> None:
        """Initialize a storage provider."""
        self.name = name
        self.id = str(uuid.uuid4())
        self.storage_type = storage_type

    @abstractmethod
    async def write(self, key: str, data: Union[str, bytes, Dict[str, Any]]) -> None:
        """Write data to storage."""
        pass

    @abstractmethod
    async def read(self, key: str) -> Union[str, bytes, Dict[str, Any]]:
        """Read data from storage."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete data from storage."""
        pass

    @abstractmethod
    async def list(self, prefix: str = "") -> List[str]:
        """List keys in storage with the given prefix."""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if a key exists in storage."""
        pass


class LocalStorageProvider(StorageProvider):
    """Provider for local file system storage."""

    def __init__(
        self,
        name: str,
        base_path: Optional[str] = None,
        create_if_missing: bool = True,
    ) -> None:
        """Initialize a local storage provider."""
        super().__init__(name, StorageType.LOCAL)

        if base_path:
            self.base_path = Path(base_path)
        else:
            # Create a temporary directory if no base path is provided
            self.base_path = Path(tempfile.mkdtemp())

        if create_if_missing and not self.base_path.exists():
            self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_path(self, key: str) -> Path:
        """Get the full path for a key."""
        return self.base_path / key

    async def write(self, key: str, data: Union[str, bytes, Dict[str, Any]]) -> None:
        """Write data to a file."""
        path = self._get_path(key)

        # Create parent directories if they don't exist
        path.parent.mkdir(parents=True, exist_ok=True)

        mode = "wb" if isinstance(data, bytes) else "w"

        if isinstance(data, dict):
            data = json.dumps(data)

        with open(path, mode) as f:
            f.write(data)

    async def read(self, key: str) -> Union[str, bytes, Dict[str, Any]]:
        """Read data from a file."""
        path = self._get_path(key)

        if not path.exists():
            raise StorageNotFoundError(f"Key not found: {key}")

        # Try to determine if it's JSON
        try:
            with open(path, "r") as f:
                content = f.read()
                # Try to parse as JSON
                return json.loads(content)
        except json.JSONDecodeError:
            # Not JSON, try as text
            try:
                with open(path, "r") as f:
                    return f.read()
            except UnicodeDecodeError:
                # Not text, read as binary
                with open(path, "rb") as f:
                    return f.read()

    async def delete(self, key: str) -> None:
        """Delete a file."""
        path = self._get_path(key)

        if not path.exists():
            raise StorageNotFoundError(f"Key not found: {key}")

        try:
            path.unlink()
        except PermissionError:
            raise StoragePermissionError(f"Permission denied to delete: {key}")

    async def list(self, prefix: str = "") -> List[str]:
        """List files with the given prefix."""
        prefix_path = self._get_path(prefix)

        if prefix and not prefix_path.parent.exists():
            return []

        if prefix and prefix_path.is_file():
            return [prefix]

        base_path_str = str(self.base_path)

        if prefix:
            # List files in the prefix directory and subdirectories
            result = []
            for root, _, files in os.walk(prefix_path):
                for file in files:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, base_path_str)
                    result.append(rel_path)
            return result
        else:
            # List all files in the base directory and subdirectories
            result = []
            for root, _, files in os.walk(self.base_path):
                for file in files:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, base_path_str)
                    result.append(rel_path)
            return result

    async def exists(self, key: str) -> bool:
        """Check if a file exists."""
        path = self._get_path(key)
        return path.exists()


class MockVectorStorageProvider(StorageProvider):
    """Mock provider for vector storage (for demonstration purposes)."""

    def __init__(self, name: str, dimension: int = 128) -> None:
        """Initialize a mock vector storage provider."""
        super().__init__(name, StorageType.VECTOR)
        self.dimension = dimension
        self.vectors: Dict[str, List[float]] = {}
        self.metadata: Dict[str, Dict[str, Any]] = {}

    async def write(self, key: str, data: Union[str, bytes, Dict[str, Any]]) -> None:
        """Write a vector to storage."""
        if not isinstance(data, dict):
            raise ValueError(
                "Vector storage requires a dictionary with 'vector' and optional 'metadata'"
            )

        vector = data.get("vector")
        metadata = data.get("metadata", {})

        if not vector or not isinstance(vector, list):
            raise ValueError("Vector must be a list of floats")

        if len(vector) != self.dimension:
            raise ValueError(f"Vector dimension must be {self.dimension}")

        self.vectors[key] = vector
        self.metadata[key] = metadata

    async def read(self, key: str) -> Dict[str, Any]:
        """Read a vector from storage."""
        if key not in self.vectors:
            raise StorageNotFoundError(f"Vector not found: {key}")

        return {
            "vector": self.vectors[key],
            "metadata": self.metadata.get(key, {}),
        }

    async def delete(self, key: str) -> None:
        """Delete a vector from storage."""
        if key not in self.vectors:
            raise StorageNotFoundError(f"Vector not found: {key}")

        del self.vectors[key]
        if key in self.metadata:
            del self.metadata[key]

    async def list(self, prefix: str = "") -> List[str]:
        """List vectors with the given prefix."""
        return [k for k in self.vectors.keys() if k.startswith(prefix)]

    async def exists(self, key: str) -> bool:
        """Check if a vector exists."""
        return key in self.vectors

    async def search(
        self, query_vector: List[float], top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors (mock implementation)."""
        if len(query_vector) != self.dimension:
            raise ValueError(f"Query vector dimension must be {self.dimension}")

        # In a real implementation, this would compute similarity scores
        # For demonstration, we'll just return random results
        results = []
        for key, vector in list(self.vectors.items())[:top_k]:
            # Mock similarity score between 0.5 and 0.9
            score = 0.5 + (hash(key) % 40) / 100
            results.append({
                "key": key,
                "score": score,
                "metadata": self.metadata.get(key, {}),
            })

        # Sort by score in descending order
        results.sort(key=lambda x: x["score"], reverse=True)
        return results


class StorageManager:
    """Manages storage providers."""

    def __init__(self) -> None:
        """Initialize a storage manager."""
        self.providers: Dict[str, StorageProvider] = {}

    def register_provider(self, provider: StorageProvider) -> None:
        """Register a storage provider."""
        self.providers[provider.name] = provider

    def get_provider(self, name: str) -> StorageProvider:
        """Get a storage provider by name."""
        if name not in self.providers:
            raise ValueError(f"Provider not found: {name}")

        return self.providers[name]

    def list_providers(self) -> List[Dict[str, Any]]:
        """List all registered providers."""
        return [
            {
                "name": provider.name,
                "id": provider.id,
                "type": provider.storage_type.value,
            }
            for provider in self.providers.values()
        ]


async def main() -> None:
    """Run the storage example."""
    print("PepperPy Storage Example")
    print("=======================")

    # Create a storage manager
    storage_manager = StorageManager()

    # Create and register storage providers
    local_provider = LocalStorageProvider(
        name="local-storage",
        base_path=tempfile.mkdtemp(),
    )
    storage_manager.register_provider(local_provider)

    vector_provider = MockVectorStorageProvider(
        name="vector-storage",
        dimension=3,  # Small dimension for demonstration
    )
    storage_manager.register_provider(vector_provider)

    # List registered providers
    print("\nRegistered Storage Providers:")
    for provider_info in storage_manager.list_providers():
        print(f"  - {provider_info['name']} ({provider_info['type']})")

    # Local storage example
    print("\nLocal Storage Example:")

    # Write different types of data
    print("  Writing data...")
    await local_provider.write("text.txt", "Hello, world!")
    await local_provider.write("data.json", {"name": "John", "age": 30})
    await local_provider.write("binary.bin", b"\x00\x01\x02\x03")

    # Create a nested directory structure
    await local_provider.write("nested/file1.txt", "Nested file 1")
    await local_provider.write("nested/file2.txt", "Nested file 2")
    await local_provider.write("nested/subdir/file3.txt", "Nested file 3")

    # List files
    print("  Listing files:")
    files = await local_provider.list()
    for file in files:
        print(f"    - {file}")

    # Read data
    print("\n  Reading data:")
    text_data = await local_provider.read("text.txt")
    print(f"    text.txt: {text_data}")

    json_data = await local_provider.read("data.json")
    print(f"    data.json: {json_data}")

    # Check if a file exists
    exists = await local_provider.exists("nonexistent.txt")
    print(f"\n  nonexistent.txt exists: {exists}")

    # Delete a file
    print("  Deleting nested/file1.txt")
    await local_provider.delete("nested/file1.txt")

    # List files again
    print("  Listing files after deletion:")
    files = await local_provider.list()
    for file in files:
        print(f"    - {file}")

    # Vector storage example
    print("\nVector Storage Example:")

    # Store vectors with metadata
    print("  Storing vectors...")
    await vector_provider.write(
        "vec1",
        {
            "vector": [0.1, 0.2, 0.3],
            "metadata": {"text": "This is a sample text", "category": "example"},
        },
    )

    await vector_provider.write(
        "vec2",
        {
            "vector": [0.4, 0.5, 0.6],
            "metadata": {"text": "Another example", "category": "sample"},
        },
    )

    await vector_provider.write(
        "vec3",
        {
            "vector": [0.7, 0.8, 0.9],
            "metadata": {"text": "Third vector", "category": "test"},
        },
    )

    # List vectors
    print("  Listing vectors:")
    vectors = await vector_provider.list()
    for vec in vectors:
        print(f"    - {vec}")

    # Read a vector
    print("\n  Reading vector:")
    vec_data = await vector_provider.read("vec1")
    print(f"    vec1: {vec_data}")

    # Search for similar vectors
    print("\n  Searching for similar vectors:")
    query_vector = [0.2, 0.3, 0.4]
    results = await vector_provider.search(query_vector, top_k=2)

    for i, result in enumerate(results):
        print(f"    {i + 1}. {result['key']} (Score: {result['score']:.2f})")
        print(f"       Metadata: {result['metadata']}")


if __name__ == "__main__":
    asyncio.run(main())
