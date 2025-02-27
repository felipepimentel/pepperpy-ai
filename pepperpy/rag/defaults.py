"""Default component registration for the RAG system."""

from .augmenters import HybridAugmenter, MultiStageAugmenter, TemplateAugmenter
from .chunkers import HTMLChunker, RecursiveChunker, TextChunker
from .embedders import (
    BatchedEmbedder,
    CachedEmbedder,
    HybridEmbedder,
    TransformerEmbedder,
)
from .indexers import AnnoyIndexer, FaissIndexer, HybridIndexer
from .registry import registry
from .retrievers import HybridRetriever, ReRankingRetriever, StandardRetriever


def register_default_components():
    """Register default implementations of RAG components."""
    # Register chunkers
    registry.register_chunker("default", TextChunker)
    registry.register_chunker("text", TextChunker)
    registry.register_chunker("recursive", RecursiveChunker)
    registry.register_chunker("html", HTMLChunker)

    # Register specialized chunkers
    registry.register_chunker("qa_chunker", TextChunker)  # Optimized for QA
    registry.register_chunker("summary_chunker", RecursiveChunker)  # For summarization
    registry.register_chunker("kb_chunker", HTMLChunker)  # For knowledge bases

    # Register embedders
    registry.register_embedder("default", TransformerEmbedder)
    registry.register_embedder("transformer", TransformerEmbedder)
    registry.register_embedder("cached", CachedEmbedder)
    registry.register_embedder("batched", BatchedEmbedder)
    registry.register_embedder("hybrid", HybridEmbedder)

    # Register specialized embedders
    registry.register_embedder("qa_embedder", TransformerEmbedder)  # Optimized for QA
    registry.register_embedder("kb_embedder", HybridEmbedder)  # For knowledge bases

    # Register indexers
    registry.register_indexer("default", FaissIndexer)
    registry.register_indexer("faiss", FaissIndexer)
    registry.register_indexer("annoy", AnnoyIndexer)
    registry.register_indexer("hybrid", HybridIndexer)

    # Register specialized indexers
    registry.register_indexer("qa_indexer", FaissIndexer)  # Optimized for QA
    registry.register_indexer("kb_indexer", HybridIndexer)  # For knowledge bases

    # Register retrievers
    registry.register_retriever("default", StandardRetriever)
    registry.register_retriever("standard", StandardRetriever)
    registry.register_retriever("hybrid", HybridRetriever)
    registry.register_retriever("reranking", ReRankingRetriever)

    # Register specialized retrievers
    registry.register_retriever(
        "qa_retriever", ReRankingRetriever
    )  # With re-ranking for QA
    registry.register_retriever("kb_retriever", HybridRetriever)  # For knowledge bases

    # Register augmenters
    registry.register_augmenter("default", TemplateAugmenter)
    registry.register_augmenter("template", TemplateAugmenter)
    registry.register_augmenter("multistage", MultiStageAugmenter)
    registry.register_augmenter("hybrid", HybridAugmenter)

    # Register specialized augmenters
    registry.register_augmenter(
        "qa_augmenter", MultiStageAugmenter
    )  # Multi-stage for QA
    registry.register_augmenter("kb_augmenter", HybridAugmenter)  # For knowledge bases
