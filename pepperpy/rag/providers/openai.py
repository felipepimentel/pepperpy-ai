"""OpenAI provider implementation for RAG capabilities.

This module provides an OpenAI implementation of the RAG provider interface,
using OpenAI embeddings for document retrieval.
"""

from typing import Any, Dict, List, Optional, Sequence

import numpy as np
from openai import OpenAI

from ..document import Document
from ..provider import RAGError, RAGProvider
from ..query import Query
from ..result import RetrievalResult


class OpenAIRAGProvider(RAGProvider):
    """OpenAI implementation of the RAG provider interface."""

    name = "openai"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "text-embedding-3-small",
        **kwargs: Any,
    ) -> None:
        """Initialize the OpenAI RAG provider.

        Args:
            api_key: OpenAI API key (default: None, uses env var)
            model: OpenAI embedding model (default: text-embedding-3-small)
            **kwargs: Additional configuration options

        Raises:
            RAGError: If required dependencies are not installed
        """
        try:
            self.client = OpenAI(api_key=api_key)
        except Exception as e:
            raise RAGError(f"Failed to initialize OpenAI client: {e}")

        self.model = model
        self.kwargs = kwargs
        self.documents: List[Document] = []

    async def initialize(self) -> None:
        """Initialize the provider."""
        pass

    async def shutdown(self) -> None:
        """Shut down the provider."""
        pass

    async def add_documents(
        self,
        documents: Sequence[Document],
        **kwargs: Any,
    ) -> None:
        """Add documents to the provider."""
        for doc in documents:
            if not doc.embeddings:
                response = await self.client.embeddings.create(
                    input=doc.content,
                    model=self.model,
                    **kwargs,
                )
                doc.embeddings = response.data[0].embedding
        self.documents.extend(documents)

    async def remove_documents(
        self,
        document_ids: List[str],
        **kwargs: Any,
    ) -> None:
        """Remove documents from the provider."""
        self.documents = [
            doc
            for doc in self.documents
            if not doc.metadata or doc.metadata.get("id") not in document_ids
        ]

    async def search(
        self,
        query: Query,
        limit: int = 10,
        **kwargs: Any,
    ) -> RetrievalResult:
        """Search for documents matching a query."""
        # Filter documents by metadata if specified
        filtered_docs = self.documents
        if query.metadata:
            filtered_docs = [
                doc
                for doc in filtered_docs
                if doc.metadata
                and all(doc.metadata.get(k) == v for k, v in query.metadata.items())
            ]

        # Get query embeddings
        if not query.embeddings:
            response = await self.client.embeddings.create(
                input=query.text,
                model=self.model,
                **kwargs,
            )
            query.embeddings = response.data[0].embedding

        # Calculate cosine similarity
        query_emb = np.array(query.embeddings)
        doc_embs = np.array([doc.embeddings for doc in filtered_docs])
        scores = np.dot(doc_embs, query_emb) / (
            np.linalg.norm(doc_embs, axis=1) * np.linalg.norm(query_emb)
        )

        # Sort by score and return top k
        indices = np.argsort(scores)[::-1][:limit]
        top_docs = [filtered_docs[i] for i in indices]
        top_scores = scores[indices].tolist()

        return RetrievalResult(
            query=query,
            documents=top_docs,
            scores=top_scores,
            metadata={
                "total_docs": len(self.documents),
                "filtered_docs": len(filtered_docs),
                "model": self.model,
            },
        )

    async def get_document(
        self,
        document_id: str,
        **kwargs: Any,
    ) -> Optional[Document]:
        """Get a document by ID."""
        for doc in self.documents:
            if doc.metadata and doc.metadata.get("id") == document_id:
                return doc
        return None

    async def list_documents(
        self,
        limit: int = 100,
        offset: int = 0,
        **kwargs: Any,
    ) -> List[Document]:
        """List documents in the provider."""
        return self.documents[offset : offset + limit]

    def get_capabilities(self) -> Dict[str, Any]:
        """Get OpenAI RAG provider capabilities."""
        return {
            "supported_models": [
                "text-embedding-3-small",
                "text-embedding-3-large",
                "text-embedding-ada-002",
            ],
            "max_docs": 2048,
            "supports_filters": True,
            "dimensions": {
                "text-embedding-3-small": 1536,
                "text-embedding-3-large": 3072,
                "text-embedding-ada-002": 1536,
            },
        }
