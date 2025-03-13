"""Domain models for the RAG module.

This module provides the core domain models used throughout the RAG module,
including document representation, metadata, chunking, transformation, and
other related models.
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
    max_chunk_size: Optional[int] = None  # Maximum chunk size (None = no limit)
    custom_chunker: Optional[Callable[[str, "ChunkingConfig"], List[str]]] = None
    metadata_config: Dict[str, Any] = field(
        default_factory=dict
    )  # Config for metadata extraction


class ChunkMetadata(Dict[str, Any]):
    """Metadata for document chunks.

    This class extends the standard dictionary with properties for accessing
    common chunk metadata.
    """

    @property
    def chunk_index(self) -> int:
        """Get the index of this chunk in the document."""
        return self.get("chunk_index", 0) or 0

    @property
    def total_chunks(self) -> int:
        """Get the total number of chunks in the document."""
        return self.get("total_chunks", 1) or 1

    @property
    def parent_id(self) -> Optional[str]:
        """Get the ID of the parent document."""
        return self.get("parent_id")

    @property
    def next_chunk_id(self) -> Optional[str]:
        """Get the ID of the next chunk."""
        return self.get("next_chunk_id")

    @property
    def prev_chunk_id(self) -> Optional[str]:
        """Get the ID of the previous chunk."""
        return self.get("prev_chunk_id")

    @property
    def hierarchy_level(self) -> int:
        """Get the hierarchy level of this chunk."""
        return self.get("hierarchy_level", 0) or 0

    @property
    def is_summary(self) -> bool:
        """Check if this chunk is a summary."""
        return bool(self.get("is_summary", False))


#
# Transformation Models
#


class TransformationType(Enum):
    """Types of document transformations."""

    NORMALIZE = "normalize"  # Unicode normalization
    CLEAN = "clean"  # Remove unwanted characters
    LOWERCASE = "lowercase"  # Convert to lowercase
    REMOVE_STOPWORDS = "remove_stopwords"  # Remove common stopwords
    REMOVE_PUNCTUATION = "remove_punctuation"  # Remove punctuation
    REMOVE_WHITESPACE = "remove_whitespace"  # Remove excess whitespace
    REMOVE_HTML = "remove_html"  # Remove HTML tags
    REMOVE_URLS = "remove_urls"  # Remove URLs
    REMOVE_NUMBERS = "remove_numbers"  # Remove numeric values
    STEM = "stem"  # Apply stemming
    LEMMATIZE = "lemmatize"  # Apply lemmatization
    CUSTOM = "custom"  # Custom transformation


@dataclass
class TransformationConfig:
    """Configuration for document transformations.

    This class defines the configuration for document transformations, including
    which transformations to apply and their parameters.
    """

    enabled: bool = True  # Whether transformations are enabled
    include_types: Optional[List[TransformationType]] = None  # Types to include
    exclude_types: Optional[List[TransformationType]] = None  # Types to exclude
    preserve_original: bool = True  # Whether to preserve the original content
    custom_transformers: Dict[str, Callable[[str], str]] = field(
        default_factory=dict
    )  # Custom transformers
    params: Dict[str, Any] = field(default_factory=dict)  # Additional parameters


#
# Metadata Models
#


class MetadataType(Enum):
    """Types of metadata that can be extracted from documents."""

    DATE = "date"  # Dates mentioned in the document
    AUTHOR = "author"  # Author information
    TOPIC = "topic"  # Topics or categories
    ENTITY = "entity"  # Named entities (people, places, organizations)
    KEYWORD = "keyword"  # Keywords or key phrases
    LANGUAGE = "language"  # Document language
    SENTIMENT = "sentiment"  # Sentiment analysis
    SUMMARY = "summary"  # Document summary
    CUSTOM = "custom"  # Custom metadata type


@dataclass
class MetadataExtractorConfig:
    """Configuration for metadata extractors.

    This class defines the configuration for metadata extractors, including
    extraction parameters and thresholds.
    """

    enabled: bool = True  # Whether this extractor is enabled
    confidence_threshold: float = 0.5  # Minimum confidence for extracted metadata
    max_items: Optional[int] = None  # Maximum number of items to extract
    include_types: Optional[List[MetadataType]] = None  # Types to include
    exclude_types: Optional[List[MetadataType]] = None  # Types to exclude
    custom_extractors: Dict[str, Callable[[str], Dict[str, Any]]] = field(
        default_factory=dict
    )  # Custom extractors
    params: Dict[str, Any] = field(default_factory=dict)  # Additional parameters


#
# Result Models
#


@dataclass
class RetrievalResult:
    """Result of a retrieval operation."""

    documents: List[Document]
    query: str
    query_embedding: Optional[List[float]] = None
    scores: Optional[List[float]] = None


@dataclass
class RerankingResult:
    """Result of a reranking operation."""

    documents: List[Document]
    query: str
    scores: Optional[List[float]] = None


@dataclass
class GenerationResult:
    """Result of a generation operation."""

    response: str
    documents: List[Document]
    query: str
    prompt: str
