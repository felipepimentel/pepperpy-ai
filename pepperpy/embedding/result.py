"""
PepperPy Embedding Results.

Result classes for embedding operations.
"""

from typing import Any

from pepperpy.core.results import TextResult


class EmbeddingResult(TextResult):
    """Result of an embedding operation."""

    def __init__(
        self,
        content: str,
        embeddings: list[list[float]],
        model: str,
        metadata: dict[str, Any] | None = None,
    ):
        """Initialize embedding result.

        Args:
            content: Summary content
            embeddings: Embedding vectors
            model: Embedding model used
            metadata: Additional metadata
        """
        super().__init__(content=content, metadata=metadata or {})
        self.embeddings = embeddings
        self.model = model

        # Add to metadata
        self.metadata["model"] = model
        self.metadata["embedding_count"] = len(embeddings)
        self.metadata["dimension"] = len(embeddings[0]) if embeddings else 0

    @property
    def dimension(self) -> int:
        """Get the dimension of the embeddings.

        Returns:
            Embedding dimension
        """
        if not self.embeddings or not self.embeddings[0]:
            return 0
        return len(self.embeddings[0])

    @property
    def embedding_count(self) -> int:
        """Get the number of embeddings.

        Returns:
            Number of embeddings
        """
        return len(self.embeddings)

    def get_embedding(self, index: int) -> list[float] | None:
        """Get a specific embedding vector.

        Args:
            index: Embedding index

        Returns:
            Embedding vector or None if out of range
        """
        if 0 <= index < len(self.embeddings):
            return self.embeddings[index]
        return None


class SimilarityResult(TextResult):
    """Result of a similarity operation."""

    def __init__(
        self,
        content: str,
        similarities: list[dict[str, Any]],
        query: str,
        model: str,
        metadata: dict[str, Any] | None = None,
    ):
        """Initialize similarity result.

        Args:
            content: Summary content
            similarities: List of similarity results
            query: Query text
            model: Embedding model used
            metadata: Additional metadata
        """
        super().__init__(content=content, metadata=metadata or {})
        self.similarities = similarities
        self.query = query
        self.model = model

        # Add to metadata
        self.metadata["model"] = model
        self.metadata["query"] = query
        self.metadata["result_count"] = len(similarities)

    @property
    def result_count(self) -> int:
        """Get the number of similarity results.

        Returns:
            Number of results
        """
        return len(self.similarities)

    def get_top_result(self) -> dict[str, Any] | None:
        """Get the top similarity result.

        Returns:
            Top result or None if no results
        """
        if not self.similarities:
            return None
        return self.similarities[0]

    def get_result(self, index: int) -> dict[str, Any] | None:
        """Get a specific similarity result.

        Args:
            index: Result index

        Returns:
            Result or None if out of range
        """
        if 0 <= index < len(self.similarities):
            return self.similarities[index]
        return None
