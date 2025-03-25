"""Base RAG module."""

from typing import List, Protocol, TypeVar

from pepperpy.rag.types import Document, Query

T = TypeVar("T")


class BaseProvider(Protocol):
    """Protocol for RAG providers."""

    async def initialize(self) -> None:
        """Initialize the provider."""
        ...

    async def cleanup(self) -> None:
        """Clean up resources."""
        ...

    async def store(self, documents: List[Document]) -> None:
        """Store documents in the RAG context.

        Args:
            documents: List of documents to store.
        """
        ...

    async def search(self, query: Query) -> List[Document]:
        """Search for relevant documents.

        Args:
            query: Search query.

        Returns:
            List of relevant documents.
        """
        ...


class RAGContext:
    """Context for RAG operations."""

    def __init__(self, provider: BaseProvider) -> None:
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
