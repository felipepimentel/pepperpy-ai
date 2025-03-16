"""Domain models for the RAG module.

This module provides the core domain models used throughout the RAG module,
including document representation, metadata, chunking, transformation, vector storage,
and other related models.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, TypeVar

from pepperpy.interfaces import Identifiable

# Type variables
T = TypeVar("T")

#
# Document Models
#


@dataclass
class Metadata:
    """Metadata for a document.

    Attributes:
        source: The source of the document
        created_at: The creation time of the document
        author: The author of the document
        title: The title of the document
        tags: Tags for the document
        custom: Custom metadata
    """

    source: Optional[str] = None
    created_at: Optional[datetime] = None
    author: Optional[str] = None
    title: Optional[str] = None
    tags: Set[str] = field(default_factory=set)
    custom: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the metadata to a dictionary.

        Returns:
            The metadata as a dictionary
        """
        return {
            "source": self.source,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "author": self.author,
            "title": self.title,
            "tags": list(self.tags),
            "custom": self.custom,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Metadata":
        """Create metadata from a dictionary.

        Args:
            data: The dictionary to create the metadata from

        Returns:
            The created metadata
        """
        created_at = data.get("created_at")
        if created_at and isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at)
            except ValueError:
                created_at = None

        return cls(
            source=data.get("source"),
            created_at=created_at,
            author=data.get("author"),
            title=data.get("title"),
            tags=set(data.get("tags", [])),
            custom=data.get("custom", {}),
        )


