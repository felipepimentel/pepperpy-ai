"""Core interfaces and base classes for the RAG system."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from .types import (
    Chunk,
    Document,
    Embedding,
    RagContext,
    RagResponse,
    SearchQuery,
    SearchResult,
)


@runtime_checkable
class RagComponent(Protocol):
    """Base protocol for all RAG components."""

    @property
    def name(self) -> str:
        """Get component name."""
        ...

    @property
    def version(self) -> str:
        """Get component version."""
        ...

    @property
    def metadata(self) -> Dict[str, Any]:
        """Get component metadata."""
        ...


class BaseRagProcessor(ABC):
    """Base class for RAG processors with common functionality."""

    def __init__(self, name: str, version: str = "0.1.0"):
        self._name = name
        self._version = version
        self._metadata: Dict[str, Any] = {}

    @property
    def name(self) -> str:
        """Get processor name."""
        return self._name

    @property
    def version(self) -> str:
        """Get processor version."""
        return self._version

    @property
    def metadata(self) -> Dict[str, Any]:
        """Get processor metadata."""
        return self._metadata

    def update_metadata(self, metadata: Dict[str, Any]):
        """Update processor metadata."""
        self._metadata.update(metadata)


class Chunker(BaseRagProcessor):
    """Base class for document chunking processors."""

    @abstractmethod
    async def chunk_document(self, document: Document) -> List[Chunk]:
        """Split document into chunks."""
        raise NotImplementedError

    @abstractmethod
    async def chunk_text(
        self, text: str, metadata: Optional[Dict[str, Any]] = None
    ) -> List[Chunk]:
        """Split text into chunks."""
        raise NotImplementedError


class Embedder(BaseRagProcessor):
    """Base class for embedding processors."""

    @abstractmethod
    async def embed_chunks(self, chunks: List[Chunk]) -> List[Embedding]:
        """Generate embeddings for chunks."""
        raise NotImplementedError

    @abstractmethod
    async def embed_query(self, query: str) -> List[float]:
        """Generate embedding for search query."""
        raise NotImplementedError


class Indexer(BaseRagProcessor):
    """Base class for vector index processors."""

    @abstractmethod
    async def index_embeddings(self, embeddings: List[Embedding]):
        """Add embeddings to the index."""
        raise NotImplementedError

    @abstractmethod
    async def search(
        self, query_embedding: List[float], query: SearchQuery
    ) -> List[SearchResult]:
        """Search for similar vectors in the index."""
        raise NotImplementedError

    @abstractmethod
    async def save(self, path: str):
        """Save index to disk."""
        raise NotImplementedError

    @abstractmethod
    async def load(self, path: str):
        """Load index from disk."""
        raise NotImplementedError


class Retriever(BaseRagProcessor):
    """Base class for context retrieval processors."""

    @abstractmethod
    async def retrieve(self, query: SearchQuery) -> List[SearchResult]:
        """Retrieve relevant chunks for query."""
        raise NotImplementedError


class Augmenter(BaseRagProcessor):
    """Base class for context augmentation processors."""

    @abstractmethod
    async def augment(self, query: str, context: RagContext) -> RagResponse:
        """Augment query with retrieved context."""
        raise NotImplementedError


class RagPipeline(BaseRagProcessor):
    """Base class for end-to-end RAG pipelines."""

    def __init__(
        self,
        chunker: Chunker,
        embedder: Embedder,
        indexer: Indexer,
        retriever: Retriever,
        augmenter: Augmenter,
        name: str = "rag_pipeline",
        version: str = "0.1.0",
    ):
        super().__init__(name=name, version=version)
        self.chunker = chunker
        self.embedder = embedder
        self.indexer = indexer
        self.retriever = retriever
        self.augmenter = augmenter

    @abstractmethod
    async def process(
        self, query: str, metadata: Optional[Dict[str, Any]] = None
    ) -> RagResponse:
        """Process query through the RAG pipeline."""
        raise NotImplementedError

    @abstractmethod
    async def index_document(self, document: Document):
        """Index a document for future retrieval."""
        raise NotImplementedError
