"""Local provider implementation for RAG capabilities.

This module provides a local implementation of the RAG provider interface,
using sentence-transformers for document embeddings and retrieval.
"""

from typing import Any, Dict, List, Optional, Sequence

import numpy as np

from ..document import Document
from ..provider import RAGError, RAGProvider
from ..query import Query
from ..result import RetrievalResult


class LocalRAGProvider(RAGProvider):
    """Local implementation of the RAG provider interface using sentence-transformers."""

    name = "local"

    def __init__(
        self,
        model: str = "all-MiniLM-L6-v2",
        device: str = "cpu",
        normalize_embeddings: bool = True,
        **kwargs: Any,
    ) -> None:
        """Initialize the Local RAG provider.

        Args:
            model: Model name from sentence-transformers (default: all-MiniLM-L6-v2)
            device: Device to run model on (default: cpu)
            normalize_embeddings: Whether to normalize embeddings (default: True)
            **kwargs: Additional configuration options

        Raises:
            RAGError: If required dependencies are not installed
        """
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise RAGError(
                "Local provider requires sentence-transformers. "
                "Install with: pip install sentence-transformers"
            )

        self.model_name = model
        self.device = device
        self.normalize = normalize_embeddings
        self.kwargs = kwargs
        self.documents: List[Document] = []
        self.model = SentenceTransformer(model, device=device)

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
                doc.embeddings = self.model.encode(
                    doc.content,
                    normalize_embeddings=self.normalize,
                ).tolist()
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
            query.embeddings = self.model.encode(
                query.text,
                normalize_embeddings=self.normalize,
            ).tolist()

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
        """Get Local RAG provider capabilities."""
        return {
            "supported_models": [
                "all-MiniLM-L6-v2",
                "all-mpnet-base-v2",
                "multi-qa-MiniLM-L6-cos-v1",
            ],
            "max_docs": 100000,  # Limited by available memory
            "supports_filters": True,
            "dimensions": {
                "all-MiniLM-L6-v2": 384,
                "all-mpnet-base-v2": 768,
                "multi-qa-MiniLM-L6-cos-v1": 384,
            },
        }
