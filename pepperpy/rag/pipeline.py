"""RAG pipeline implementations.

This module provides concrete implementations of RAG pipelines.
"""

from typing import Optional

from pepperpy.core.logging import get_logger
from pepperpy.rag.base import RagPipeline
from pepperpy.rag.generation import GenerationManager
from pepperpy.rag.indexing import IndexingManager
from pepperpy.rag.retrieval import RetrievalManager
from pepperpy.rag.types import RagComponentType, RagResponse, SearchQuery

logger = get_logger(__name__)


class StandardRagPipeline(RagPipeline):
    """Standard RAG pipeline implementation.

    This pipeline implements the standard RAG flow:
    1. Retrieve relevant chunks using the retrieval manager
    2. Generate a response using the generation manager
    """

    def __init__(self, component_id: str, name: str, description: str = ""):
        """Initialize the standard RAG pipeline.

        Args:
            component_id: Unique identifier for the pipeline
            name: Human-readable name for the pipeline
            description: Description of the pipeline's functionality
        """
        super().__init__(component_id, name, description)
        self._indexing_manager: Optional[IndexingManager] = None
        self._retrieval_manager: Optional[RetrievalManager] = None
        self._generation_manager: Optional[GenerationManager] = None

    @property
    def indexing_manager(self) -> IndexingManager:
        """Get the indexing manager.

        Returns:
            The indexing manager

        Raises:
            ValueError: If the indexing manager is not set
        """
        if self._indexing_manager is None:
            raise ValueError("Indexing manager not set")
        return self._indexing_manager

    @property
    def retrieval_manager(self) -> RetrievalManager:
        """Get the retrieval manager.

        Returns:
            The retrieval manager

        Raises:
            ValueError: If the retrieval manager is not set
        """
        if self._retrieval_manager is None:
            raise ValueError("Retrieval manager not set")
        return self._retrieval_manager

    @property
    def generation_manager(self) -> GenerationManager:
        """Get the generation manager.

        Returns:
            The generation manager

        Raises:
            ValueError: If the generation manager is not set
        """
        if self._generation_manager is None:
            raise ValueError("Generation manager not set")
        return self._generation_manager

    def add_component(self, component: RagPipeline) -> None:
        """Add a component to the pipeline.

        Args:
            component: The component to add
        """
        super().add_component(component)

        # Store references to manager components for convenience
        if component.component_type == RagComponentType.INDEXING_MANAGER:
            self._indexing_manager = component  # type: ignore
        elif component.component_type == RagComponentType.RETRIEVAL_MANAGER:
            self._retrieval_manager = component  # type: ignore
        elif component.component_type == RagComponentType.GENERATION_MANAGER:
            self._generation_manager = component  # type: ignore

    async def process(self, query: SearchQuery) -> RagResponse:
        """Process a query through the pipeline.

        Args:
            query: The query to process

        Returns:
            The generated response
        """
        logger.info(f"Processing query: {query.query}")

        # Retrieve relevant chunks
        context = await self.retrieval_manager.retrieve(query)
        logger.debug(f"Retrieved {len(context.results)} results")

        # Generate a response
        response = await self.generation_manager.generate(context)
        logger.debug("Generated response")

        return response
