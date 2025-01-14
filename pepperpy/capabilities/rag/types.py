"""RAG types module."""

from typing import TypedDict


class RAGConfig(TypedDict, total=False):
    """RAG configuration."""

    model: str
    temperature: float
    max_tokens: int
    chunk_size: int
    chunk_overlap: int
    embedding_model: str
    embedding_batch_size: int
    embedding_normalize: bool
    embedding_device: str


class RAGSearchKwargs(TypedDict, total=False):
    """RAG search keyword arguments."""

    top_k: int
    min_score: float
    max_tokens: int
    temperature: float
    model: str
