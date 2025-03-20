"""Local filesystem storage provider implementation.

This module provides a local filesystem-based implementation of the storage
provider interface, supporting file operations with metadata.

Example:
    >>> from pepperpy.storage.providers.local import LocalStorageProvider
    >>> provider = LocalStorageProvider(base_path="/data")
    >>> await provider.write("file.txt", "Hello, World!")
    >>> content = await provider.read("file.txt")
    >>> print(content)
"""

import asyncio
import logging
import os
import stat
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional, Union

import aiofiles

from pepperpy.core.errors import NotFoundError
from pepperpy.storage.provider import (
    StorageError,
    StorageObject,
    StorageProvider,
    StorageStats,
)

logger = logging.getLogger(__name__)


class LocalStorageProvider(StorageProvider):
    """Local filesystem implementation of the storage provider interface."""

    name = "local"

    def __init__(
        self,
        base_path: Union[str, Path],
        create_path: bool = True,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize local storage provider.

        Args:
            base_path: Base directory for storage
            create_path: Whether to create base path if it doesn't exist
            config: Optional configuration dictionary

        Raises:
            StorageError: If base path is invalid or inaccessible
        """
        super().__init__(base_url="file://localhost", config=config)
        self.base_path = Path(base_path).resolve()
        self.create_path = create_path

    async def initialize(self) -> None:
        """Initialize storage provider.

        Creates base directory if it doesn't exist and validate permissions.

        Raises:
            StorageError: If initialization fails
        """
        try:
            if not self.base_path.exists():
                if self.create_path:
                    self.base_path.mkdir(parents=True, exist_ok=True)
                else:
                    raise StorageError(f"Base path does not exist: {self.base_path}")

            # Validate permissions
            if not os.access(self.base_path, os.R_OK | os.W_OK):
                raise StorageError(f"Insufficient permissions for base path: {self.base_path}")

        except Exception as e:
            if not isinstance(e, StorageError):
                raise StorageError(f"Failed to initialize local storage: {e}")
            raise

    def _resolve_path(self, key: str) -> Path:
        """Resolve storage key to filesystem path.

        Args:
            key: Storage key

        Returns:
            Resolved Path object

        Raises:
            StorageError: If path resolution fails or path is invalid
        """
        try:
            # Normalize key and resolve path
            key = os.path.normpath(key.lstrip("/"))
            path = (self.base_path / key).resolve()

            # Ensure path is within base path
            if not str(path).startswith(str(self.base_path)):
                raise StorageError(f"Invalid path: {path}")

            return path
        except Exception as e:
            if not isinstance(e, StorageError):
                raise StorageError(f"Failed to resolve path: {e}")
            raise

    def _create_storage_object(self, path: Path) -> StorageObject:
        """Create StorageObject from filesystem path.

        Args:
            path: Path to file

        Returns:
            StorageObject instance

        Raises:
            StorageError: If file stats cannot be retrieved
        """
        try:
            # Get file stats
            stats = path.stat()

            # Create relative key from base path
            key = str(path.relative_to(self.base_path))

            # Get basic file metadata
            metadata = {
                "mode": stat.filemode(stats.st_mode),
                "uid": stats.st_uid,
                "gid": stats.st_gid,
                "content_type": "application/octet-stream",
            }

            # Try to guess content type
            try:
                import mimetypes
                content_type, _ = mimetypes.guess_type(path)
                if content_type:
                    metadata["content_type"] = content_type
            except Exception:
                pass

            return StorageObject(
                key=key,
                size=stats.st_size,
                last_modified=datetime.fromtimestamp(stats.st_mtime),
                metadata=metadata,
            )
        except Exception as e:
            raise StorageError(f"Failed to create storage object: {e}")

    async def read(self, key: str, **kwargs: Any) -> bytes:
        """Read file contents.

        Args:
            key: File path relative to base path
            **kwargs: Additional options (ignored)

        Returns:
            File contents as bytes

        Raises:
            NotFoundError: If file does not exist
            StorageError: If read fails
        """
        path = self._resolve_path(key)
        if not path.is_file():
            raise NotFoundError(f"File not found: {key}")

        try:
            async with aiofiles.open(path, mode="rb") as f:
                return await f.read()
        except Exception as e:
            raise StorageError(f"Failed to read file: {e}")

    async def write(
        self,
        key: str,
        data: Union[str, bytes],
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> StorageObject:
        """Write file contents.

        Args:
            key: File path relative to base path
            data: File contents (string or bytes)
            metadata: Optional file metadata
            **kwargs: Additional options (ignored)

        Returns:
            StorageObject for written file

        Raises:
            StorageError: If write fails
        """
        path = self._resolve_path(key)

        try:
            # Create parent directories
            path.parent.mkdir(parents=True, exist_ok=True)

            # Convert string to bytes if needed
            if isinstance(data, str):
                data = data.encode("utf-8")

            # Write file
            async with aiofiles.open(path, mode="wb") as f:
                await f.write(data)

            # Set metadata if provided
            if metadata:
                # Set mode if provided
                if "mode" in metadata:
                    mode = int(metadata["mode"], 8)
                    os.chmod(path, mode)

                # Set ownership if provided
                if "uid" in metadata and "gid" in metadata:
                    os.chown(path, metadata["uid"], metadata["gid"])

            return self._create_storage_object(path)

        except Exception as e:
            raise StorageError(f"Failed to write file: {e}")

    async def delete(self, key: str, **kwargs: Any) -> None:
        """Delete a file.

        Args:
            key: File path relative to base path
            **kwargs: Additional options (ignored)

        Raises:
            NotFoundError: If file does not exist
            StorageError: If deletion fails
        """
        path = self._resolve_path(key)
        if not path.exists():
            raise NotFoundError(f"File not found: {key}")

        try:
            await asyncio.to_thread(os.remove, path)
        except Exception as e:
            raise StorageError(f"Failed to delete file: {e}")

    async def list(
        self,
        prefix: Optional[str] = None,
        **kwargs: Any,
    ) -> List[StorageObject]:
        """List files with optional prefix.

        Args:
            prefix: Optional path prefix to filter by
            **kwargs: Additional options (ignored)

        Returns:
            List of StorageObject instances

        Raises:
            StorageError: If listing fails
        """
        try:
            # Resolve prefix path
            base = self.base_path
            if prefix:
                base = self._resolve_path(prefix)
                if not base.exists():
                    return []

            # List files recursively
            objects = []
            for root, _, files in os.walk(base):
                for name in files:
                    path = Path(root) / name
                    try:
                        objects.append(self._create_storage_object(path))
                    except Exception as e:
                        logger.warning(f"Failed to process file {path}: {e}")

            return objects

        except Exception as e:
            if not isinstance(e, StorageError):
                raise StorageError(f"Failed to list files: {e}")
            raise

    async def get_stats(self, **kwargs: Any) -> StorageStats:
        """Get storage statistics.

        Args:
            **kwargs: Additional options (ignored)

        Returns:
            StorageStats instance

        Raises:
            StorageError: If stats retrieval fails
        """
        try:
            total_size = 0
            total_objects = 0

            # Walk directory tree
            for root, _, files in os.walk(self.base_path):
                for name in files:
                    try:
                        path = Path(root) / name
                        stats = path.stat()
                        total_size += stats.st_size
                        total_objects += 1
                    except Exception as e:
                        logger.warning(f"Failed to process file {name}: {e}")

            return StorageStats(
                total_objects=total_objects,
                total_size=total_size,
                last_updated=datetime.now(),
                metadata={
                    "base_path": str(self.base_path),
                    "fs_type": os.statvfs(self.base_path).f_fsid,
                },
            )

        except Exception as e:
            raise StorageError(f"Failed to get storage stats: {e}")

    async def stream(
        self,
        key: str,
        chunk_size: int = 8192,
        **kwargs: Any,
    ) -> AsyncIterator[bytes]:
        """Stream file contents in chunks.

        Args:
            key: File path relative to base path
            chunk_size: Size of chunks in bytes
            **kwargs: Additional options (ignored)

        Returns:
            AsyncIterator yielding data chunks

        Raises:
            NotFoundError: If file does not exist
            StorageError: If streaming fails
        """
        path = self._resolve_path(key)
        if not path.is_file():
            raise NotFoundError(f"File not found: {key}")

        try:
            async with aiofiles.open(path, mode="rb") as f:
                while True:
                    chunk = await f.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk
        except Exception as e:
            raise StorageError(f"Failed to stream file: {e}")

    def get_capabilities(self) -> Dict[str, Any]:
        """Get local storage provider capabilities."""
        capabilities = super().get_capabilities()
        capabilities.update({
            "max_size": None,  # Limited only by filesystem
            "supports_streaming": True,
            "supports_metadata": True,
            "supports_persistence": True,
            "base_path": str(self.base_path),
        })
        return capabilities
