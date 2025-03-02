"""Public interface for retrieval systems.

This module provides a stable public interface for retrieval systems
used in RAG (Retrieval Augmented Generation). It exposes the core
retrieval abstractions and implementations that are considered part
of the public API.

Classes:
    Retriever: Base class for retrieval systems
    VectorRetriever: Vector-based retrieval implementation
    Document: Represents a document in the retrieval system
    SearchResult: Result from a retrieval operation
    SearchQuery: Query for retrieval operations
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union


@dataclass
class Document:
    """Represents a document in the retrieval system.

    Attributes:
        id: Unique identifier for the document
        content: The content of the document
        metadata: Additional metadata about the document
    """

    id: str
    content: str
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        """Initialize default values."""
        if self.metadata is None:
            self.metadata = {}


@dataclass
class SearchQuery:
    """Query for retrieval operations.

    Attributes:
        query: The query text
        top_k: Number of results to return
        filters: Metadata filters to apply
    """

    query: str
    top_k: int = 5
    filters: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Initialize default values."""
        if self.filters is None:
            self.filters = {}


@dataclass
class SearchResult:
    """Result from a retrieval operation.

    Attributes:
        document: The retrieved document
        score: Relevance score for the document
        metadata: Additional metadata about the result
    """

    document: Document
    score: float
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        """Initialize default values."""
        if self.metadata is None:
            self.metadata = {}


class Retriever:
    """Base class for retrieval systems.

    This class defines the interface for retrieval systems used in RAG.
    Subclasses should implement the search method to provide specific
    retrieval functionality.
    """

    def __init__(self, name: str, description: str = ""):
        """Initialize the retriever.

        Args:
            name: Human-readable name for the retriever
            description: Description of the retriever's functionality
        """
        self.name = name
        self.description = description

    async def search(self, query: Union[str, SearchQuery]) -> List[SearchResult]:
        """Search for documents matching the query.

        Args:
            query: The search query or query object

        Returns:
            List of search results

        Raises:
            NotImplementedError: If the subclass does not implement this method
        """
        raise NotImplementedError("Subclasses must implement search method")

    async def add_documents(self, documents: List[Document]) -> None:
        """Add documents to the retrieval system.

        Args:
            documents: The documents to add

        Raises:
            NotImplementedError: If the subclass does not implement this method
        """
        raise NotImplementedError("Subclasses must implement add_documents method")

    async def delete_documents(self, document_ids: List[str]) -> None:
        """Delete documents from the retrieval system.

        Args:
            document_ids: The IDs of the documents to delete

        Raises:
            NotImplementedError: If the subclass does not implement this method
        """
        raise NotImplementedError("Subclasses must implement delete_documents method")


class VectorRetriever(Retriever):
    """Vector-based retrieval implementation.

    This class provides a retrieval system based on vector embeddings.
    It uses similarity search to find documents matching a query.
    """

    def __init__(
        self,
        name: str,
        embedding_provider: Any,
        vector_store: Any,
        description: str = "",
    ):
        """Initialize the vector retriever.

        Args:
            name: Human-readable name for the retriever
            embedding_provider: Provider for generating embeddings
            vector_store: Storage for vector embeddings
            description: Description of the retriever's functionality
        """
        super().__init__(name, description)
        self.embedding_provider = embedding_provider
        self.vector_store = vector_store

    async def search(self, query: Union[str, SearchQuery]) -> List[SearchResult]:
        """Search for documents matching the query.

        Args:
            query: The search query or query object

        Returns:
            List of search results
        """
        # Convert string query to SearchQuery if needed
        if isinstance(query, str):
            query = SearchQuery(query=query)

        # Generate embedding for the query
        query_embedding = await self.embedding_provider.embed(query.query)

        # Search the vector store
        results = await self.vector_store.search(
            query_embedding,
            top_k=query.top_k,
            filters=query.filters,
        )

        # Convert to SearchResult objects
        return [
            SearchResult(
                document=Document(
                    id=result["id"],
                    content=result["content"],
                    metadata=result.get("metadata", {}),
                ),
                score=result["score"],
            )
            for result in results
        ]

    async def add_documents(self, documents: List[Document]) -> None:
        """Add documents to the retrieval system.

        Args:
            documents: The documents to add
        """
        # Generate embeddings for the documents
        embeddings = []
        for document in documents:
            embedding = await self.embedding_provider.embed(document.content)
            embeddings.append(embedding)

        # Add to the vector store
        await self.vector_store.add(
            documents=[
                {
                    "id": doc.id,
                    "content": doc.content,
                    "metadata": doc.metadata,
                    "embedding": embedding,
                }
                for doc, embedding in zip(documents, embeddings)
            ]
        )

    async def delete_documents(self, document_ids: List[str]) -> None:
        """Delete documents from the retrieval system.

        Args:
            document_ids: The IDs of the documents to delete
        """
        await self.vector_store.delete(document_ids)


# Export public classes
__all__ = [
    "Document",
    "SearchQuery",
    "SearchResult",
    "Retriever",
    "VectorRetriever",
]
