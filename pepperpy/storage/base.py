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
from typing import Any, AsyncIterator, Dict, List, Optional, Sequence

from pepperpy.core import PepperpyError
from pepperpy.core.base import BaseProvider

logger = logging.getLogger(__name__)


class StorageError(PepperpyError):
    """Base class for storage errors."""

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize a storage error.

        Args:
            message: Error message
            provider: Optional provider name
            operation: Optional operation name
            **kwargs: Additional error context
        """
        super().__init__(message, **kwargs)
        self.provider = provider
        self.operation = operation

    def __str__(self) -> str:
        """Get string representation of the error.

        Returns:
            Error message with provider and operation if available
        """
        parts = [self.message]
        if self.provider:
            parts.append(f"Provider: {self.provider}")
        if self.operation:
            parts.append(f"Operation: {self.operation}")
        return " | ".join(parts)


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


class StorageProvider(BaseProvider, ABC):
    """Base class for storage providers.

    This class defines the interface that all storage providers must implement.
    It provides methods for storing and retrieving vectors with metadata.
    """

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize storage provider.

        Args:
            config: Optional configuration dictionary
        """
        super().__init__(config)

    @abstractmethod
    async def store_vectors(
        self,
        vectors: Sequence[List[float]],
        metadata: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> List[str]:
        """Store vectors with optional metadata.

        Args:
            vectors: List of vectors to store
            metadata: Optional list of metadata for each vector
            **kwargs: Additional provider-specific arguments

        Returns:
            List of IDs for stored vectors

        Raises:
            StorageError: If storing vectors fails
        """
        pass

    @abstractmethod
    async def retrieve_vectors(
        self,
        vector_ids: List[str],
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """Retrieve vectors by ID.

        Args:
            vector_ids: List of vector IDs to retrieve
            **kwargs: Additional provider-specific arguments

        Returns:
            List of dictionaries containing vectors and metadata

        Raises:
            StorageError: If retrieving vectors fails
        """
        pass

    @abstractmethod
    async def delete_vectors(
        self,
        vector_ids: List[str],
        **kwargs: Any,
    ) -> None:
        """Delete vectors by ID.

        Args:
            vector_ids: List of vector IDs to delete
            **kwargs: Additional provider-specific arguments

        Raises:
            StorageError: If deleting vectors fails
        """
        pass

    @abstractmethod
    async def search_vectors(
        self,
        query_vector: List[float],
        limit: int = 10,
        filter: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors.

        Args:
            query_vector: Vector to search for
            limit: Maximum number of results to return
            filter: Optional metadata filter
            **kwargs: Additional provider-specific arguments

        Returns:
            List of dictionaries containing vectors, metadata, and scores

        Raises:
            StorageError: If searching vectors fails
        """
        pass

    @abstractmethod
    async def list_vectors(
        self,
        limit: int = 100,
        offset: int = 0,
        filter: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """List stored vectors.

        Args:
            limit: Maximum number of results to return
            offset: Number of results to skip
            filter: Optional metadata filter
            **kwargs: Additional provider-specific arguments

        Returns:
            List of dictionaries containing vectors and metadata

        Raises:
            StorageError: If listing vectors fails
        """
        pass

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
        data: Any,
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
