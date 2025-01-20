"""Vector module for dynamic sources."""

from .embeddings import EmbeddingModel, OpenAIEmbeddingModel
from .indexer import VectorIndex, IndexError, SearchResult, IndexManager
from .base import VectorDB, VectorDBError
from .faiss import FaissVectorDB
from .semantic import SemanticSearch

__all__ = [
    "EmbeddingModel",
    "OpenAIEmbeddingModel",
    "VectorIndex",
    "IndexError",
    "SearchResult",
    "IndexManager",
    "VectorDB",
    "VectorDBError",
    "FaissVectorDB",
    "SemanticSearch",
] 