"""Capability enums for the pepperpy library."""

from enum import Enum, auto


class RAGCapability(Enum):
    """RAG capabilities."""

    DOCUMENT_LOADING = auto()
    DOCUMENT_CHUNKING = auto()
    DOCUMENT_EMBEDDING = auto()
    DOCUMENT_SEARCH = auto()
    DOCUMENT_RETRIEVAL = auto()


class RAGStrategy(Enum):
    """RAG strategies."""

    BASIC = auto()
    SEMANTIC = auto()
    HYBRID = auto()
    RECURSIVE = auto() 