"""Base classes for the retrieval components of the RAG system.

This module provides the base classes and interfaces for the retrieval components.
"""

from abc import abstractmethod
from typing import Dict, List, Optional

from pepperpy.core.logging import get_logger
from pepperpy.rag.base import RagComponent
from pepperpy.rag.indexing.base import Indexer
from pepperpy.rag.types import RagComponentType, RagContext, SearchQuery, SearchResult

logger = get_logger(__name__)


class Retriever(RagComponent):
    """Base class for retrieval components."""

    component_type = RagComponentType.RETRIEVER

    @abstractmethod
    async def retrieve(self, query: SearchQuery) -> List[SearchResult]:
        """Retrieve relevant chunks for a query.

        Args:
            query: The search query

        Returns:
            A list of search results

        """


class SimilarityRetriever(Retriever):
    """Retriever that uses vector similarity to find relevant chunks."""

    def __init__(
        self, component_id: str, name: str, indexer: Indexer, description: str = "",
    ):
        """Initialize the similarity retriever.

        Args:
            component_id: Unique identifier for the component
            name: Human-readable name for the component
            indexer: The indexer to use for retrieval
            description: Description of the component's functionality

        """
        super().__init__(component_id, name, description)
        self.indexer = indexer

    async def initialize(self) -> None:
        """Initialize the similarity retriever."""
        logger.info(f"Initializing similarity retriever: {self.name}")
        await self.indexer.initialize()
        await super().initialize()

    async def cleanup(self) -> None:
        """Clean up the similarity retriever."""
        logger.info(f"Cleaning up similarity retriever: {self.name}")
        await self.indexer.cleanup()
        await super().cleanup()


class RetrievalManager(RagComponent):
    """Manager for retrieval operations."""

    component_type = RagComponentType.RETRIEVAL_MANAGER

    def __init__(self, component_id: str, name: str, description: str = ""):
        """Initialize the retrieval manager.

        Args:
            component_id: Unique identifier for the component
            name: Human-readable name for the component
            description: Description of the component's functionality

        """
        super().__init__(component_id, name, description)
        self.retrievers: Dict[str, Retriever] = {}
        self.default_retriever: Optional[str] = None

    def add_retriever(self, retriever: Retriever, set_as_default: bool = False) -> None:
        """Add a retriever to the manager.

        Args:
            retriever: The retriever to add
            set_as_default: Whether to set this retriever as the default

        """
        self.retrievers[retriever.component_id] = retriever
        logger.debug(f"Added retriever {retriever.name} to manager {self.name}")

        if set_as_default or self.default_retriever is None:
            self.default_retriever = retriever.component_id
            logger.debug(f"Set {retriever.name} as default retriever")

    def get_retriever(self, retriever_id: str) -> Optional[Retriever]:
        """Get a retriever by ID.

        Args:
            retriever_id: The ID of the retriever to get

        Returns:
            The retriever if found, None otherwise

        """
        return self.retrievers.get(retriever_id)

    async def initialize(self) -> None:
        """Initialize all retrievers."""
        logger.info(f"Initializing retrieval manager: {self.name}")
        for retriever in self.retrievers.values():
            await retriever.initialize()
        await super().initialize()

    async def cleanup(self) -> None:
        """Clean up all retrievers."""
        logger.info(f"Cleaning up retrieval manager: {self.name}")
        for retriever in self.retrievers.values():
            await retriever.cleanup()
        await super().cleanup()

    async def retrieve(
        self, query: SearchQuery, retriever_id: Optional[str] = None,
    ) -> RagContext:
        """Retrieve relevant chunks using the specified retriever or the default.

        Args:
            query: The search query
            retriever_id: The ID of the retriever to use, or None to use the default

        Returns:
            A RAG context containing the query and search results

        """
        if retriever_id is None:
            if self.default_retriever is None:
                raise ValueError("No default retriever set")
            retriever_id = self.default_retriever

        retriever = self.get_retriever(retriever_id)
        if retriever is None:
            raise ValueError(f"Retriever not found: {retriever_id}")

        results = await retriever.retrieve(query)
        return RagContext(query=query, results=results)
