"""RAG (Retrieval Augmented Generation) capabilities."""

from typing import TypedDict

from .base import Document
from .base import RAGCapability as BaseRAG
from .simple import SimpleRAGCapability as SimpleRAG
from .strategies.base import BaseRAGStrategy
from .strategies.semantic import SemanticRAGStrategy


class RAGConfig(TypedDict, total=False):
    """RAG configuration."""

    model: str | None
    temperature: float | None
    max_tokens: int | None
    top_p: float | None
    frequency_penalty: float | None
    presence_penalty: float | None
    timeout: float | None
    limit: int | None
    threshold: float | None
    top_k: int | None


__all__ = [
    "BaseRAG",
    "BaseRAGStrategy",
    "Document",
    "RAGConfig",
    "SemanticRAGStrategy",
    "SimpleRAG",
]
