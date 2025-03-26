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

import json
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional, Sequence, Union

from pepperpy.core.base import BaseProvider
from pepperpy.core.config import Config
from pepperpy.core.errors import PepperpyError
from pepperpy.core.types import Document

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
        name: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize storage provider.

        Args:
            name: Provider name
            config: Optional configuration dictionary
        """
        super().__init__(name=name, config=config)

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

    async def save_json(
        self,
        filename: str,
        data: Any,
        base_dir: Optional[str] = None,
        indent: int = 2,
        **kwargs: Any,
    ) -> Path:
        """Save JSON data to file.

        Args:
            filename: Target filename
            data: Data to save
            base_dir: Optional base directory
            indent: JSON indentation level
            **kwargs: Additional provider options

        Returns:
            Path to saved file

        Raises:
            StorageError: If save fails
        """
        if not base_dir:
            base_dir = ".pepperpy/storage"

        path = Path(base_dir) / filename
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent)

        return path

    async def load_json(
        self,
        filename: str,
        base_dir: Optional[str] = None,
        **kwargs: Any,
    ) -> Any:
        """Load JSON data from file.

        Args:
            filename: Source filename
            base_dir: Optional base directory
            **kwargs: Additional provider options

        Returns:
            Loaded data

        Raises:
            StorageError: If load fails
        """
        if not base_dir:
            base_dir = ".pepperpy/storage"

        path = Path(base_dir) / filename

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    async def store_as_document(
        self,
        filename: str,
        data: Any,
        collection_name: str = "default",
        provider_type: str = "annoy",
        **kwargs: Any,
    ) -> None:
        """Save data as document and add to RAG.

        Args:
            filename: Target filename
            data: Data to save
            collection_name: RAG collection name
            provider_type: RAG provider type
            **kwargs: Additional provider options

        Raises:
            StorageError: If operation fails
        """
        # Save file
        path = await self.save_json(filename, data)

        # Add to RAG
        doc = Document(
            text=json.dumps(data) if isinstance(data, (dict, list)) else str(data),
            metadata={"source": str(path)},
        )
        await self.rag.add([doc])

    async def store_structured_document(
        self,
        collection_name: str,
        document_id: str,
        data: Any,
        output_dir: Optional[str] = None,
        provider_type: str = "annoy",
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Store structured data as searchable document.

        Args:
            collection_name: RAG collection name
            document_id: Document identifier
            data: Data to store
            output_dir: Optional output directory
            provider_type: RAG provider type
            **kwargs: Additional provider options

        Returns:
            Stored data

        Raises:
            StorageError: If operation fails
        """
        # Save file
        filename = f"{document_id}.json"
        await self.save_json(filename, data, base_dir=output_dir)

        # Add to RAG
        await self.rag.add([
            Document(text=json.dumps(data, indent=2), metadata={"id": document_id})
        ])

        return data

    async def search_structured_documents(
        self,
        collection_name: str,
        query_text: str,
        output_dir: Optional[str] = None,
        provider_type: str = "annoy",
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """Search structured documents in a collection.

        Args:
            collection_name: RAG collection name
            query_text: Search query
            output_dir: Optional output directory
            provider_type: RAG provider type
            **kwargs: Additional provider options

        Returns:
            List of matching documents

        Raises:
            StorageError: If search fails
        """
        results = await self.rag.search(query_text=query_text)

        # Convert documents to dictionaries
        documents = []
        for doc in results:
            try:
                data = json.loads(doc.text)
                documents.append(data)
            except:
                continue

        return documents

    async def store_and_search_structured(
        self,
        collection_name: str,
        document_id: str,
        data: Any,
        search_query: str,
        output_dir: Optional[str] = None,
        provider_type: str = "annoy",
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """Store and search structured documents in one operation.

        Args:
            collection_name: RAG collection name
            document_id: Document identifier
            data: Data to store
            search_query: Search query
            output_dir: Optional output directory
            provider_type: RAG provider type
            **kwargs: Additional provider options

        Returns:
            List of matching documents

        Raises:
            StorageError: If operation fails
        """
        # Store document
        await self.store_structured_document(
            collection_name=collection_name,
            document_id=document_id,
            data=data,
            output_dir=output_dir,
            provider_type=provider_type,
            **kwargs,
        )

        # Search documents
        return await self.search_structured_documents(
            collection_name=collection_name,
            query_text=search_query,
            output_dir=output_dir,
            provider_type=provider_type,
            **kwargs,
        )


class StorageComponent:
    """Storage component for file and directory management."""

    def __init__(self, config: Config) -> None:
        """Initialize storage component."""
        self.config = config
        self._provider: Optional[StorageProvider] = None
        self._base_dir: str = ".pepperpy/storage"

    def configure(
        self,
        base_dir: str = ".pepperpy/storage",
        provider_type: str = "local",
        **kwargs,
    ) -> "StorageComponent":
        """Configure the storage component."""
        self._base_dir = base_dir
        self._provider_type = provider_type
        self._provider_options = kwargs
        return self

    async def _initialize(self) -> None:
        """Initialize the storage provider."""
        try:
            if hasattr(self.config, "load_storage_provider"):
                self._provider = self.config.load_storage_provider(
                    base_dir=self._base_dir,
                    provider_type=getattr(self, "_provider_type", "local"),
                    **getattr(self, "_provider_options", {}),
                )
                if self._provider:
                    await self._provider.initialize()
        except Exception as e:
            print(f"Warning: Failed to initialize storage provider: {e}")

        os.makedirs(self._base_dir, exist_ok=True)

    async def _cleanup(self) -> None:
        """Clean up resources."""
        if self._provider and hasattr(self._provider, "cleanup"):
            try:
                await self._provider.cleanup()
            except Exception as e:
                print(f"Warning: Failed to cleanup storage provider: {e}")

    def ensure_dir(
        self, directory: Union[str, Path], base_dir: Optional[str] = None
    ) -> Path:
        """Ensure directory exists."""
        if base_dir:
            directory = os.path.join(base_dir, directory)
        else:
            directory = os.path.join(self._base_dir, directory)

        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        return path

    async def save_text(
        self, filename: str, content: str, base_dir: Optional[str] = None
    ) -> Path:
        """Save text content to file."""
        if not base_dir:
            base_dir = self._base_dir

        path = Path(base_dir) / filename
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        return path

    async def save_json(
        self, filename: str, data: Any, base_dir: Optional[str] = None, indent: int = 2
    ) -> Path:
        """Save JSON data to file."""
        if not base_dir:
            base_dir = self._base_dir

        path = Path(base_dir) / filename
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent)

        return path

    async def load_text(self, filename: str, base_dir: Optional[str] = None) -> str:
        """Load text content from file."""
        if not base_dir:
            base_dir = self._base_dir

        path = Path(base_dir) / filename

        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    async def load_json(self, filename: str, base_dir: Optional[str] = None) -> Any:
        """Load JSON data from file."""
        if not base_dir:
            base_dir = self._base_dir

        path = Path(base_dir) / filename

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    async def file_exists(self, filename: str, base_dir: Optional[str] = None) -> bool:
        """Check if file exists."""
        if not base_dir:
            base_dir = self._base_dir

        path = Path(base_dir) / filename
        return path.is_file()

    async def list_files(
        self, directory: str = "", pattern: str = "*", base_dir: Optional[str] = None
    ) -> List[str]:
        """List files in directory."""
        if not base_dir:
            base_dir = self._base_dir

        path = Path(base_dir) / directory
        if not path.exists():
            return []

        return [str(p.relative_to(path)) for p in path.glob(pattern) if p.is_file()]
