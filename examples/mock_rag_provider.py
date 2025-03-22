"""Mock RAG provider for testing.

This module provides a simple mock implementation of the RAG provider interface
for testing purposes.
"""

from typing import Any, List, Optional, Sequence

from pepperpy.rag import Document, Query, RAGProvider, RetrievalResult


class MockRAGProvider(RAGProvider):
    """Mock implementation of the RAG provider interface."""

    name = "mock"

    def __init__(self) -> None:
        """Initialize the mock RAG provider."""
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
        # Filter documents by metadata if filters are specified
        filtered_docs = self.documents
        if query.metadata:
            filtered_docs = [
                doc
                for doc in filtered_docs
                if doc.metadata
                and all(doc.metadata.get(k) == v for k, v in query.metadata.items())
            ]

        # Return all documents with score 1.0
        filtered_docs = filtered_docs[:limit]
        return RetrievalResult(
            query=query,
            documents=filtered_docs,
            scores=[1.0] * len(filtered_docs),
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
