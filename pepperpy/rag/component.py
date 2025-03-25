"""RAG component module."""

from typing import List, Optional

from pepperpy.core.base import BaseComponent
from pepperpy.core.config import Config
from pepperpy.rag import Document, Query
from pepperpy.rag.base import BaseProvider as RAGProvider


class RAGComponent(BaseComponent):
    """RAG component for retrieval augmented generation."""

    def __init__(self, config: Config) -> None:
        """Initialize RAG component.

        Args:
            config: Configuration instance
        """
        super().__init__()
        self.config = config
        self._provider: Optional[RAGProvider] = None
        self._collection_name: Optional[str] = None
        self._persist_directory: Optional[str] = None

    def configure(self, collection_name: str, persist_directory: str) -> "RAGComponent":
        """Configure the RAG component.

        Args:
            collection_name: Name of the collection
            persist_directory: Directory to persist data

        Returns:
            Self for chaining
        """
        self._collection_name = collection_name
        self._persist_directory = persist_directory
        return self

    async def _initialize(self) -> None:
        """Initialize the RAG provider."""
        if not self._collection_name or not self._persist_directory:
            raise ValueError(
                "RAG component must be configured with collection_name and persist_directory"
            )
        self._provider = self.config.load_rag_provider(
            collection_name=self._collection_name,
            persist_directory=self._persist_directory,
        )
        await self._provider.initialize()

    async def _cleanup(self) -> None:
        """Clean up resources."""
        if self._provider:
            await self._provider.cleanup()

    async def add_documents(self, documents: List[Document]) -> None:
        """Add documents to the RAG context.

        Args:
            documents: List of documents to add
        """
        if not self._provider:
            await self.initialize()
        await self._provider.store(documents)

    async def search(self, query: Query) -> List[Document]:
        """Search for relevant documents.

        Args:
            query: Search query

        Returns:
            List of relevant documents
        """
        if not self._provider:
            await self.initialize()
        return await self._provider.search(query)
