"""Mock storage provider for testing.

This module provides a simple mock implementation of the storage provider interface
for testing purposes.
"""

from datetime import datetime
from typing import Any, AsyncIterator, Dict, List, Optional, Union

from pepperpy.storage import StorageError, StorageObject, StorageProvider, StorageStats


class MockStorageProvider(StorageProvider):
    """Mock implementation of the storage provider interface."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the mock storage provider."""
        super().__init__(config=config)
        self.storage: Dict[str, bytes] = {}

    async def read(
        self,
        key: str,
        **kwargs: Any,
    ) -> bytes:
        """Read object data."""
        if key not in self.storage:
            raise StorageError(f"Object not found: {key}")
        return self.storage[key]

    async def write(
        self,
        key: str,
        data: Union[str, bytes],
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> StorageObject:
        """Write object data."""
        if isinstance(data, str):
            data = data.encode("utf-8")
        self.storage[key] = data
        return StorageObject(
            key=key,
            size=len(data),
            last_modified=datetime.now(),
            metadata=metadata or {},
        )

    async def delete(
        self,
        key: str,
        **kwargs: Any,
    ) -> None:
        """Delete an object."""
        if key not in self.storage:
            raise StorageError(f"Object not found: {key}")
        del self.storage[key]

    async def list(
        self,
        prefix: Optional[str] = None,
        **kwargs: Any,
    ) -> List[StorageObject]:
        """List objects with optional prefix."""
        objects = []
        for key, data in self.storage.items():
            if prefix and not key.startswith(prefix):
                continue
            objects.append(
                StorageObject(
                    key=key,
                    size=len(data),
                    last_modified=datetime.now(),
                    metadata={},
                )
            )
        return objects

    async def get_stats(self, **kwargs: Any) -> StorageStats:
        """Get storage statistics."""
        total_size = sum(len(data) for data in self.storage.values())
        return StorageStats(
            total_objects=len(self.storage),
            total_size=total_size,
            last_updated=datetime.now(),
        )

    async def stream(
        self,
        key: str,
        chunk_size: int = 8192,
        **kwargs: Any,
    ) -> AsyncIterator[bytes]:
        """Stream object data in chunks."""
        if key not in self.storage:
            raise StorageError(f"Object not found: {key}")
        data = self.storage[key]
        for i in range(0, len(data), chunk_size):
            yield data[i : i + chunk_size]

    def get_capabilities(self) -> Dict[str, Any]:
        """Get storage provider capabilities."""
        return {
            "max_size": 1024 * 1024 * 1024,  # 1GB
            "supports_streaming": True,
            "supports_metadata": True,
        }
