"""Simple RAG capability implementation."""

import asyncio
from collections.abc import AsyncGenerator
from typing import Any, Dict, List, Optional, Type, cast

import numpy as np
from sentence_transformers import SentenceTransformer

from ...ai_types import Message, MessageRole
from ...exceptions import CapabilityError, DependencyError
from ...providers.base import BaseProvider
from ...responses import AIResponse
from .base import Document, RAGCapability, RAGConfig


class SimpleRAGCapability(RAGCapability):
    """Simple RAG capability implementation."""

    def __init__(self, config: RAGConfig, provider: Type[BaseProvider[Any]]) -> None:
        """Initialize capability.

        Args:
            config: Capability configuration
            provider: Provider class to use
        """
        super().__init__(config, provider)
        self._model: Optional[SentenceTransformer] = None
        self._np: Optional[Any] = None
        self._documents: Dict[str, Document] = {}
        self._embeddings: Dict[str, List[float]] = {}

    def _ensure_initialized(self) -> None:
        """Ensure capability is initialized.

        Raises:
            CapabilityError: If capability is not initialized
        """
        if self._np is None or self._model is None:
            raise CapabilityError("RAG capability not initialized", "rag")

    async def _setup(self) -> None:
        """Setup capability resources."""
        try:
            self._np = np
            self._model = SentenceTransformer(self.config.model_name)
        except ImportError as e:
            raise DependencyError(
                "Missing required dependencies for RAG capability. "
                "Install with: pip install pepperpy-ai[rag]",
                package="numpy, sentence-transformers"
            ) from e

    async def _teardown(self) -> None:
        """Teardown capability resources."""
        self._model = None
        self._np = None
        self._documents.clear()
        self._embeddings.clear()

    async def add_document(self, document: Document) -> None:
        """Add a document to the RAG system.

        Args:
            document: The document to add.

        Raises:
            CapabilityError: If capability is not initialized
        """
        self._ensure_initialized()
        model = cast(SentenceTransformer, self._model)
        np_module = cast(Any, self._np)

        # Compute embedding asynchronously
        embedding = await asyncio.to_thread(
            model.encode, document.content, convert_to_numpy=True
        )
        self._documents[document.id] = document
        self._embeddings[document.id] = embedding.tolist()

    async def remove_document(self, document_id: str) -> None:
        """Remove a document from the RAG system.

        Args:
            document_id: The ID of the document to remove.
        """
        self._documents.pop(document_id, None)
        self._embeddings.pop(document_id, None)

    async def search(
        self,
        query: str,
        *,
        limit: Optional[int] = None,
        **kwargs: Any,
    ) -> List[Document]:
        """Search for documents matching a query.

        Args:
            query: The search query.
            limit: Maximum number of documents to return.
            **kwargs: Additional search parameters.

        Returns:
            A list of matching documents.

        Raises:
            CapabilityError: If capability is not initialized
        """
        self._ensure_initialized()
        model = cast(SentenceTransformer, self._model)
        np_module = cast(Any, self._np)

        if not self._documents:
            return []

        # Compute query embedding
        query_embedding = await asyncio.to_thread(
            model.encode, query, convert_to_numpy=True
        )

        # Compute similarities
        similarities = []
        for doc_id, doc_embedding in self._embeddings.items():
            similarity = np_module.dot(query_embedding, doc_embedding) / (
                np_module.linalg.norm(query_embedding) * np_module.linalg.norm(doc_embedding)
            )
            similarities.append((doc_id, similarity))

        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        if limit:
            similarities = similarities[:limit]

        # Return documents
        return [self._documents[doc_id] for doc_id, _ in similarities]
