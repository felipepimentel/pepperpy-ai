"""Base RAG module."""

from abc import abstractmethod
from typing import List, TypeVar

from pepperpy.providers import BaseProvider
from pepperpy.rag.types import Document, Query

T = TypeVar("T")


class RAGProvider(BaseProvider):
    """Base class for RAG providers."""

    @abstractmethod
    async def store(self, documents: List[Document]) -> None:
        """Store documents in the RAG context.

        Args:
            documents: List of documents to store.
        """
        pass

    @abstractmethod
    async def search(self, query: Query) -> List[Document]:
        """Search for relevant documents.

        Args:
            query: Search query.

        Returns:
            List of relevant documents.
        """
        pass


class RAGContext:
    """Context for RAG operations."""

    def __init__(self, provider: RAGProvider) -> None:
        """Initialize the RAG context.

        Args:
            provider: The RAG provider to use.
        """
        self.provider = provider

    async def initialize(self) -> None:
        """Initialize the context."""
        await self.provider.initialize()

    async def cleanup(self) -> None:
        """Clean up resources."""
        await self.provider.cleanup()

    async def add_documents(self, documents: List[Document]) -> None:
        """Add documents to the context.

        Args:
            documents: List of documents to add.
        """
        await self.provider.store(documents)

    async def search(self, query: Query) -> List[Document]:
        """Search for relevant documents.

        Args:
            query: Search query.

        Returns:
            List of relevant documents.
        """
        return await self.provider.search(query)
