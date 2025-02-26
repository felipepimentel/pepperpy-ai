"""Local storage provider implementation.

This module provides a local filesystem implementation of the storage provider interface.
It handles:
- Local file operations
- Directory management
- Metadata tracking
- Error handling
"""

import os
import shutil
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional, Union

import aiofiles
import aiofiles.os
import magic

from pepperpy.core.errors import ConfigurationError
from pepperpy.core.logging import get_logger
from pepperpy.providers.base import ProviderError
from pepperpy.providers.storage.base import (
    BaseStorageProvider,
    StorageConfig,
    StorageMetadata,
)

# Configure logging
logger = get_logger(__name__)

# Default chunk size for streaming (64KB)
DEFAULT_CHUNK_SIZE = 64 * 1024


class LocalStorageProvider(BaseStorageProvider):
    """Local filesystem storage provider implementation."""

    def __init__(self, config: StorageConfig) -> None:
        """Initialize local storage provider.

        Args:
            config: Storage configuration

        Raises:
            ConfigurationError: If configuration is invalid
        """
        super().__init__(config)
        if not self.root_path:
            raise ConfigurationError("Root path is required for local storage")
        self.root_path = Path(self.root_path).resolve()

    async def initialize(self) -> None:
        """Initialize the provider.

        This method creates the root directory if needed.

        Raises:
            ConfigurationError: If initialization fails
        """
        if self._initialized:
            return

        try:
            # Create root directory if needed
            if self.create_if_missing:
                os.makedirs(self.root_path, exist_ok=True)

            # Set permissions if specified
            if self.permissions is not None:
                os.chmod(self.root_path, self.permissions)

            self._initialized = True
            logger.info(
                "Local storage provider initialized",
                extra={"root_path": str(self.root_path)},
            )

        except Exception as e:
            raise ConfigurationError(f"Failed to initialize local storage: {e}")

    async def cleanup(self) -> None:
        """Clean up provider resources."""
        self._initialized = False
        logger.info("Local storage provider cleaned up")

    def _resolve_path(self, path: Union[str, Path]) -> Path:
        """Resolve path relative to root.

        Args:
            path: Path to resolve

        Returns:
            Absolute path

        Raises:
            ProviderError: If path is invalid or outside root
        """
        try:
            resolved = (self.root_path / Path(path)).resolve()
            if not str(resolved).startswith(str(self.root_path)):
                raise ProviderError("Path is outside root directory")
            return resolved
        except Exception as e:
            raise ProviderError(f"Invalid path: {e}")

    async def read(self, path: Union[str, Path]) -> bytes:
        """Read file contents.

        Args:
            path: File path

        Returns:
            File contents

        Raises:
            ProviderError: If read fails
        """
        if not self._initialized:
            raise ProviderError("Provider not initialized")

        try:
            resolved_path = self._resolve_path(path)
            async with aiofiles.open(resolved_path, "rb") as f:
                return await f.read()
        except Exception as e:
            raise ProviderError(f"Failed to read file: {e}")

    async def write(
        self,
        path: Union[str, Path],
        data: Union[str, bytes],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> StorageMetadata:
        """Write data to file.

        Args:
            path: File path
            data: Data to write
            metadata: Optional metadata

        Returns:
            File metadata

        Raises:
            ProviderError: If write fails
        """
        if not self._initialized:
            raise ProviderError("Provider not initialized")

        try:
            resolved_path = self._resolve_path(path)

            # Create parent directories if needed
            if self.create_if_missing:
                os.makedirs(resolved_path.parent, exist_ok=True)

            # Convert string to bytes if needed
            if isinstance(data, str):
                data = data.encode()

            # Write data
            async with aiofiles.open(resolved_path, "wb") as f:
                await f.write(data)

            # Set permissions if specified
            if self.permissions is not None:
                os.chmod(resolved_path, self.permissions)

            # Get metadata
            return await self.get_metadata(path)

        except Exception as e:
            raise ProviderError(f"Failed to write file: {e}")

    async def delete(self, path: Union[str, Path]) -> None:
        """Delete file or directory.

        Args:
            path: Path to delete

        Raises:
            ProviderError: If deletion fails
        """
        if not self._initialized:
            raise ProviderError("Provider not initialized")

        try:
            resolved_path = self._resolve_path(path)
            if resolved_path.is_dir():
                shutil.rmtree(resolved_path)
            else:
                os.remove(resolved_path)
        except Exception as e:
            raise ProviderError(f"Failed to delete path: {e}")

    async def exists(self, path: Union[str, Path]) -> bool:
        """Check if path exists.

        Args:
            path: Path to check

        Returns:
            True if path exists

        Raises:
            ProviderError: If check fails
        """
        if not self._initialized:
            raise ProviderError("Provider not initialized")

        try:
            resolved_path = self._resolve_path(path)
            return resolved_path.exists()
        except Exception as e:
            raise ProviderError(f"Failed to check path: {e}")

    async def list(
        self,
        path: Union[str, Path],
        recursive: bool = False,
        include_metadata: bool = False,
    ) -> Union[List[str], List[StorageMetadata]]:
        """List directory contents.

        Args:
            path: Directory path
            recursive: List recursively
            include_metadata: Include metadata

        Returns:
            List of paths or metadata

        Raises:
            ProviderError: If listing fails
        """
        if not self._initialized:
            raise ProviderError("Provider not initialized")

        try:
            resolved_path = self._resolve_path(path)
            if not resolved_path.is_dir():
                raise ProviderError("Path is not a directory")

            # Get paths
            if recursive:
                paths = [
                    p
                    for p in resolved_path.rglob("*")
                    if not any(part.startswith(".") for part in p.parts)
                ]
            else:
                paths = [
                    p for p in resolved_path.iterdir() if not p.name.startswith(".")
                ]

            # Convert to relative paths
            rel_paths = [str(p.relative_to(self.root_path)) for p in paths]

            # Return paths or metadata
            if include_metadata:
                return [await self.get_metadata(p) for p in rel_paths]
            return rel_paths

        except Exception as e:
            raise ProviderError(f"Failed to list directory: {e}")

    async def get_metadata(self, path: Union[str, Path]) -> StorageMetadata:
        """Get item metadata.

        Args:
            path: Item path

        Returns:
            Item metadata

        Raises:
            ProviderError: If metadata retrieval fails
        """
        if not self._initialized:
            raise ProviderError("Provider not initialized")

        try:
            resolved_path = self._resolve_path(path)
            if not resolved_path.exists():
                raise ProviderError("Path does not exist")

            # Get file stats
            stats = resolved_path.stat()

            # Get content type
            content_type = None
            if resolved_path.is_file():
                content_type = magic.from_file(str(resolved_path), mime=True)

            # Create metadata
            return StorageMetadata(
                path=str(Path(path)),
                size=stats.st_size,
                created_at=stats.st_ctime,
                modified_at=stats.st_mtime,
                content_type=content_type,
                metadata={},
            )

        except Exception as e:
            raise ProviderError(f"Failed to get metadata: {e}")

    async def update_metadata(
        self, path: Union[str, Path], metadata: Dict[str, Any]
    ) -> StorageMetadata:
        """Update item metadata.

        Args:
            path: Item path
            metadata: New metadata

        Returns:
            Updated metadata

        Raises:
            ProviderError: If update fails
        """
        if not self._initialized:
            raise ProviderError("Provider not initialized")

        try:
            # Get current metadata
            current = await self.get_metadata(path)

            # Update metadata
            current.metadata.update(metadata)
            return current

        except Exception as e:
            raise ProviderError(f"Failed to update metadata: {e}")

    async def stream(self, path: Union[str, Path]) -> AsyncIterator[bytes]:
        """Stream file contents.

        Args:
            path: File path

        Returns:
            Content stream

        Raises:
            ProviderError: If streaming fails
        """
        if not self._initialized:
            raise ProviderError("Provider not initialized")

        try:
            resolved_path = self._resolve_path(path)
            if not resolved_path.is_file():
                raise ProviderError("Path is not a file")

            async with aiofiles.open(resolved_path, "rb") as f:
                while chunk := await f.read(DEFAULT_CHUNK_SIZE):
                    yield chunk

        except Exception as e:
            raise ProviderError(f"Failed to stream file: {e}")
