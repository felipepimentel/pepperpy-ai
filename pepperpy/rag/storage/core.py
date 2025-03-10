"""Core functionality for vector storage in RAG.

This module provides the core functionality for vector storage in RAG,
including vector representation, storage, and retrieval.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from pepperpy.rag.document.core import DocumentChunk
from pepperpy.rag.errors import StorageError
from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)


@dataclass
class VectorEmbedding:
    """A vector embedding for a document chunk.

    Attributes:
        vector: The vector embedding
        document_id: The ID of the document this embedding belongs to
        chunk_id: The ID of the document chunk this embedding belongs to
        metadata: Additional metadata for the embedding
    """

    vector: List[float]
    document_id: str
    chunk_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the vector embedding to a dictionary.

        Returns:
            The vector embedding as a dictionary
        """
        return {
            "vector": self.vector,
            "document_id": self.document_id,
            "chunk_id": self.chunk_id,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VectorEmbedding":
        """Create a vector embedding from a dictionary.

        Args:
            data: The dictionary to create the vector embedding from

        Returns:
            The created vector embedding
        """
        return cls(
            vector=data.get("vector", []),
            document_id=data.get("document_id", ""),
            chunk_id=data.get("chunk_id", ""),
            metadata=data.get("metadata", {}),
        )


@dataclass
class ScoredChunk:
    """A document chunk with a similarity score.

    Attributes:
        chunk: The document chunk
        score: The similarity score
    """

    chunk: DocumentChunk
    score: float


class VectorStore(ABC):
    """Base class for vector stores.

    Vector stores are responsible for storing and retrieving vector embeddings
    for document chunks.
    """

    @abstractmethod
    async def add_embedding(self, embedding: VectorEmbedding) -> None:
        """Add a vector embedding to the store.

        Args:
            embedding: The vector embedding to add

        Raises:
            VectorStoreError: If there is an error adding the embedding
        """
        pass

    @abstractmethod
    async def add_embeddings(self, embeddings: List[VectorEmbedding]) -> None:
        """Add vector embeddings to the store.

        Args:
            embeddings: The vector embeddings to add

        Raises:
            VectorStoreError: If there is an error adding the embeddings
        """
        pass

    @abstractmethod
    async def get_embedding(self, chunk_id: str) -> Optional[VectorEmbedding]:
        """Get a vector embedding from the store.

        Args:
            chunk_id: The ID of the document chunk to get the embedding for

        Returns:
            The vector embedding, or None if it doesn't exist

        Raises:
            VectorStoreError: If there is an error getting the embedding
        """
        pass

    @abstractmethod
    async def delete_embedding(self, chunk_id: str) -> None:
        """Delete a vector embedding from the store.

        Args:
            chunk_id: The ID of the document chunk to delete the embedding for

        Raises:
            VectorStoreError: If there is an error deleting the embedding
        """
        pass

    @abstractmethod
    async def delete_embeddings(self, document_id: str) -> None:
        """Delete vector embeddings from the store.

        Args:
            document_id: The ID of the document to delete embeddings for

        Raises:
            VectorStoreError: If there is an error deleting the embeddings
        """
        pass

    @abstractmethod
    async def search(
        self,
        query_vector: List[float],
        limit: int = 10,
        min_score: float = 0.0,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[VectorEmbedding, float]]:
        """Search for similar vector embeddings.

        Args:
            query_vector: The query vector
            limit: The maximum number of results to return
            min_score: The minimum similarity score
            filter_metadata: Metadata to filter the results by

        Returns:
            A list of tuples of vector embeddings and their similarity scores

        Raises:
            VectorStoreError: If there is an error searching for embeddings
        """
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear the store.

        Raises:
            VectorStoreError: If there is an error clearing the store
        """
        pass


class VectorStoreManager:
    """Manager for vector stores.

    The vector store manager provides a unified interface for working with
    different vector stores.
    """

    def __init__(self):
        """Initialize the vector store manager."""
        self._stores: Dict[str, VectorStore] = {}
        self._default_store: Optional[str] = None

    def register_store(
        self, name: str, store: VectorStore, default: bool = False
    ) -> None:
        """Register a vector store.

        Args:
            name: The name of the store
            store: The store to register
            default: Whether to set this store as the default

        Raises:
            StorageError: If a store with the same name is already registered
        """
        if name in self._stores:
            raise StorageError(f"Vector store '{name}' is already registered")

        self._stores[name] = store

        if default or self._default_store is None:
            self._default_store = name

    def unregister_store(self, name: str) -> None:
        """Unregister a vector store.

        Args:
            name: The name of the store to unregister

        Raises:
            StorageError: If the store is not registered
        """
        if name not in self._stores:
            raise StorageError(f"Vector store '{name}' is not registered")

        del self._stores[name]

        if self._default_store == name:
            self._default_store = next(iter(self._stores)) if self._stores else None

    def get_store(self, name: Optional[str] = None) -> VectorStore:
        """Get a vector store.

        Args:
            name: The name of the store to get, or None to get the default store

        Returns:
            The vector store

        Raises:
            StorageError: If the store is not registered or no default store is set
        """
        if name is None:
            if self._default_store is None:
                raise StorageError("No default vector store is set")

            name = self._default_store

        if name not in self._stores:
            raise StorageError(f"Vector store '{name}' is not registered")

        return self._stores[name]

    def set_default_store(self, name: str) -> None:
        """Set the default vector store.

        Args:
            name: The name of the store to set as the default

        Raises:
            StorageError: If the store is not registered
        """
        if name not in self._stores:
            raise StorageError(f"Vector store '{name}' is not registered")

        self._default_store = name

    def get_default_store(self) -> Optional[str]:
        """Get the name of the default vector store.

        Returns:
            The name of the default vector store, or None if no default store is set
        """
        return self._default_store

    def get_stores(self) -> Dict[str, VectorStore]:
        """Get all registered vector stores.

        Returns:
            A dictionary of store names to vector stores
        """
        return self._stores.copy()


# Global vector store manager
_vector_store_manager = VectorStoreManager()


def get_vector_store_manager() -> VectorStoreManager:
    """Get the global vector store manager.

    Returns:
        The global vector store manager
    """
    return _vector_store_manager
