"""Simple RAG implementation using sentence transformers."""

import asyncio
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, cast

import numpy as np
from sentence_transformers import SentenceTransformer

from pepperpy_core.responses import AIResponse
from pepperpy_core.providers import BaseProvider

from .base import BaseRAG, Document, RAGConfig


@dataclass
class SimpleRAGConfig(RAGConfig):
    """Configuration for simple RAG implementation.
    
    Attributes:
        model_name: The name of the sentence transformer model to use.
        device: The device to use for model inference (e.g., "cpu", "cuda").
        normalize_embeddings: Whether to normalize embeddings to unit length.
        batch_size: The batch size for computing embeddings.
    """

    model_name: str = "all-MiniLM-L6-v2"
    device: str = "cpu"
    normalize_embeddings: bool = True
    batch_size: int = 32
    metadata: Dict[str, Any] = field(default_factory=dict)


class SimpleRAG(BaseRAG):
    """Simple RAG implementation using sentence transformers."""

    def __init__(self, config: RAGConfig, provider: BaseProvider) -> None:
        """Initialize the simple RAG implementation.

        Args:
            config: The RAG configuration.
            provider: The AI provider to use for generation.
        """
        super().__init__(config, provider)
        self._documents: Dict[str, Document] = {}
        self._embeddings: Dict[str, np.ndarray] = {}
        self._model = SentenceTransformer("all-MiniLM-L6-v2")

    async def initialize(self) -> None:
        """Initialize the RAG system."""
        # Nothing to initialize
        pass

    async def cleanup(self) -> None:
        """Clean up resources."""
        await self.clear()

    async def add_document(self, document: Document) -> None:
        """Add a document to the RAG system.

        Args:
            document: The document to add.
        """
        # Compute embedding asynchronously
        embedding = await asyncio.to_thread(
            self._model.encode, document.content, convert_to_numpy=True
        )
        self._documents[document.id] = document
        self._embeddings[document.id] = embedding

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
        """
        if not self._documents:
            return []

        # Compute query embedding
        query_embedding = await asyncio.to_thread(
            self._model.encode, query, convert_to_numpy=True
        )

        # Calculate similarities
        similarities = {
            doc_id: np.dot(query_embedding, doc_embedding)
            for doc_id, doc_embedding in self._embeddings.items()
        }

        # Sort by similarity
        sorted_ids = sorted(similarities.keys(), key=lambda k: similarities[k], reverse=True)
        if limit is not None:
            sorted_ids = sorted_ids[:limit]

        return [self._documents[doc_id] for doc_id in sorted_ids]

    async def generate(
        self,
        query: str,
        *,
        stream: bool = False,
        **kwargs: Any,
    ) -> AIResponse:
        """Generate a response using retrieved documents.

        Args:
            query: The query to answer.
            stream: Whether to stream the response.
            **kwargs: Additional generation parameters.

        Returns:
            The generated response.
        """
        # Retrieve relevant documents
        limit = kwargs.pop("limit", self.config.max_documents)
        documents = await self.search(query, limit=limit)

        # Format prompt with retrieved documents
        docs_text = "\n\n".join(
            f"Document {i+1}:\n{doc.content}"
            for i, doc in enumerate(documents)
        )
        prompt = self.config.prompt_template.format(
            documents=docs_text,
            query=query,
        )

        # Generate response
        if stream:
            return await self.provider.stream(prompt, **kwargs)
        return await self.provider.complete(prompt, **kwargs)

    async def clear(self) -> None:
        """Clear all documents from the RAG system."""
        self._documents.clear()
        self._embeddings.clear() 