"""Chroma storage provider implementation.

This module provides a Chroma-based implementation of the storage provider interface,
using ChromaDB for persistent vector storage and retrieval.
"""

import hashlib
import uuid
from typing import Any, Dict, List, Optional, Sequence, Union

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


def _to_dict(metadata: Optional[Metadata]) -> Dict[str, Any]:
    """Convert metadata to dictionary."""
    if metadata is None:
        return {}
    return {k: v for k, v in metadata.items()}


def _to_embedding(
    embedding: Optional[Union[Embedding, List[float]]],
) -> Optional[List[float]]:
    """Convert embedding to list of floats."""
    if embedding is None:
        return None
    if isinstance(embedding, list):
        return embedding
    return list(embedding)


def _get_embeddings(result: Union[GetResult, QueryResult]) -> Optional[List[Embedding]]:
    """Get embeddings from result."""
    if "embeddings" not in result:
        return None
    embeddings = result.get("embeddings")
    if not embeddings:
        return None
    return embeddings


class HashEmbeddingFunction(EmbeddingFunction):
    """Simple embedding function that uses SHA-256 hash for testing purposes."""

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

    def __init__(
        self,
        collection_name: str = "pepperpy",
        persist_directory: Optional[str] = None,
        embedding_function: Optional[Union[str, EmbeddingFunction]] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the Chroma storage provider.

        Args:
            collection_name: Name of the ChromaDB collection (default: pepperpy)
            persist_directory: Directory to persist vectors (default: None, in-memory)
            embedding_function: Name or instance of embedding function (default: None, uses hash-based)
            **kwargs: Additional configuration options

        Raises:
            StorageError: If required dependencies are not installed
        """
        super().__init__(name=name, **kwargs)
        try:
            import chromadb
            from chromadb.config import Settings
        except ImportError:
            raise StorageError(
                "Chroma provider requires chromadb. Install with: pip install chromadb"
            )

        # Store persist_directory for capabilities
        self.persist_directory = persist_directory

        # Initialize ChromaDB client
        settings = Settings(
            persist_directory=persist_directory,
            anonymized_telemetry=False,
            **kwargs,
        )
        self.client = chromadb.Client(settings)

        # Initialize embedding function
        if isinstance(embedding_function, str):
            try:
                from chromadb.utils import embedding_functions

                self.embeddings = getattr(embedding_functions, embedding_function)()
            except (ImportError, AttributeError) as e:
                raise StorageError(f"Failed to initialize embedding function: {e}")
        elif isinstance(embedding_function, EmbeddingFunction):
            self.embeddings = embedding_function
        else:
            # Use simple hash-based embeddings by default
            self.embeddings = HashEmbeddingFunction()

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embeddings,
            metadata={"hnsw:space": "cosine"},
        )

    async def store_vectors(
        self,
        vectors: Sequence[List[float]],
        metadata: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> List[str]:
        """Store vectors with optional metadata."""
        if not vectors:
            return []

        # Generate IDs for vectors
        ids = [str(uuid.uuid4()) for _ in vectors]

        # Add to collection
        self.collection.add(
            ids=ids,
            embeddings=vectors,
            metadatas=metadata,
            **kwargs,
        )

        return ids

    async def retrieve_vectors(
        self,
        vector_ids: List[str],
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """Retrieve vectors by ID."""
        result = self.collection.get(
            ids=vector_ids,
            include_embeddings=True,
            **kwargs,
        )

        vectors = []
        for i, vector_id in enumerate(result["ids"]):
            vectors.append({
                "id": vector_id,
                "vector": result["embeddings"][i],
                "metadata": _to_dict(result["metadatas"][i]),
            })
        return vectors

    async def delete_vectors(
        self,
        vector_ids: List[str],
        **kwargs: Any,
    ) -> None:
        """Delete vectors by ID."""
        self.collection.delete(ids=vector_ids, **kwargs)

    async def search_vectors(
        self,
        query_vector: List[float],
        limit: int = 10,
        filter: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors."""
        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=limit,
            where=filter,
            include_embeddings=True,
            **kwargs,
        )

        matches = []
        for i, vector_id in enumerate(results["ids"][0]):
            matches.append({
                "id": vector_id,
                "vector": results["embeddings"][0][i],
                "metadata": _to_dict(results["metadatas"][0][i]),
                "score": float(results["distances"][0][i]),
            })
        return matches

    async def list_vectors(
        self,
        limit: int = 100,
        offset: int = 0,
        filter: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """List stored vectors."""
        # Note: ChromaDB doesn't support offset/limit directly
        # We'll fetch all and slice
        result = self.collection.get(
            where=filter,
            include_embeddings=True,
            **kwargs,
        )

        vectors = []
        for i, vector_id in enumerate(result["ids"][offset : offset + limit]):
            vectors.append({
                "id": vector_id,
                "vector": result["embeddings"][i],
                "metadata": _to_dict(result["metadatas"][i]),
            })
        return vectors

    def get_capabilities(self) -> Dict[str, Any]:
        """Get Chroma storage provider capabilities."""
        return {
            "persistent": bool(self.persist_directory),
            "max_vectors": 1_000_000,  # ChromaDB can handle millions of vectors
            "supports_filters": True,
            "supports_persistence": True,
            "embedding_function": (
                self.embeddings.__class__.__name__ if self.embeddings else "hash-based"
            ),
        }
