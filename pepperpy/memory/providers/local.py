"""Local file-based provider for memory capability."""

import fnmatch
import json
import pickle
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from pepperpy.memory.base import BaseMemoryProvider, MemoryItem


class LocalConfig(BaseModel):
    """Configuration for local memory provider."""

    path: Path = Field(
        default=Path.home() / ".pepperpy" / "memory",
        description="Base directory for storing memory items.",
    )
    format: str = Field(default="json", description="Storage format (json or pickle).")


class LocalProvider(BaseMemoryProvider):
    """Local file-based implementation of memory provider."""

    def __init__(self, **config: Any):
        """Initialize provider with configuration.

        Args:
            **config: Configuration parameters
        """
        self.config = LocalConfig(**config)
        self.config.path.mkdir(parents=True, exist_ok=True)

    def _get_path(self, key: str) -> Path:
        """Get file path for a key.

        Args:
            key: Memory item key

        Returns:
            Path to storage file
        """
        # Sanitize key for filesystem
        safe_key = "".join(c if c.isalnum() else "_" for c in key)
        return self.config.path / f"{safe_key}.{self.config.format}"

    def _serialize(self, item: MemoryItem[Any]) -> bytes:
        """Serialize memory item to bytes.

        Args:
            item: Memory item to serialize

        Returns:
            Serialized data
        """
        if self.config.format == "json":
            data = {
                "key": item.key,
                "value": item.value,
                "created_at": item.created_at.isoformat(),
                "metadata": item.metadata,
                "ttl": item.ttl,
            }
            return json.dumps(data).encode()
        else:
            return pickle.dumps(item)

    def _deserialize(self, key: str, data: bytes) -> MemoryItem[Any]:
        """Deserialize memory item from bytes.

        Args:
            key: Item key
            data: Serialized data

        Returns:
            Deserialized memory item
        """
        if self.config.format == "json":
            data_dict = json.loads(data.decode())
            return MemoryItem(
                key=data_dict["key"],
                value=data_dict["value"],
                created_at=datetime.fromisoformat(data_dict["created_at"]),
                metadata=data_dict["metadata"],
                ttl=data_dict["ttl"],
            )
        else:
            return pickle.loads(data)

    async def get(
        self, key: str, *, default: Optional[Any] = None, **kwargs: Any
    ) -> Optional[Any]:
        """Retrieve a value from memory.

        Args:
            key: Key to retrieve
            default: Value to return if key not found
            **kwargs: Additional provider-specific parameters

        Returns:
            Retrieved value or default
        """
        path = self._get_path(key)

        if not path.exists():
            return default

        try:
            with open(path, "rb") as f:
                item = self._deserialize(key, f.read())

            # Check TTL
            if item.ttl is not None:
                age = (datetime.now() - item.created_at).total_seconds()
                if age > item.ttl:
                    await self.delete(key)
                    return default

            return item.value

        except (IOError, json.JSONDecodeError, pickle.UnpicklingError):
            return default

    async def set(
        self,
        key: str,
        value: Any,
        *,
        ttl: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Store a value in memory.

        Args:
            key: Key to store value under
            value: Value to store
            ttl: Time-to-live in seconds
            metadata: Additional metadata to store
            **kwargs: Additional provider-specific parameters
        """
        item = MemoryItem(
            key=key, value=value, created_at=datetime.now(), metadata=metadata, ttl=ttl
        )

        path = self._get_path(key)
        with open(path, "wb") as f:
            f.write(self._serialize(item))

    async def delete(self, key: str, **kwargs: Any) -> bool:
        """Delete a value from memory.

        Args:
            key: Key to delete
            **kwargs: Additional provider-specific parameters

        Returns:
            True if key was deleted, False if not found
        """
        path = self._get_path(key)

        if not path.exists():
            return False

        try:
            path.unlink()
            return True
        except IOError:
            return False

    async def search(
        self, pattern: str, *, limit: Optional[int] = None, **kwargs: Any
    ) -> List[str]:
        """Search for keys matching pattern.

        Args:
            pattern: Pattern to match against keys
            limit: Maximum number of keys to return
            **kwargs: Additional provider-specific parameters

        Returns:
            List of matching keys
        """
        # List all files
        files = list(self.config.path.glob(f"*.{self.config.format}"))

        # Extract and filter keys
        keys = []
        for file in files:
            key = file.stem
            if fnmatch.fnmatch(key, pattern):
                keys.append(key)

        # Sort and limit
        keys.sort()
        if limit:
            keys = keys[:limit]

        return keys

    async def clear(self, **kwargs: Any) -> None:
        """Clear all values from memory.

        Args:
            **kwargs: Additional provider-specific parameters
        """
        for file in self.config.path.glob(f"*.{self.config.format}"):
            try:
                file.unlink()
            except IOError:
                continue