@dataclass
class Document(Identifiable):
    """A document for RAG.

    Attributes:
        content: The content of the document
        metadata: Metadata for the document
        id: The ID of the document
    """

    content: str
    metadata: Metadata = field(default_factory=Metadata)
    id: str = field(default="")

    def __post_init__(self) -> None:
        """Initialize the document."""
        if not self.id:
            self.id = self._generate_id()

    def _generate_id(self) -> str:
        """Generate an ID for the document.

        Returns:
            The generated ID
        """
        # Create a hash of the content and metadata
        content_hash = hashlib.sha256(self.content.encode()).hexdigest()
        metadata_hash = hashlib.sha256(
            json.dumps(self.metadata.to_dict(), sort_keys=True).encode()
        ).hexdigest()

        return f"{content_hash[:8]}-{metadata_hash[:8]}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert the document to a dictionary.

        Returns:
            The document as a dictionary
        """
        return {
            "id": self.id,
            "content": self.content,
            "metadata": self.metadata.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Document":
        """Create a document from a dictionary.

        Args:
            data: The dictionary to create the document from

        Returns:
            The created document
        """
        return cls(
            id=data.get("id", ""),
            content=data.get("content", ""),
            metadata=Metadata.from_dict(data.get("metadata", {})),
        )


@dataclass
class DocumentChunk(Identifiable):
    """A chunk of a document for RAG.

    Attributes:
        content: The content of the chunk
        metadata: Metadata for the chunk
        document_id: The ID of the document this chunk belongs to
        chunk_index: The index of this chunk in the document
        id: The ID of the chunk
    """

    content: str
    metadata: Metadata
    document_id: str
    chunk_index: int = 0
    id: str = field(default="")

    def __post_init__(self) -> None:
        """Initialize the document chunk."""
        if not self.id:
            self.id = self._generate_id()

    def _generate_id(self) -> str:
        """Generate an ID for the document chunk.

        Returns:
            The generated ID
        """
        # Create a hash of the content, document ID, and chunk index
        content_hash = hashlib.sha256(self.content.encode()).hexdigest()

        return f"{self.document_id}-{self.chunk_index}-{content_hash[:8]}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert the document chunk to a dictionary.

        Returns:
            The document chunk as a dictionary
        """
        return {
            "id": self.id,
            "content": self.content,
            "metadata": self.metadata.to_dict(),
            "document_id": self.document_id,
            "chunk_index": self.chunk_index,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocumentChunk":
        """Create a document chunk from a dictionary.

        Args:
            data: The dictionary to create the document chunk from

        Returns:
            The created document chunk
        """
        return cls(
            id=data.get("id", ""),
            content=data.get("content", ""),
            metadata=Metadata.from_dict(data.get("metadata", {})),
            document_id=data.get("document_id", ""),
            chunk_index=data.get("chunk_index", 0),
        )


#
# Chunking Models
#


class ChunkingStrategy(Enum):
    """Strategies for chunking documents."""

    FIXED_SIZE = "fixed_size"  # Fixed-size chunks with optional overlap
    SENTENCE = "sentence"  # Sentence-based chunking
    PARAGRAPH = "paragraph"  # Paragraph-based chunking
    SEMANTIC = "semantic"  # Semantic-based chunking using embeddings
    HIERARCHICAL = "hierarchical"  # Hierarchical chunking (nested chunks)
    SLIDING_WINDOW = "sliding_window"  # Sliding window with configurable stride
    CUSTOM = "custom"  # Custom chunking using a provided function


@dataclass
class ChunkingConfig:
    """Configuration for document chunking.

    This class defines the configuration for document chunking, including
    chunk size, overlap, and strategy-specific parameters.
    """

    strategy: ChunkingStrategy = ChunkingStrategy.FIXED_SIZE
    chunk_size: int = 1000  # Default chunk size in characters or tokens
    chunk_overlap: int = 200  # Default overlap between chunks
    separator: str = " "  # Separator to use when joining text
    keep_separator: bool = True  # Whether to keep separators in chunks
    respect_sentence_boundaries: bool = True  # Try to avoid breaking sentences
    respect_paragraph_boundaries: bool = True  # Try to avoid breaking paragraphs
    min_chunk_size: int = 100  # Minimum chunk size to avoid tiny chunks

    # Additional parameters for specific strategies
    params: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the chunking configuration to a dictionary.

        Returns:
            The chunking configuration as a dictionary
        """
        return {
            "strategy": self.strategy.value,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "separator": self.separator,
            "keep_separator": self.keep_separator,
            "respect_sentence_boundaries": self.respect_sentence_boundaries,
            "respect_paragraph_boundaries": self.respect_paragraph_boundaries,
            "min_chunk_size": self.min_chunk_size,
            "params": self.params,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChunkingConfig":
        """Create chunking configuration from a dictionary.

        Args:
            data: The dictionary to create the chunking configuration from

        Returns:
            The created chunking configuration
        """
        strategy_value = data.get("strategy", ChunkingStrategy.FIXED_SIZE.value)
        strategy = ChunkingStrategy(strategy_value)

        return cls(
            strategy=strategy,
            chunk_size=data.get("chunk_size", 1000),
            chunk_overlap=data.get("chunk_overlap", 200),
            separator=data.get("separator", " "),
            keep_separator=data.get("keep_separator", True),
            respect_sentence_boundaries=data.get("respect_sentence_boundaries", True),
            respect_paragraph_boundaries=data.get("respect_paragraph_boundaries", True),
            min_chunk_size=data.get("min_chunk_size", 100),
            params=data.get("params", {}),
        )


@dataclass
class ChunkMetadata:
    """Metadata for a document chunk.

    This class defines the metadata for a document chunk, including
    information about the chunking process and the original document.
    """

    strategy: ChunkingStrategy
    chunk_size: int
    chunk_overlap: int
    chunk_index: int
    total_chunks: int
    original_document_id: str
    custom: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the chunk metadata to a dictionary.

        Returns:
            The chunk metadata as a dictionary
        """
        return {
            "strategy": self.strategy.value,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "chunk_index": self.chunk_index,
            "total_chunks": self.total_chunks,
            "original_document_id": self.original_document_id,
            "custom": self.custom,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChunkMetadata":
        """Create chunk metadata from a dictionary.

        Args:
            data: The dictionary to create the chunk metadata from

        Returns:
            The created chunk metadata
        """
        strategy_value = data.get("strategy", ChunkingStrategy.FIXED_SIZE.value)
        strategy = ChunkingStrategy(strategy_value)

        return cls(
            strategy=strategy,
            chunk_size=data.get("chunk_size", 0),
            chunk_overlap=data.get("chunk_overlap", 0),
            chunk_index=data.get("chunk_index", 0),
            total_chunks=data.get("total_chunks", 0),
            original_document_id=data.get("original_document_id", ""),
            custom=data.get("custom", {}),
        )


#
# Transformation Models
#


class TransformationType(Enum):
    """Types of document transformations."""

    CLEAN_TEXT = "clean_text"  # Basic text cleaning
    REMOVE_HTML = "remove_html"  # HTML tag removal
    NORMALIZE_WHITESPACE = "normalize_whitespace"  # Normalize whitespace
    CLEAN_MARKDOWN = "clean_markdown"  # Markdown formatting removal
    CUSTOM = "custom"  # Custom transformation using a provided function


@dataclass
class TransformationConfig:
    """Configuration for document transformation.

    This class defines the configuration for document transformation, including
    the types of transformations to apply and any custom transformations.
    """

    types: List[TransformationType] = field(
        default_factory=lambda: [
            TransformationType.CLEAN_TEXT,
            TransformationType.REMOVE_HTML,
        ]
    )
    preserve_original_content: bool = True
    custom_transformations: Dict[str, Callable[[str], str]] = field(
        default_factory=dict
    )
    params: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the transformation configuration to a dictionary.

        Returns:
            The transformation configuration as a dictionary
        """
        return {
            "types": [t.value for t in self.types],
            "preserve_original_content": self.preserve_original_content,
            "params": self.params,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TransformationConfig":
        """Create transformation configuration from a dictionary.

        Args:
            data: The dictionary to create the transformation configuration from

        Returns:
            The created transformation configuration
        """
        types_values = data.get(
            "types",
            [
                TransformationType.CLEAN_TEXT.value,
                TransformationType.REMOVE_HTML.value,
            ],
        )
        types = [TransformationType(t) for t in types_values]

        return cls(
            types=types,
            preserve_original_content=data.get("preserve_original_content", True),
            params=data.get("params", {}),
        )


#
# Metadata Models
#


class MetadataType(Enum):
    """Types of metadata extraction."""

    BASIC = "basic"  # Basic metadata (title, author, etc.)
    HTML = "html"  # Metadata extraction from HTML
    PDF = "pdf"  # Metadata extraction from PDF
    TEXT = "text"  # Basic text statistics
    NLP = "nlp"  # NLP-based metadata extraction
    CUSTOM = "custom"  # Custom metadata extraction


@dataclass
class MetadataExtractorConfig:
    """Configuration for metadata extraction.

    This class defines the configuration for metadata extraction, including
    the types of metadata to extract and any custom extractors.
    """

    types: List[MetadataType] = field(
        default_factory=lambda: [
            MetadataType.BASIC,
            MetadataType.TEXT,
        ]
    )
    confidence_threshold: float = 0.5
    params: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the metadata extractor configuration to a dictionary.

        Returns:
            The metadata extractor configuration as a dictionary
        """
        return {
            "types": [t.value for t in self.types],
            "confidence_threshold": self.confidence_threshold,
            "params": self.params,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MetadataExtractorConfig":
        """Create metadata extractor configuration from a dictionary.

        Args:
            data: The dictionary to create the metadata extractor configuration from

        Returns:
            The created metadata extractor configuration
        """
        types_values = data.get(
            "types",
            [
                MetadataType.BASIC.value,
                MetadataType.TEXT.value,
            ],
        )
        types = [MetadataType(t) for t in types_values]

        return cls(
            types=types,
            confidence_threshold=data.get("confidence_threshold", 0.5),
            params=data.get("params", {}),
        )


#
# Vector Storage Models
#


@dataclass
class VectorEmbedding:
    """A vector embedding for a document chunk.

    Attributes:
        vector: The vector embedding
        document_id: The ID of the document this embedding belongs to
        chunk_id: The ID of the document chunk this embedding belongs to
        metadata: Additional metadata for the embedding
        document: Optional reference to the full document
    """

    vector: List[float]
    document_id: str
    chunk_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    document: Optional[Document] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the vector embedding to a dictionary.

        Returns:
            The vector embedding as a dictionary
        """
        return {
            "vector": self.vector,
            "document_id": self.document_id,
            "chunk_id": self.chunk_id,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VectorEmbedding":
        """Create a vector embedding from a dictionary.

        Args:
            data: The dictionary to create the vector embedding from

        Returns:
            The created vector embedding
        """
        return cls(
            vector=data.get("vector", []),
            document_id=data.get("document_id", ""),
            chunk_id=data.get("chunk_id", ""),
            metadata=data.get("metadata", {}),
        )


@dataclass
class ScoredChunk:
    """A document chunk with a similarity score.

    Attributes:
        chunk: The document chunk
        score: The similarity score
    """

    chunk: DocumentChunk
    score: float


#
# Result Models
#


@dataclass
class RetrievalResult:
    """Result of a retrieval operation.

    Attributes:
        chunks: The retrieved document chunks
        query: The query used for retrieval
        metadata: Additional metadata about the retrieval
    """

    chunks: List[ScoredChunk]
    query: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RerankingResult:
    """Result of a reranking operation.

    Attributes:
        chunks: The reranked document chunks
        query: The query used for reranking
        original_chunks: The original chunks before reranking
        metadata: Additional metadata about the reranking
    """

    chunks: List[ScoredChunk]
    query: str
    original_chunks: List[ScoredChunk]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GenerationResult:
    """Result of a generation operation.

    Attributes:
        text: The generated text
        chunks: The document chunks used for generation
        query: The query used for generation
        metadata: Additional metadata about the generation
    """

    text: str
    chunks: List[ScoredChunk]
    query: str
    metadata: Dict[str, Any] = field(default_factory=dict)
