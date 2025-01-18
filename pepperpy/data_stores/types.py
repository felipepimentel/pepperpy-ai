"""RAG capability types module."""

from typing import TypedDict

from pepperpy.shared.types.config_types import ModelConfig, RAGConfig


class Document(TypedDict, total=False):
    """Document type."""

    content: str
    metadata: dict[str, str | int | float | bool | None]


class RAGSearchKwargs(TypedDict, total=False):
    """RAG search keyword arguments."""

    model: str
    temperature: float
    max_tokens: int
    top_k: int
    min_score: float


__all__ = [
    "Document",
    "ModelConfig",
    "RAGConfig",
    "RAGSearchKwargs",
]
