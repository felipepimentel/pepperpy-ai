"""Base classes for the indexing components of the RAG system.

This module provides the base classes and interfaces for the indexing components.
"""

from abc import abstractmethod
from typing import Any, Dict, List, Optional

from pepperpy.core.logging import get_logger
from pepperpy.rag.base import RagComponent
from pepperpy.rag.types import Chunk, Document, Embedding, RagComponentType

logger = get_logger(__name__)


class Chunker(RagComponent):
    """Base class for document chunking components."""

    component_type = RagComponentType.CHUNKER

    @abstractmethod
    async def chunk_document(self, document: Document) -> List[Chunk]:
        """Split document into chunks.

        Args:
            document: The document to chunk

        Returns:
            A list of chunks
        """
        pass

    @abstractmethod
    async def chunk_text(
        self, text: str, metadata: Optional[Dict[str, Any]] = None
    ) -> List[Chunk]:
        """Split text into chunks.

        Args:
            text: The text to chunk
            metadata: Optional metadata to associate with the chunks

        Returns:
            A list of chunks
        """
        pass


class Embedder(RagComponent):
    """Base class for embedding components."""

    component_type = RagComponentType.EMBEDDER

    @abstractmethod
    async def embed_chunks(self, chunks: List[Chunk]) -> List[Embedding]:
        """Generate embeddings for chunks.

        Args:
            chunks: The chunks to embed

        Returns:
            A list of embeddings
        """
        pass

    @abstractmethod
    async def embed_query(self, query: str) -> List[float]:
        """Generate embedding for search query.

        Args:
            query: The query to embed

        Returns:
            The query embedding vector
        """
        pass


class Indexer(RagComponent):
    """Base class for indexing components."""

    component_type = RagComponentType.INDEXER

    @abstractmethod
    async def index_embeddings(self, embeddings: List[Embedding]) -> None:
        """Add embeddings to the index.

        Args:
            embeddings: The embeddings to index
        """
        pass

    @abstractmethod
    async def save(self, path: str) -> None:
        """Save index to disk.

        Args:
            path: The path to save the index to
        """
        pass

    @abstractmethod
    async def load(self, path: str) -> None:
        """Load index from disk.

        Args:
            path: The path to load the index from
        """
        pass


class DocumentIndexer(RagComponent):
    """Component that combines chunking, embedding, and indexing."""

    component_type = RagComponentType.DOCUMENT_INDEXER

    def __init__(
        self,
        component_id: str,
        name: str,
        chunker: Chunker,
        embedder: Embedder,
        indexer: Indexer,
        description: str = "",
    ):
        """Initialize the document indexer.

        Args:
            component_id: Unique identifier for the component
            name: Human-readable name for the component
            chunker: The chunker component to use
            embedder: The embedder component to use
            indexer: The indexer component to use
            description: Description of the component's functionality
        """
        super().__init__(component_id, name, description)
        self.chunker = chunker
        self.embedder = embedder
        self.indexer = indexer

    async def initialize(self) -> None:
        """Initialize the document indexer and its components."""
        logger.info(f"Initializing document indexer: {self.name}")
        await self.chunker.initialize()
        await self.embedder.initialize()
        await self.indexer.initialize()
        await super().initialize()

    async def cleanup(self) -> None:
        """Clean up the document indexer and its components."""
        logger.info(f"Cleaning up document indexer: {self.name}")
        await self.chunker.cleanup()
        await self.embedder.cleanup()
        await self.indexer.cleanup()
        await super().cleanup()

    async def index_document(self, document: Document) -> None:
        """Index a document.

        Args:
            document: The document to index
        """
        logger.debug(f"Indexing document: {document.id}")
        chunks = await self.chunker.chunk_document(document)
        embeddings = await self.embedder.embed_chunks(chunks)
        await self.indexer.index_embeddings(embeddings)

    async def index_text(
        self, text: str, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Index a text string.

        Args:
            text: The text to index
            metadata: Optional metadata to associate with the text
        """
        logger.debug("Indexing text")
        chunks = await self.chunker.chunk_text(text, metadata)
        embeddings = await self.embedder.embed_chunks(chunks)
        await self.indexer.index_embeddings(embeddings)


class IndexingManager(RagComponent):
    """Manager for indexing operations."""

    component_type = RagComponentType.INDEXING_MANAGER

    def __init__(self, component_id: str, name: str, description: str = ""):
        """Initialize the indexing manager.

        Args:
            component_id: Unique identifier for the component
            name: Human-readable name for the component
            description: Description of the component's functionality
        """
        super().__init__(component_id, name, description)
        self.indexers: Dict[str, DocumentIndexer] = {}

    def add_indexer(self, indexer: DocumentIndexer) -> None:
        """Add an indexer to the manager.

        Args:
            indexer: The indexer to add
        """
        self.indexers[indexer.component_id] = indexer
        logger.debug(f"Added indexer {indexer.name} to manager {self.name}")

    def get_indexer(self, indexer_id: str) -> Optional[DocumentIndexer]:
        """Get an indexer by ID.

        Args:
            indexer_id: The ID of the indexer to get

        Returns:
            The indexer if found, None otherwise
        """
        return self.indexers.get(indexer_id)

    async def initialize(self) -> None:
        """Initialize all indexers."""
        logger.info(f"Initializing indexing manager: {self.name}")
        for indexer in self.indexers.values():
            await indexer.initialize()
        await super().initialize()

    async def cleanup(self) -> None:
        """Clean up all indexers."""
        logger.info(f"Cleaning up indexing manager: {self.name}")
        for indexer in self.indexers.values():
            await indexer.cleanup()
        await super().cleanup()

    async def index_document(
        self, document: Document, indexer_id: Optional[str] = None
    ) -> None:
        """Index a document using the specified indexer or all indexers.

        Args:
            document: The document to index
            indexer_id: The ID of the indexer to use, or None to use all indexers
        """
        if indexer_id:
            indexer = self.get_indexer(indexer_id)
            if indexer:
                await indexer.index_document(document)
            else:
                logger.warning(f"Indexer not found: {indexer_id}")
        else:
            for indexer in self.indexers.values():
                await indexer.index_document(document)
