"""Core data types for the RAG system."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List


class ChunkType(Enum):
    """Types of document chunks."""

    TEXT = "text"
    CODE = "code"
    TABLE = "table"
    LIST = "list"
    EQUATION = "equation"
    IMAGE = "image"
    CUSTOM = "custom"


@dataclass
class Chunk:
    """Represents a chunk of content with metadata."""

    id: str
    content: str
    type: ChunkType
    start_idx: int
    end_idx: int
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Document:
    """Represents a document in the RAG system."""

    id: str
    content: str
    chunks: List[Chunk]
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class Embedding:
    """Represents an embedding vector with metadata."""

    id: str
    vector: List[float]
    chunk_id: str
    model: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchQuery:
    """Represents a search query with parameters."""

    text: str
    filters: Dict[str, Any] = field(default_factory=dict)
    top_k: int = 5
    threshold: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchResult:
    """Represents a search result with relevance score."""

    chunk: Chunk
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RagContext:
    """Context for RAG operations including configuration and state."""

    query: str
    results: List[SearchResult]
    metadata: Dict[str, Any] = field(default_factory=dict)
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RagResponse:
    """Response from the RAG system including generated content and context."""

    content: str
    context: RagContext
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
