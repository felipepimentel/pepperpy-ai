"""Storage provider interface for PepperPy.

This module provides the base classes and interfaces for storage providers,
supporting different storage backends like local filesystem, S3, etc.

Example:
    >>> from pepperpy.storage import StorageProvider
    >>> provider = StorageProvider.from_config({
    ...     "provider": "local",
    ...     "base_path": "/data"
    ... })
    >>> await provider.write("file.txt", "Hello, World!")
    >>> content = await provider.read("file.txt")
    >>> print(content)
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, AsyncIterator, Dict, List, Optional, Union

from pepperpy.core.errors import PepperpyError

logger = logging.getLogger(__name__)


@dataclass
class StorageObject:
    """Represents a stored object with metadata.

    Args:
        key: Object key/path
        size: Object size in bytes
        last_modified: Last modification timestamp
        metadata: Optional object metadata
            - content_type: MIME type
            - etag: Object hash/version
            - custom: Additional metadata fields

    Example:
        >>> obj = StorageObject(
        ...     key="data/file.txt",
        ...     size=1024,
        ...     last_modified=datetime.now(),
        ...     metadata={"content_type": "text/plain"}
        ... )
    """

    key: str
    size: int
    last_modified: datetime
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class StorageStats:
    """Storage statistics and usage information.

    Args:
        total_objects: Total number of objects
        total_size: Total size in bytes
        last_updated: Last update timestamp
        metadata: Optional additional statistics

    Example:
        >>> stats = StorageStats(
        ...     total_objects=100,
        ...     total_size=1024*1024,
        ...     last_updated=datetime.now()
        ... )
    """

    total_objects: int
    total_size: int
    last_updated: datetime
    metadata: Optional[Dict[str, Any]] = None


class StorageError(PepperpyError):
    """Base exception for storage-related errors."""

    pass


class StorageProvider(ABC):
    """Base class for storage providers."""

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize storage provider.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}

    @abstractmethod
    async def read(
        self,
        key: str,
        **kwargs: Any,
    ) -> bytes:
        """Read object data.

        Args:
            key: Object key/path
            **kwargs: Additional provider-specific arguments

        Returns:
            Object data as bytes

        Raises:
            NotFoundError: If object does not exist
            StorageError: If read fails
        """
        raise NotImplementedError

    @abstractmethod
    async def write(
        self,
        key: str,
        data: Union[str, bytes],
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> StorageObject:
        """Write object data.

        Args:
            key: Object key/path
            data: Object data (string or bytes)
            metadata: Optional object metadata
            **kwargs: Additional provider-specific arguments

        Returns:
            StorageObject with metadata

        Raises:
            StorageError: If write fails
        """
        raise NotImplementedError

    @abstractmethod
    async def delete(
        self,
        key: str,
        **kwargs: Any,
    ) -> None:
        """Delete an object.

        Args:
            key: Object key/path
            **kwargs: Additional provider-specific arguments

        Raises:
            NotFoundError: If object does not exist
            StorageError: If deletion fails
        """
        raise NotImplementedError

    @abstractmethod
    async def list(
        self,
        prefix: Optional[str] = None,
        **kwargs: Any,
    ) -> List[StorageObject]:
        """List objects with optional prefix.

        Args:
            prefix: Optional key prefix to filter by
            **kwargs: Additional provider-specific arguments

        Returns:
            List of StorageObject instances

        Raises:
            StorageError: If listing fails
        """
        raise NotImplementedError

    @abstractmethod
    async def get_stats(self, **kwargs: Any) -> StorageStats:
        """Get storage statistics.

        Args:
            **kwargs: Additional provider-specific arguments

        Returns:
            StorageStats instance

        Raises:
            StorageError: If stats retrieval fails
        """
        raise NotImplementedError

    @abstractmethod
    async def stream(
        self,
        key: str,
        chunk_size: int = 8192,
        **kwargs: Any,
    ) -> AsyncIterator[bytes]:
        """Stream object data in chunks.

        Args:
            key: Object key/path
            chunk_size: Size of chunks in bytes
            **kwargs: Additional provider-specific arguments

        Returns:
            AsyncIterator yielding data chunks

        Raises:
            NotFoundError: If object does not exist
            StorageError: If streaming fails
        """
        raise NotImplementedError

    def get_capabilities(self) -> Dict[str, Any]:
        """Get storage provider capabilities.

        Returns:
            Dictionary containing:
                - max_size: Maximum object size in bytes
                - supports_streaming: Whether streaming is supported
                - supports_metadata: Whether metadata is supported
                - additional provider-specific capabilities
        """
        return {
            "max_size": 0,
            "supports_streaming": False,
            "supports_metadata": False,
        }
