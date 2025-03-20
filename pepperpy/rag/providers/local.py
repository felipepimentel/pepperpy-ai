"""Local provider implementation for RAG capabilities.

This module provides a local implementation of the RAG provider interface,
using sentence-transformers for document embeddings and retrieval.
"""

from typing import Any, Dict, List, Sequence, Union

import numpy as np
from numpy.typing import NDArray

from .. import Document, Query, RAGError, RAGProvider, RetrievalResult


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
        self.embeddings: List[NDArray[np.float32]] = []

        try:
            self.model = SentenceTransformer(model, device=device)
        except Exception as e:
            raise RAGError(f"Failed to load local model: {e}")

    def initialize(self) -> None:
        """Initialize the provider.

        Validates that the model is loaded and ready.
        """
        if not hasattr(self, "model"):
            raise RAGError("Model not properly initialized")

    def add_documents(self, documents: Sequence[Document], **kwargs: Any) -> None:
        """Add documents to the retrieval collection.

        Args:
            documents: Documents to add
            **kwargs: Additional provider-specific arguments

        Raises:
            ValidationError: If documents are invalid
            RAGError: If document addition fails
        """
        try:
            # Generate embeddings for documents
            texts = [doc.content for doc in documents]
            embeddings = self.model.encode(
                texts, normalize_embeddings=self.normalize, **kwargs
            )

            # Store documents and embeddings
            for doc, embedding in zip(documents, embeddings):
                self.documents.append(doc)
                self.embeddings.append(embedding.astype(np.float32))

        except Exception as e:
            raise RAGError(f"Failed to add documents: {e}")

    def retrieve(self, query: Union[str, Query], **kwargs: Any) -> RetrievalResult:
        """Retrieve relevant documents for a query.

        Args:
            query: Query string or Query object
            **kwargs: Additional provider-specific arguments

        Returns:
            RetrievalResult containing matched documents and scores

        Raises:
            ValidationError: If query is invalid
            RAGError: If retrieval fails
        """
        try:
            # Convert query to Query object if string
            if isinstance(query, str):
                query = Query(text=query)

            # Generate query embedding
            query_embedding = self.model.encode(
                query.text, normalize_embeddings=self.normalize, **kwargs
            ).astype(np.float32)

            # Calculate similarity scores
            scores = []
            for doc_embedding in self.embeddings:
                if self.normalize:
                    score = np.dot(query_embedding, doc_embedding)
                else:
                    score = np.dot(query_embedding, doc_embedding) / (
                        np.linalg.norm(query_embedding) * np.linalg.norm(doc_embedding)
                    )
                scores.append(float(score))

            # Sort by score and apply filters
            results = list(zip(self.documents, scores))
            results.sort(key=lambda x: x[1], reverse=True)

            # Apply filters if specified
            if query.filters:
                results = [
                    (doc, score)
                    for doc, score in results
                    if doc.metadata
                    and all(doc.metadata.get(k) == v for k, v in query.filters.items())
                ]

            # Apply score threshold if specified
            if query.score_threshold is not None:
                results = [
                    (doc, score)
                    for doc, score in results
                    if score >= query.score_threshold
                ]

            # Limit to k results
            results = results[: query.k]

            return RetrievalResult(
                documents=[doc for doc, _ in results],
                scores=[score for _, score in results],
                metadata={
                    "total_docs": len(self.documents),
                    "filtered_docs": len(results),
                    "model": self.model_name,
                    "device": self.device,
                },
            )

        except Exception as e:
            raise RAGError(f"Failed to retrieve documents: {e}")

    def delete_documents(self, document_ids: Sequence[str], **kwargs: Any) -> None:
        """Delete documents from the retrieval collection.

        Args:
            document_ids: IDs of documents to delete
            **kwargs: Additional provider-specific arguments

        Raises:
            ValidationError: If document IDs are invalid
            RAGError: If document deletion fails
        """
        try:
            # Find indices of documents to delete
            indices_to_delete = []
            for i, doc in enumerate(self.documents):
                doc_id = doc.metadata.get("id") if doc.metadata else None
                if doc_id and doc_id in document_ids:
                    indices_to_delete.append(i)

            # Delete documents and embeddings
            for i in reversed(indices_to_delete):
                del self.documents[i]
                del self.embeddings[i]

        except Exception as e:
            raise RAGError(f"Failed to delete documents: {e}")

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
