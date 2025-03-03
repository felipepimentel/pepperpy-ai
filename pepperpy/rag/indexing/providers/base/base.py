"""Base class for indexing providers.

This module provides the base class for all indexing providers.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from pepperpy.core.logging import get_logger
from pepperpy.rag.indexing.base import Chunker, DocumentIndexer, Embedder, Indexer
from pepperpy.rag.indexing.providers.base.types import (
    IndexingProviderType,
    IndexingRequest,
    IndexingResponse,
)

logger = get_logger(__name__)


class IndexingProvider(DocumentIndexer, ABC):
    """Base class for all indexing providers."""

    def __init__(
        self,
        component_id: str,
        name: str,
        provider_type: IndexingProviderType,
        chunker: Chunker,
        embedder: Embedder,
        indexer: Indexer,
        description: str = "",
        config: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the indexing provider.

        Args:
            component_id: Unique identifier for the component
            name: Human-readable name for the component
            provider_type: The type of provider
            chunker: The chunker component to use
            embedder: The embedder component to use
            indexer: The indexer component to use
            description: Description of the component's functionality
            config: Configuration for the provider

        """
        super().__init__(component_id, name, chunker, embedder, indexer, description)
        self.provider_type = provider_type
        self.config = config or {}

    @abstractmethod
    async def process_request(self, request: IndexingRequest) -> IndexingResponse:
        """Process an indexing request.

        Args:
            request: The indexing request

        Returns:
            The indexing response

        """

    async def initialize(self) -> None:
        """Initialize the provider."""
        logger.debug(f"Initializing indexing provider: {self.component_id}")
        await super().initialize()

    async def cleanup(self) -> None:
        """Clean up the provider."""
        logger.debug(f"Cleaning up indexing provider: {self.component_id}")
        await super().cleanup()
