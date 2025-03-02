"""Public Interface for RAG (Retrieval Augmented Generation)

This module provides a stable public interface for the RAG functionality.
It exposes the core RAG abstractions and implementations that are
considered part of the public API.

Core Components:
    RAGPipeline: Base class for RAG pipelines
    RAGConfig: Configuration for RAG systems
    RAGFactory: Factory for creating RAG pipelines

Retrieval:
    Retriever: Base class for retrieval systems
    VectorRetriever: Vector-based retrieval implementation
    Document: Represents a document in the retrieval system
    SearchResult: Result from a retrieval operation
    SearchQuery: Query for retrieval operations

Processing:
    Preprocessor: Base class for preprocessing components
    Optimizer: Base class for optimization components
"""

# Import retriever interfaces
from .retriever import Document, Retriever, SearchQuery, SearchResult, VectorRetriever

__all__ = [
    # Retrieval
    "Retriever",
    "VectorRetriever",
    "Document",
    "SearchQuery",
    "SearchResult",
]
