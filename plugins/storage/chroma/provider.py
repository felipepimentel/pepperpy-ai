"""Chroma storage provider implementation.

This module provides a Chroma-based implementation of the storage provider interface,
using ChromaDB for persistent vector storage and retrieval.
"""

import hashlib
import uuid
from typing import Any

from chromadb.api.types import (
    Documents,
    Embedding,
    EmbeddingFunction,
    Embeddings,
    GetResult,
    Metadata,
    QueryResult,
)

from ..base import StorageError, StorageProvider


def _to_dict(metadata: Metadata | None) -> dict[str, Any]:
    """Convert metadata to dictionary."""
    if metadata is None:
        return {}
    return {k: v for k, v in metadata.items()}


def _to_embedding(
    embedding: Embedding | list[float] | None,
) -> list[float] | None:
    """Convert embedding to list of floats."""
    if embedding is None:
        return None
    if isinstance(embedding, list):
        return embedding
    return list(embedding)


def _get_embeddings(result: GetResult | QueryResult) -> list[Embedding] | None:
    """Get embeddings from result."""
    if "embeddings" not in result:
        return None
    embeddings = result.get("embeddings")
    if not embeddings:
        return None
    return embeddings


class HashEmbeddingFunction(EmbeddingFunction):
    """Simple embedding function that uses SHA-256 hash for development and
    demonstration purposes.

    This embedding function creates vector representations using hash values,
    making it suitable for development, demonstrations, and prototyping scenarios
    where advanced semantic understanding is not required.
    """

    def __init__(self, dimension: int = 64) -> None:
        """Initialize the hash embedding function.

        Args:
            dimension: Size of the embedding vector (default: 64)
        """
        self.dimension = dimension

    def __call__(self, texts: Documents) -> Embeddings:
        """Convert texts to embeddings using SHA-256 hash.

        Args:
            texts: List of texts to convert to embeddings

        Returns:
            List of embedding vectors
        """
        embeddings = []
        for text in texts:
            # Get SHA-256 hash of text
            hash_bytes = hashlib.sha256(str(text).encode()).digest()

            # Convert hash bytes to floats between -1 and 1
            embedding = []
            for i in range(self.dimension):
                byte_val = hash_bytes[i % 32]  # Reuse hash bytes if needed
                embedding.append((byte_val / 128.0) - 1.0)  # Scale to [-1, 1]

            embeddings.append(embedding)
        return embeddings


class ChromaStorageProvider(StorageProvider):
    """Chroma implementation of the storage provider interface using ChromaDB."""

    name = "chroma"

    # Attributes auto-bound from plugin.yaml with default values as fallback
    api_key: str
    client = None  # Will be set to ChromaDB client in __init__

    def __init__(
        self,
        collection_name: str = "default",
        persist_directory: str | None = None,
        embedding_function: EmbeddingFunction | None = None,
    ):
        """Initialize the ChromaStorageProvider.

        Args:
            collection_name: Name of the collection to use
            persist_directory: Directory to persist the database. If None, uses memory
            embedding_function: Function to use for embedding. If None, no embedding
        """
        import chromadb

        self.client = chromadb.Client()
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.embedding_function = embedding_function
        self._collection = None

    async def initialize(self):
        """Initialize the client and collection."""
        self._collection = await self._get_or_create_collection()

    async def _get_or_create_collection(self):
        """Get or create the collection."""
        # Check if client is initialized
        if self.client is None:
            raise StorageError("Client not initialized")

        # ChromaDB's client doesn't have async methods, so we need to use
        # synchronous methods
        try:
            return self.client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function,
            )
        except Exception as e:
            raise StorageError(f"Failed to get or create collection: {e}") from e

    async def store_vectors(
        self,
        vectors: list[list[float]],
        metadata: list[dict[str, Any]],
        vector_ids: list[str] | None = None,
        **kwargs: Any,
    ) -> list[str]:
        """Store vectors in the collection."""
        # Generate IDs if not provided
        if vector_ids is None:
            vector_ids = [str(uuid.uuid4()) for _ in range(len(vectors))]

        # Ensure IDs match vector count
        if len(vector_ids) != len(vectors):
            raise StorageError(
                f"Number of IDs ({len(vector_ids)}) must match vectors ({len(vectors)})"
            )

        # Add to collection
        if self._collection is None:
            raise StorageError("Collection not initialized")

        self._collection.add(
            ids=vector_ids,
            embeddings=vectors,
            metadatas=metadata,
            **kwargs,
        )

        return vector_ids

    async def get_vectors(
        self, vector_ids: list[str], **kwargs: Any
    ) -> list[dict[str, Any]]:
        """Retrieve vectors by ID."""
        if self._collection is None:
            raise StorageError("Collection not initialized")

        result = self._collection.get(
            ids=vector_ids,
            include_embeddings=True,
            **kwargs,
        )

        # Format results
        return [
            {
                "id": id,
                "embedding": embedding,
                "metadata": metadata,
            }
            for id, embedding, metadata in zip(
                result["ids"], result["embeddings"], result["metadatas"], strict=False
            )
        ]

    async def delete_vectors(self, vector_ids: list[str], **kwargs: Any) -> None:
        """Delete vectors by ID."""
        if self._collection is None:
            raise StorageError("Collection not initialized")

        self._collection.delete(ids=vector_ids, **kwargs)

    async def search_vectors(
        self,
        query_vector: list[float],
        limit: int = 10,
        filter: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """Search for similar vectors."""
        if self._collection is None:
            raise StorageError("Collection not initialized")

        results = self._collection.query(
            query_embeddings=[query_vector],
            n_results=limit,
            where=filter,
            include_embeddings=True,
            **kwargs,
        )

        # Format results
        return [
            {
                "id": id,
                "embedding": embedding,
                "metadata": metadata,
                "distance": distance,
            }
            for id, embedding, metadata, distance in zip(
                results["ids"][0],
                results["embeddings"][0],
                results["metadatas"][0],
                results["distances"][0],
                strict=False,
            )
        ]

    async def list_vectors(
        self,
        limit: int | None = None,
        offset: int = 0,
        filter: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """List vectors with optional filtering."""
        if self._collection is None:
            raise StorageError("Collection not initialized")

        # Note: ChromaDB doesn't support offset/limit directly
        # We'll fetch all and slice
        result = self._collection.get(
            where=filter,
            include_embeddings=True,
            **kwargs,
        )

        # Apply offset and limit manually
        start = offset
        end = None if limit is None else offset + limit

        return [
            {
                "id": id,
                "embedding": embedding,
                "metadata": metadata,
            }
            for id, embedding, metadata in zip(
                result["ids"][start:end],
                result["embeddings"][start:end],
                result["metadatas"][start:end],
                strict=False,
            )
        ]

    def get_capabilities(self) -> dict[str, Any]:
        """Get Chroma storage provider capabilities."""
        return {
            "persistent": bool(self.persist_directory),
            "max_vectors": 1_000_000,  # ChromaDB can handle millions of vectors
            "supports_filters": True,
            "supports_persistence": True,
            "embedding_function": (
                self.embedding_function.__class__.__name__
                if self.embedding_function
                else "hash-based"
            ),
        }
