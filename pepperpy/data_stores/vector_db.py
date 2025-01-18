"""Vector database interface and implementations."""

from abc import ABC, abstractmethod
from typing import Any

import numpy as np
from pydantic import BaseModel


class Document(BaseModel):
    """Represents a document in the vector store."""

    id: str
    text: str
    metadata: dict[str, Any] = {}
    embedding: list[float] | None = None


class SearchResult(BaseModel):
    """Represents a search result from the vector store."""

    document: Document
    score: float


class VectorDBConfig(BaseModel):
    """Configuration for vector databases."""

    collection_name: str
    embedding_dim: int
    distance_metric: str = "cosine"
    index_params: dict[str, Any] = {}


class BaseVectorDB(ABC):
    """Base class for vector database implementations."""

    def __init__(self, config: VectorDBConfig) -> None:
        """Initialize the vector database.

        Args:
            config: Configuration for the database
        """
        self.config = config

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize any resources needed by the database."""
        pass

    @abstractmethod
    async def add_documents(
        self, documents: list[Document], batch_size: int = 100
    ) -> list[str]:
        """Add documents to the database.

        Args:
            documents: List of documents to add
            batch_size: Size of batches for insertion

        Returns:
            List of document IDs

        Raises:
            Exception: If document insertion fails
        """
        pass

    @abstractmethod
    async def search(
        self,
        query_embedding: list[float],
        k: int = 5,
        filter: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """Search for similar documents.

        Args:
            query_embedding: Query vector to search with
            k: Number of results to return
            filter: Optional metadata filter

        Returns:
            List of search results

        Raises:
            Exception: If search fails
        """
        pass

    @abstractmethod
    async def delete(self, document_ids: str | list[str]) -> None:
        """Delete documents from the database.

        Args:
            document_ids: ID or list of IDs to delete

        Raises:
            Exception: If deletion fails
        """
        pass

    @abstractmethod
    async def get(
        self, document_ids: str | list[str]
    ) -> Document | None | list[Document | None]:
        """Get documents by ID.

        Args:
            document_ids: ID or list of IDs to retrieve

        Returns:
            Document(s) if found, None if not found

        Raises:
            Exception: If retrieval fails
        """
        pass

    @abstractmethod
    async def update(self, documents: Document | list[Document]) -> None:
        """Update documents in the database.

        Args:
            documents: Document(s) to update

        Raises:
            Exception: If update fails
        """
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up any resources used by the database."""
        pass

    async def __aenter__(self) -> "BaseVectorDB":
        """Context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Context manager exit."""
        await self.cleanup()

    def _validate_embedding(self, embedding: list[float]) -> None:
        """Validate an embedding vector.

        Args:
            embedding: The embedding to validate

        Raises:
            ValueError: If embedding is invalid
        """
        if len(embedding) != self.config.embedding_dim:
            raise ValueError(
                f"Embedding dimension mismatch. Expected {self.config.embedding_dim}, "
                f"got {len(embedding)}"
            )

    def _compute_similarity(
        self, embedding1: list[float], embedding2: list[float]
    ) -> float:
        """Compute similarity between two embeddings.

        Args:
            embedding1: First embedding
            embedding2: Second embedding

        Returns:
            Similarity score

        Raises:
            ValueError: If embeddings are invalid
        """
        self._validate_embedding(embedding1)
        self._validate_embedding(embedding2)

        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)

        if self.config.distance_metric == "cosine":
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            return float(np.dot(vec1, vec2) / (norm1 * norm2))
        elif self.config.distance_metric == "euclidean":
            return float(-np.linalg.norm(vec1 - vec2))
        elif self.config.distance_metric == "dot":
            return float(np.dot(vec1, vec2))
        else:
            msg = f"Unsupported distance metric: {self.config.distance_metric}"
            raise ValueError(msg)
