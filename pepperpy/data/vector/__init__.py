"""Vector store module for Pepperpy."""

from .base import VectorStore
from .faiss import FAISSVectorStore

__all__ = [
    "VectorStore",
    "FAISSVectorStore",
]
