"""Base RAG module."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from pepperpy_ai.responses import AIResponse
from pepperpy_ai.providers.base import BaseProvider


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


@dataclass
class RAGConfig:
    """Configuration for RAG capabilities.
    
    Attributes:
        name: Configuration name
        description: Configuration description
        prompt_template: Template for generating prompts with retrieved documents.
        max_documents: Maximum number of documents to use in generation.
        metadata: Additional metadata for the RAG system.
    """

    name: str
    description: str
    prompt_template: str = (
        "Based on the following documents:\n\n{documents}\n\n"
        "Please answer the following question:\n\n{query}"
    )
    max_documents: int = 5
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseRAG(ABC):
    """Base class for RAG implementations."""
    
    def __init__(self, config: RAGConfig, provider: BaseProvider) -> None:
        """Initialize the RAG system.

        Args:
            config: The RAG configuration.
            provider: The AI provider to use for generation.
        """
        self.config = config
        self.provider = provider
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the RAG system."""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up resources."""
        pass
    
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