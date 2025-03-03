"""Chroma provider implementation.

This module provides the Chroma provider for indexing.
"""

from typing import Any, Dict, Optional

from pepperpy.core.logging import get_logger
from pepperpy.rag.indexing.base import Chunker, Embedder, Indexer
from pepperpy.rag.indexing.providers.base import (
    IndexingProvider,
    IndexingProviderType,
    IndexingRequest,
    IndexingResponse,
)

logger = get_logger(__name__)


class ChromaProvider(IndexingProvider):
    """Chroma provider for indexing."""

    def __init__(
        self,
        component_id: str,
        name: str,
        chunker: Chunker,
        embedder: Embedder,
        indexer: Indexer,
        persist_directory: str = "./chroma_db",
        description: str = "Chroma provider for indexing",
        config: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the Chroma provider.

        Args:
            component_id: Unique identifier for the component
            name: Human-readable name for the component
            chunker: The chunker component to use
            embedder: The embedder component to use
            indexer: The indexer component to use
            persist_directory: Directory to persist the Chroma database
            description: Description of the component's functionality
            config: Additional configuration for the provider

        """
        super().__init__(
            component_id,
            name,
            IndexingProviderType.CHROMA,
            chunker,
            embedder,
            indexer,
            description,
            config,
        )
        self.persist_directory = persist_directory

    async def process_request(self, request: IndexingRequest) -> IndexingResponse:
        """Process an indexing request.

        Args:
            request: The indexing request

        Returns:
            The indexing response

        """
        # Placeholder for actual implementation
        logger.info(
            f"Processing indexing request for collection: {request.collection_name}",
        )

        # Process documents if any
        for document in request.documents:
            await self.index_document(document)

        # Process chunks if any
        if request.chunks:
            embeddings = await self.embedder.embed_chunks(request.chunks)
            await self.indexer.index_embeddings(embeddings)

        return IndexingResponse(
            success=True,
            document_ids=[doc.id for doc in request.documents],
            chunk_ids=[chunk.id for chunk in request.chunks],
            metadata={"collection": request.collection_name},
        )

    async def initialize(self) -> None:
        """Initialize the provider."""
        logger.debug(f"Initializing Chroma provider: {self.component_id}")
        await super().initialize()

    async def cleanup(self) -> None:
        """Clean up the provider."""
        logger.debug(f"Cleaning up Chroma provider: {self.component_id}")
        await super().cleanup()
