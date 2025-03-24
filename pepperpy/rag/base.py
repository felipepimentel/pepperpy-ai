"""Base classes for RAG module."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Union

from pepperpy.core import PepperpyError
from pepperpy.core.base import BaseModelContext
from pepperpy.embeddings.base import EmbeddingProvider


class RAGError(PepperpyError):
    """Base class for all RAG errors."""

    pass


class Document:
    """A document in the RAG system."""

    def __init__(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        embeddings: Optional[Union[List[float], List[List[float]]]] = None,
        id: Optional[str] = None,
        created_at: Optional[datetime] = None,
    ) -> None:
        """Initialize a document.

        Args:
            content: The content of the document.
            metadata: Optional metadata associated with the document.
            embeddings: Optional embeddings for the document.
            id: Optional unique identifier for the document.
            created_at: Optional creation timestamp.
        """
        self.content = content
        self.metadata = metadata or {}
        self.embeddings = embeddings
        self.id = id
        self.created_at = created_at or datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert the document to a dictionary.

        Returns:
            A dictionary representation of the document.
        """
        return {
            "content": self.content,
            "metadata": self.metadata,
            "embeddings": self.embeddings,
            "id": self.id,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Document":
        """Create a document from a dictionary.

        Args:
            data: A dictionary containing document data.

        Returns:
            A new Document instance.
        """
        return cls(
            content=data["content"],
            metadata=data.get("metadata"),
            embeddings=data.get("embeddings"),
            id=data.get("id"),
            created_at=datetime.fromisoformat(data["created_at"])
            if data.get("created_at")
            else None,
        )


class Query:
    """A query in the RAG system."""

    def __init__(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        embeddings: Optional[Union[List[float], List[List[float]]]] = None,
        id: Optional[str] = None,
        created_at: Optional[datetime] = None,
    ) -> None:
        """Initialize a query.

        Args:
            content: The content of the query.
            metadata: Optional metadata associated with the query.
            embeddings: Optional embeddings for the query.
            id: Optional unique identifier for the query.
            created_at: Optional creation timestamp.
        """
        self.content = content
        self.metadata = metadata or {}
        self.embeddings = embeddings
        self.id = id
        self.created_at = created_at or datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert the query to a dictionary.

        Returns:
            A dictionary representation of the query.
        """
        return {
            "content": self.content,
            "metadata": self.metadata,
            "embeddings": self.embeddings,
            "id": self.id,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Query":
        """Create a query from a dictionary.

        Args:
            data: A dictionary containing query data.

        Returns:
            A new Query instance.
        """
        return cls(
            content=data["content"],
            metadata=data.get("metadata"),
            embeddings=data.get("embeddings"),
            id=data.get("id"),
            created_at=datetime.fromisoformat(data["created_at"])
            if data.get("created_at")
            else None,
        )


class RetrievalResult:
    """A result from a retrieval operation."""

    def __init__(
        self,
        query: Query,
        documents: List[Document],
        scores: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize a retrieval result.

        Args:
            query: The query that produced this result.
            documents: The retrieved documents.
            scores: Optional relevance scores for each document.
            metadata: Optional metadata associated with the result.
        """
        self.query = query
        self.documents = documents
        self.scores = scores
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary.

        Returns:
            A dictionary representation of the result.
        """
        return {
            "query": self.query.to_dict(),
            "documents": [doc.to_dict() for doc in self.documents],
            "scores": self.scores,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RetrievalResult":
        """Create a result from a dictionary.

        Args:
            data: A dictionary containing result data.

        Returns:
            A new RetrievalResult instance.
        """
        return cls(
            query=Query.from_dict(data["query"]),
            documents=[Document.from_dict(doc) for doc in data["documents"]],
            scores=data.get("scores"),
            metadata=data.get("metadata"),
        )


class BaseRAGProvider(ABC):
    """Base class for RAG providers."""

    def __init__(self, embedding_provider: Optional[EmbeddingProvider] = None) -> None:
        """Initialize the provider.

        Args:
            embedding_provider: Optional provider for generating embeddings.
        """
        self.embedding_provider = embedding_provider

    @abstractmethod
    async def add_documents(
        self, documents: Union[Document, List[Document]]
    ) -> List[Document]:
        """Add documents to the provider.

        Args:
            documents: A document or list of documents to add.

        Returns:
            The added documents.

        Raises:
            RAGError: If there is an error adding the documents.
        """
        pass

    @abstractmethod
    async def search(
        self,
        query: Query,
        limit: int = 10,
        min_score: Optional[float] = None,
        **kwargs: Any,
    ) -> RetrievalResult:
        """Search for documents similar to the query.

        Args:
            query: The query to search for.
            limit: Maximum number of results to return.
            min_score: Minimum similarity score for results.
            **kwargs: Additional provider-specific arguments.

        Returns:
            A RetrievalResult containing the query and matching documents.

        Raises:
            RAGError: If there is an error performing the search.
        """
        pass

    @abstractmethod
    async def delete_documents(self, document_ids: Union[str, List[str]]) -> None:
        """Delete documents from the provider.

        Args:
            document_ids: A document ID or list of document IDs to delete.

        Raises:
            RAGError: If there is an error deleting the documents.
        """
        pass

    @abstractmethod
    async def get_documents(
        self, document_ids: Union[str, List[str]]
    ) -> List[Document]:
        """Get documents by their IDs.

        Args:
            document_ids: A document ID or list of document IDs to retrieve.

        Returns:
            The requested documents.

        Raises:
            RAGError: If there is an error retrieving the documents.
        """
        pass

    @abstractmethod
    async def list_documents(self) -> List[Document]:
        """List all documents in the provider.

        Returns:
            All documents in the provider.

        Raises:
            RAGError: If there is an error listing the documents.
        """
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all documents from the provider.

        Raises:
            RAGError: If there is an error clearing the documents.
        """
        pass


class RAGContext(BaseModelContext):
    """Context for RAG operations."""

    def __init__(
        self,
        provider: BaseRAGProvider,
        embedding_provider: Optional[EmbeddingProvider] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the RAG context.

        Args:
            provider: The RAG provider instance.
            embedding_provider: Optional embedding provider.
            context: Optional context dictionary.
        """
        super().__init__(provider, context)
        self.embedding_provider = embedding_provider

    @property
    def provider(self) -> BaseRAGProvider:
        """Get the RAG provider instance."""
        return self.model

    async def add_documents(
        self, documents: Union[Document, list[Document]]
    ) -> list[Document]:
        """Add documents to the provider.

        Args:
            documents: A document or list of documents to add.

        Returns:
            The added documents.
        """
        if isinstance(documents, Document):
            documents = [documents]

        # If we have an embedding provider, generate embeddings for documents
        # that don't have them
        if self.embedding_provider:
            for doc in documents:
                if not doc.embeddings:
                    content = doc.content
                    doc.embeddings = await self.embedding_provider.embed_text(content)

        return await self.provider.add_documents(documents)

    async def search(
        self,
        query: Union[str, Query],
        limit: int = 10,
        min_score: Optional[float] = None,
        **kwargs: Any,
    ) -> RetrievalResult:
        """Search for documents similar to the query.

        Args:
            query: The query string or Query object.
            limit: Maximum number of results to return.
            min_score: Minimum similarity score for results.
            **kwargs: Additional provider-specific arguments.

        Returns:
            A RetrievalResult containing the query and matching documents.
        """
        if isinstance(query, str):
            query = Query(content=query)

        # If we have an embedding provider and the query doesn't have embeddings,
        # generate them
        if self.embedding_provider and not query.embeddings:
            query.embeddings = await self.embedding_provider.embed_text(query.content)

        return await self.provider.search(query, limit, min_score, **kwargs)

    async def delete_documents(self, document_ids: Union[str, list[str]]) -> None:
        """Delete documents from the provider.

        Args:
            document_ids: A document ID or list of document IDs to delete.
        """
        await self.provider.delete_documents(document_ids)

    async def get_documents(
        self, document_ids: Union[str, list[str]]
    ) -> list[Document]:
        """Get documents by their IDs.

        Args:
            document_ids: A document ID or list of document IDs to retrieve.

        Returns:
            The requested documents.
        """
        return await self.provider.get_documents(document_ids)

    async def list_documents(self) -> list[Document]:
        """List all documents in the provider.

        Returns:
            All documents in the provider.
        """
        return await self.provider.list_documents()

    async def clear(self) -> None:
        """Clear all documents from the provider."""
        await self.provider.clear()
