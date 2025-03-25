"""Base classes for RAG module."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Union, Protocol, Sequence, TypeVar

from pepperpy.core import PepperpyError
from pepperpy.core.base import BaseModelContext, BaseProvider as CoreBaseProvider
from pepperpy.embeddings.base import EmbeddingProvider

T = TypeVar("T")


class RAGError(PepperpyError):
    """Base class for all RAG errors."""

    pass


class Document(Dict[str, Any]):
    """A document in the RAG system."""

    def __init__(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Initialize a document.

        Args:
            text: The document text.
            metadata: Optional metadata for the document.
        """
        super().__init__(text=text, metadata=metadata or {})

    def to_dict(self) -> Dict[str, Any]:
        """Convert the document to a dictionary.

        Returns:
            A dictionary representation of the document.
        """
        return dict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Document":
        """Create a document from a dictionary.

        Args:
            data: A dictionary containing document data.

        Returns:
            A new Document instance.
        """
        return cls(text=data["text"], metadata=data.get("metadata", {}))


class Query:
    """A search query in the RAG system."""

    def __init__(self, text: str) -> None:
        """Initialize a query.

        Args:
            text: The query text.
        """
        self.text = text

    def to_dict(self) -> Dict[str, Any]:
        """Convert the query to a dictionary.

        Returns:
            A dictionary representation of the query.
        """
        return {"text": self.text}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Query":
        """Create a query from a dictionary.

        Args:
            data: A dictionary containing query data.

        Returns:
            A new Query instance.
        """
        return cls(text=data["text"])

    def __str__(self) -> str:
        """Convert the query to a string.

        Returns:
            The query text.
        """
        return self.text


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


class BaseProvider(CoreBaseProvider, Protocol):
    """Base class for RAG providers."""

    @abstractmethod
    def add_documents(
        self,
        documents: Sequence[Dict[str, Any]],
        collection_name: Optional[str] = None,
        **kwargs: Any,
    ) -> List[str]:
        """Add documents to the vector store.

        Args:
            documents: List of documents to add.
                Each document must have at least 'text' and 'metadata' fields.
            collection_name: Optional name of the collection to add documents to.
                If not provided, uses the default collection.
            **kwargs: Additional provider-specific arguments.

        Returns:
            List of document IDs.
        """
        pass

    @abstractmethod
    def search(
        self,
        query: str,
        collection_name: Optional[str] = None,
        top_k: int = 5,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """Search for documents similar to the query.

        Args:
            query: The search query.
            collection_name: Optional name of the collection to search in.
                If not provided, uses the default collection.
            top_k: Number of results to return.
            **kwargs: Additional provider-specific arguments.

        Returns:
            List of documents sorted by relevance.
        """
        pass

    @abstractmethod
    def delete_documents(
        self,
        document_ids: Union[str, List[str]],
        collection_name: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Delete documents from the vector store.

        Args:
            document_ids: ID or list of IDs of documents to delete.
            collection_name: Optional name of the collection to delete from.
                If not provided, uses the default collection.
            **kwargs: Additional provider-specific arguments.
        """
        pass

    @abstractmethod
    def get_document(
        self,
        document_id: str,
        collection_name: Optional[str] = None,
        **kwargs: Any,
    ) -> Optional[Dict[str, Any]]:
        """Get a document by ID.

        Args:
            document_id: ID of the document to get.
            collection_name: Optional name of the collection to get from.
                If not provided, uses the default collection.
            **kwargs: Additional provider-specific arguments.

        Returns:
            The document if found, None otherwise.
        """
        pass

    @abstractmethod
    def get_documents(
        self,
        document_ids: Union[str, List[str]],
        collection_name: Optional[str] = None,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """Get multiple documents by their IDs.

        Args:
            document_ids: ID or list of IDs of documents to get.
            collection_name: Optional name of the collection to get from.
                If not provided, uses the default collection.
            **kwargs: Additional provider-specific arguments.

        Returns:
            List of documents.
        """
        pass

    @abstractmethod
    def list_documents(
        self,
        collection_name: Optional[str] = None,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """List all documents in a collection.

        Args:
            collection_name: Optional name of the collection to list.
                If not provided, uses the default collection.
            **kwargs: Additional provider-specific arguments.

        Returns:
            List of all documents.
        """
        pass

    @abstractmethod
    def clear(
        self,
        collection_name: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Clear all documents from a collection.

        Args:
            collection_name: Optional name of the collection to clear.
                If not provided, uses the default collection.
            **kwargs: Additional provider-specific arguments.
        """
        pass


class RAGContext(BaseModelContext):
    """Context for RAG operations."""

    def __init__(
        self,
        provider: BaseProvider,
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
    def provider(self) -> BaseProvider:
        """Get the RAG provider instance."""
        return self.model

    def add_documents(
        self,
        documents: Union[Document, List[Document]],
        **kwargs: Any,
    ) -> List[str]:
        """Add documents to the provider.

        Args:
            documents: A document or list of documents to add.
            **kwargs: Additional provider-specific arguments.

        Returns:
            List of document IDs.
        """
        if isinstance(documents, Document):
            documents = [documents]
        return self.provider.add_documents([dict(doc) for doc in documents], **kwargs)

    def search(
        self,
        query: Union[str, Query],
        top_k: int = 5,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """Search for documents similar to the query.

        Args:
            query: The search query.
            top_k: Number of results to return.
            **kwargs: Additional provider-specific arguments.

        Returns:
            List of documents sorted by relevance.
        """
        if isinstance(query, Query):
            query = str(query)
        return self.provider.search(query, top_k=top_k, **kwargs)

    def delete_documents(
        self,
        document_ids: Union[str, List[str]],
        **kwargs: Any,
    ) -> None:
        """Delete documents from the provider.

        Args:
            document_ids: A document ID or list of document IDs to delete.
            **kwargs: Additional provider-specific arguments.
        """
        self.provider.delete_documents(document_ids, **kwargs)

    def get_documents(
        self,
        document_ids: Union[str, List[str]],
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """Get documents by their IDs.

        Args:
            document_ids: A document ID or list of document IDs to retrieve.
            **kwargs: Additional provider-specific arguments.

        Returns:
            List of documents.
        """
        return self.provider.get_documents(document_ids, **kwargs)

    def list_documents(self, **kwargs: Any) -> List[Dict[str, Any]]:
        """List all documents in the provider.

        Args:
            **kwargs: Additional provider-specific arguments.

        Returns:
            List of all documents.
        """
        return self.provider.list_documents(**kwargs)

    def clear(self, **kwargs: Any) -> None:
        """Clear all documents from the provider.

        Args:
            **kwargs: Additional provider-specific arguments.
        """
        self.provider.clear(**kwargs)
