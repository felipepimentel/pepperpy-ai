"""Local filesystem storage provider.

This module provides a local filesystem implementation of the storage provider interface.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional, Union

from ..base import StorageError, StorageObject, StorageProvider, StorageStats


class LocalStorageProvider(StorageProvider):
    """Local filesystem implementation of the storage provider interface."""

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the local storage provider.

        Args:
            config: Configuration dictionary with:
                - root_dir: Base directory for storage (required)
                - create_root: Create root directory if missing (default: True)
        """
        super().__init__(config=config)

        if not config or "root_dir" not in config:
            raise StorageError("root_dir is required in config")

        self.root_dir = Path(config["root_dir"])
        if config.get("create_root", True):
            self.root_dir.mkdir(parents=True, exist_ok=True)

    def _get_path(self, key: str) -> Path:
        """Get absolute path for a key."""
        path = self.root_dir / key
        if not path.is_relative_to(self.root_dir):
            raise StorageError(f"Invalid key path: {key}")
        return path

    async def read(
        self,
        key: str,
        **kwargs: Any,
    ) -> bytes:
        """Read object data from local file."""
        try:
            path = self._get_path(key)
            return path.read_bytes()
        except FileNotFoundError:
            raise StorageError(f"Object not found: {key}")
        except Exception as e:
            raise StorageError(f"Failed to read {key}: {e}")

    async def write(
        self,
        key: str,
        data: Union[str, bytes],
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> StorageObject:
        """Write object data to local file."""
        try:
            path = self._get_path(key)
            path.parent.mkdir(parents=True, exist_ok=True)

            if isinstance(data, str):
                data = data.encode("utf-8")

            path.write_bytes(data)
            stats = path.stat()

            return StorageObject(
                key=key,
                size=stats.st_size,
                last_modified=datetime.fromtimestamp(stats.st_mtime),
                metadata=metadata or {},
            )
        except Exception as e:
            raise StorageError(f"Failed to write {key}: {e}")

    async def delete(
        self,
        key: str,
        **kwargs: Any,
    ) -> None:
        """Delete local file."""
        try:
            path = self._get_path(key)
            if not path.exists():
                raise StorageError(f"Object not found: {key}")
            path.unlink()
        except StorageError:
            raise
        except Exception as e:
            raise StorageError(f"Failed to delete {key}: {e}")

    async def list(
        self,
        prefix: Optional[str] = None,
        **kwargs: Any,
    ) -> List[StorageObject]:
        """List files in local directory."""
        try:
            objects = []
            search_dir = self.root_dir
            if prefix:
                search_dir = self._get_path(prefix)
                if not search_dir.exists():
                    return []

            for path in search_dir.rglob("*"):
                if not path.is_file():
                    continue

                rel_path = str(path.relative_to(self.root_dir))
                if prefix and not rel_path.startswith(prefix):
                    continue

                stats = path.stat()
                objects.append(
                    StorageObject(
                        key=rel_path,
                        size=stats.st_size,
                        last_modified=datetime.fromtimestamp(stats.st_mtime),
                        metadata={},
                    )
                )
            return objects
        except Exception as e:
            raise StorageError(f"Failed to list objects: {e}")

    async def get_stats(self, **kwargs: Any) -> StorageStats:
        """Get storage statistics for local directory."""
        try:
            total_size = 0
            total_objects = 0

            for path in self.root_dir.rglob("*"):
                if path.is_file():
                    total_objects += 1
                    total_size += path.stat().st_size

            return StorageStats(
                total_objects=total_objects,
                total_size=total_size,
                last_updated=datetime.now(),
            )
        except Exception as e:
            raise StorageError(f"Failed to get stats: {e}")

    async def stream(
        self,
        key: str,
        chunk_size: int = 8192,
        **kwargs: Any,
    ) -> AsyncIterator[bytes]:
        """Stream local file in chunks."""
        try:
            path = self._get_path(key)
            if not path.exists():
                raise StorageError(f"Object not found: {key}")

            with path.open("rb") as f:
                while chunk := f.read(chunk_size):
                    yield chunk
        except StorageError:
            raise
        except Exception as e:
            raise StorageError(f"Failed to stream {key}: {e}")

    def get_capabilities(self) -> Dict[str, Any]:
        """Get local storage provider capabilities."""
        return {
            "max_size": None,  # Limited only by filesystem
            "supports_streaming": True,
            "supports_metadata": True,
            "persistent": True,
            "root_dir": str(self.root_dir),
        }
