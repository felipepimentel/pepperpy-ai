"""OpenAI provider implementation for RAG capabilities.

This module provides OpenAI-specific implementations of the RAG provider
interface, using OpenAI's embedding models for document retrieval.
"""

from typing import Any, Dict, List, Optional, Sequence, Union

import numpy as np
from numpy.typing import NDArray
from openai import OpenAI

from .. import Document, Query, RAGError, RAGProvider, RetrievalResult


class OpenAIRAGProvider(RAGProvider):
    """OpenAI implementation of the RAG provider interface."""

    name = "openai"

    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-3-small",
        organization_id: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        **kwargs: Any,
    ) -> None:
        """Initialize the OpenAI RAG provider.

        Args:
            api_key: OpenAI API key
            model: Model to use (default: text-embedding-3-small)
            organization_id: Optional organization ID
            base_url: Optional API base URL
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
            **kwargs: Additional configuration options
        """
        self.model = model
        self.client = OpenAI(
            api_key=api_key,
            organization=organization_id,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
        )
        self.documents: List[Document] = []
        self.embeddings: List[NDArray[np.float32]] = []

    def initialize(self) -> None:
        """Initialize the provider.

        Validates the API key and model availability.
        """
        try:
            self.client.models.list()
        except Exception as e:
            raise RAGError(f"Failed to initialize OpenAI RAG provider: {e}")

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
            response = self.client.embeddings.create(
                model=self.model, input=texts, **kwargs
            )

            # Store documents and embeddings
            for doc, data in zip(documents, response.data):
                self.documents.append(doc)
                self.embeddings.append(np.array(data.embedding, dtype=np.float32))

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
            response = self.client.embeddings.create(
                model=self.model, input=query.text, **kwargs
            )
            query_embedding = np.array(response.data[0].embedding, dtype=np.float32)

            # Calculate similarity scores
            scores = []
            for doc_embedding in self.embeddings:
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
