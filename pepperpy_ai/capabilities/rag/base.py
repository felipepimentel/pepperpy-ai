"""Base classes for RAG (Retrieval Augmented Generation) capabilities."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from pepperpy_core.responses import AIResponse
from pepperpy_core.providers import BaseProvider

from ..base import BaseCapability, BaseConfig


@dataclass
class Document:
    """A document for RAG.
    
    Attributes:
        id: The document identifier.
        content: The document content.
        metadata: Additional metadata for the document.
        embedding: Optional document embedding.
    """

    id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None


@runtime_checkable
class DocumentStore(Protocol):
    """Protocol for document storage backends."""

    async def add_document(self, document: Document) -> None:
        """Add a document to the store.

        Args:
            document: The document to add.
        """
        ...

    async def remove_document(self, document_id: str) -> None:
        """Remove a document from the store.

        Args:
            document_id: The ID of the document to remove.
        """
        ...

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
        ...

    async def clear(self) -> None:
        """Clear all documents from the store."""
        ...


@dataclass
class RAGConfig(BaseConfig):
    """Configuration for RAG capabilities.
    
    Attributes:
        prompt_template: Template for generating prompts with retrieved documents.
        max_documents: Maximum number of documents to use in generation.
        metadata: Additional metadata for the RAG system.
    """

    prompt_template: str = (
        "Based on the following documents:\n\n{documents}\n\n"
        "Please answer the following question:\n\n{query}"
    )
    max_documents: int = 5
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseRAG(BaseCapability, ABC):
    """Base class for RAG capabilities."""

    def __init__(self, config: RAGConfig, provider: BaseProvider) -> None:
        """Initialize the RAG capability.

        Args:
            config: The RAG configuration.
            provider: The AI provider to use for generation.
        """
        super().__init__(config, provider)
        self.config = config

    @abstractmethod
    async def add_document(self, document: Document) -> None:
        """Add a document to the RAG system.

        Args:
            document: The document to add.
        """
        pass

    @abstractmethod
    async def remove_document(self, document_id: str) -> None:
        """Remove a document from the RAG system.

        Args:
            document_id: The ID of the document to remove.
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all documents from the RAG system."""
        pass 