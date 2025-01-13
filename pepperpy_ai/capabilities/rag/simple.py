"""Simple RAG capability implementation."""

from collections.abc import AsyncGenerator
from typing import Any, TypeVar, cast

import numpy as np
from numpy.typing import NDArray
from sentence_transformers import SentenceTransformer

from ...config.rag import RAGConfig
from ...providers.base import BaseProvider
from ...responses import AIResponse, ResponseMetadata
from .base import RAGCapability, RAGGenerateKwargs, RAGSearchKwargs
from .document import Document

T = TypeVar("T", bound=BaseProvider[Any])

class SimpleRAGCapability(RAGCapability[T]):
    """Simple RAG capability implementation."""

    def __init__(
        self,
        config: RAGConfig,
        provider: type[T]
    ) -> None:
        """Initialize RAG capability."""
        super().__init__(config, provider)
        self._model: SentenceTransformer | None = None
        self._embeddings: dict[str, list[float]] = {}

    async def initialize(self) -> None:
        """Initialize capability resources."""
        if not self.is_initialized:
            try:
                self._model = SentenceTransformer(self.config.model)
                self._initialized = True
            except ImportError as e:
                raise ImportError(
                    "Required packages not installed. "
                    "Please install sentence-transformers and numpy."
                ) from e

    async def cleanup(self) -> None:
        """Clean up capability resources."""
        if self.is_initialized:
            self._model = None
            self._embeddings.clear()
            self._initialized = False

    async def _compute_embedding(self, text: str) -> list[float]:
        """Compute embedding for text."""
        self._ensure_initialized()
        model = cast(SentenceTransformer, self._model)

        # Compute embedding asynchronously
        embeddings: NDArray[np.float32] = model.encode(text)
        return cast(list[float], embeddings.tolist())

    async def search(
        self,
        query: str,
        *,
        limit: int | None = None,
        **kwargs: RAGSearchKwargs,
    ) -> list[Document]:
        """Search for documents matching a query.

        Args:
            query: The search query.
            limit: Maximum number of documents to return.
            **kwargs: Additional keyword arguments.

        Returns:
            list[Document]: List of matching documents.
        """
        self._ensure_initialized()

        if not self._embeddings:
            return []

        # Compute query embedding
        query_embedding = await self._compute_embedding(query)

        # Compute similarities
        similarities = []
        for doc_id, doc_embedding in self._embeddings.items():
            similarity = (
                np.dot(query_embedding, doc_embedding)
                / (
                    np.linalg.norm(query_embedding)
                    * np.linalg.norm(doc_embedding)
                )
            )
            similarities.append((doc_id, similarity))

        # Sort by similarity and limit results
        similarities.sort(key=lambda x: x[1], reverse=True)
        if limit:
            similarities = similarities[:limit]

        # Return documents
        return [
            Document(id=doc_id, content="", metadata={"similarity": sim})
            for doc_id, sim in similarities
        ]

    async def generate(
        self,
        query: str,
        documents: list[Document],
        *,
        stream: bool = False,
        **kwargs: RAGGenerateKwargs,
    ) -> AIResponse | AsyncGenerator[AIResponse, None]:
        """Generate response from RAG.

        Args:
            query: User query.
            documents: Retrieved documents.
            stream: Whether to stream the response.
            **kwargs: Additional keyword arguments.

        Returns:
            AIResponse | AsyncGenerator[AIResponse, None]: Generated response.
        """
        self._ensure_initialized()

        # Generate response
        if stream:
            async def stream_response() -> AsyncGenerator[AIResponse, None]:
                yield AIResponse(
                    content="Simple RAG processing messages",
                    metadata=cast(ResponseMetadata, {
                        "model": self.config.model,
                        "provider": "simple_rag",
                        "usage": {"total_tokens": 0},
                        "finish_reason": "stop",
                    }),
                )
            return stream_response()

        return AIResponse(
            content="Simple RAG processing messages",
            metadata=cast(ResponseMetadata, {
                "model": self.config.model,
                "provider": "simple_rag",
                "usage": {"total_tokens": 0},
                "finish_reason": "stop",
            }),
        )
