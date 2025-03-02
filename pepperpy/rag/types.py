"""Type definitions for the RAG system.

This module defines the core data types for the RAG system.
"""

from enum import Enum, auto
from typing import Any, Dict, List

from pydantic import BaseModel, Field


class RagComponentType(Enum):
    """Types of RAG components."""

    CUSTOM = auto()
    PIPELINE = auto()

    # Indexing components
    CHUNKER = auto()
    EMBEDDER = auto()
    INDEXER = auto()
    DOCUMENT_INDEXER = auto()
    INDEXING_MANAGER = auto()

    # Retrieval components
    RETRIEVER = auto()
    SIMILARITY_RETRIEVER = auto()
    HYBRID_RETRIEVER = auto()
    RETRIEVAL_MANAGER = auto()

    # Generation components
    GENERATOR = auto()
    PROMPT_GENERATOR = auto()
    CONTEXT_AWARE_GENERATOR = auto()
    GENERATION_MANAGER = auto()


class Document(BaseModel):
    """A document to be indexed and retrieved."""

    id: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Chunk(BaseModel):
    """A chunk of content from a document."""

    id: str
    content: str
    document_id: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Embedding(BaseModel):
    """An embedding vector for a chunk."""

    id: str
    vector: List[float]
    chunk_id: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SearchQuery(BaseModel):
    """A search query for the RAG system."""

    query: str
    filters: Dict[str, Any] = Field(default_factory=dict)
    top_k: int = 5
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SearchResult(BaseModel):
    """A search result from the RAG system."""

    chunk: Chunk
    score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RagContext(BaseModel):
    """Context for RAG operations."""

    query: SearchQuery
    results: List[SearchResult] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RagResponse(BaseModel):
    """Response from the RAG system."""

    query: SearchQuery
    response: str
    context: RagContext
    metadata: Dict[str, Any] = Field(default_factory=dict)
