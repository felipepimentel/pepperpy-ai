"""Base classes for RAG strategies."""

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, TypeVar

from pepperpy_core.types import BaseConfig

from ..base import Document

T = TypeVar("T", bound="BaseRAGStrategy")


@dataclass
class RAGStrategyConfig(BaseConfig):
    """Configuration for RAG strategies.
    
    Attributes:
        chunk_size: The size of text chunks for splitting documents.
        chunk_overlap: The overlap between consecutive chunks.
        max_documents: The maximum number of documents to store.
        similarity_threshold: The minimum similarity score for retrieving documents.
        max_context_documents: The maximum number of documents to include in context.
    """

    chunk_size: int = 1000
    chunk_overlap: int = 200
    max_documents: int = 1000
    similarity_threshold: float = 0.7
    max_context_documents: int = 5
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseRAGStrategy(ABC):
    """Base class for RAG strategies.
    
    This class provides the foundation for implementing different RAG strategies.
    Each strategy can implement its own document processing, storage, and retrieval
    mechanisms.
    """

    def __init__(self, config: RAGStrategyConfig) -> None:
        """Initialize the RAG strategy.

        Args:
            config: The strategy configuration.
        """
        self.config = config
        self._documents: list[Document] = []

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the strategy.
        
        This method should perform any necessary initialization steps,
        such as loading models or setting up storage.
        """
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up resources used by the strategy.
        
        This method should clean up any resources used by the strategy,
        such as closing connections or freeing memory.
        """
        pass

    @abstractmethod
    async def process_document(self, document: Document) -> Document:
        """Process a document for storage.

        This method should prepare the document for storage by performing
        necessary operations such as chunking, embedding computation, etc.

        Args:
            document: The document to process.

        Returns:
            The processed document.
        """
        pass

    @abstractmethod
    async def add_document(self, document: Document) -> None:
        """Add a document to the strategy.

        Args:
            document: The document to add.
        """
        if len(self._documents) >= self.config.max_documents:
            raise ValueError(
                f"Maximum number of documents ({self.config.max_documents}) reached"
            )
        processed_doc = await self.process_document(document)
        self._documents.append(processed_doc)

    @abstractmethod
    async def remove_document(self, document: Document) -> None:
        """Remove a document from the strategy.

        Args:
            document: The document to remove.
        """
        try:
            self._documents.remove(document)
        except ValueError:
            pass

    @abstractmethod
    async def search(self, query: str, top_k: int = 5) -> list[Document]:
        """Search for documents similar to the query.

        Args:
            query: The search query.
            top_k: The maximum number of documents to return.

        Returns:
            A list of documents sorted by relevance.
        """
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all documents from the strategy."""
        self._documents.clear()

    @abstractmethod
    async def add_documents(self, documents: Sequence[Document]) -> None:
        """Add multiple documents to the strategy.

        Args:
            documents: The documents to add.
        """
        for document in documents:
            await self.add_document(document)

    @abstractmethod
    async def remove_documents(self, documents: Sequence[Document]) -> None:
        """Remove multiple documents from the strategy.

        Args:
            documents: The documents to remove.
        """
        for document in documents:
            await self.remove_document(document)

    @property
    def documents(self) -> list[Document]:
        """Get all stored documents.

        Returns:
            A list of all stored documents.
        """
        return self._documents.copy()
