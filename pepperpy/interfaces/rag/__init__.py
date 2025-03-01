"""Public Interface for RAG (Retrieval Augmented Generation)

This module provides a stable public interface for the RAG functionality.
It exposes the core RAG abstractions and implementations that are
considered part of the public API.

Core Components:
    RAGPipeline: Base class for RAG pipelines
    RAGConfig: Configuration for RAG systems
    RAGFactory: Factory for creating RAG pipelines

Retrieval:
    RetrievalSystem: Base class for retrieval systems
    VectorRetrieval: Vector-based retrieval implementation

Processing:
    Preprocessor: Base class for preprocessing components
    Optimizer: Base class for optimization components
"""

# Import public classes and functions from the implementation
from pepperpy.rag.base import RAGPipeline
from pepperpy.rag.config import RAGConfig
from pepperpy.rag.factory import RAGFactory
from pepperpy.rag.indexing import IndexingSystem
from pepperpy.rag.processors.optimization import Optimizer
from pepperpy.rag.processors.preprocessing import Preprocessor
from pepperpy.rag.retrieval.system import RetrievalSystem, VectorRetrieval

__all__ = [
    # Core
    "RAGPipeline",
    "RAGConfig",
    "RAGFactory",
    # Retrieval
    "RetrievalSystem",
    "VectorRetrieval",
    # Processing
    "Preprocessor",
    "Optimizer",
    # Indexing
    "IndexingSystem",
] 