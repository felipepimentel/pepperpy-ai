"""Document module for RAG capabilities."""

from typing import TypedDict


class Document(TypedDict):
    """Document type for RAG capabilities."""

    content: str
    metadata: dict[str, str]
    embedding: list[float] | None
