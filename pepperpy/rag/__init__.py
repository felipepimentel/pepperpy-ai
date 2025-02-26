"""Retrieval-Augmented Generation (RAG) package for Pepperpy."""

from .chunking import (
    Chunk,
    ChunkingStrategy,
    FixedSizeChunking,
    SentenceChunking,
)
from .embedding import (
    DocumentEmbedding,
    EmbeddingProvider,
    EmbeddingCache,
    EmbeddingManager,
)
from .retrieval import (
    RetrievalResult,
    RetrievalStrategy,
    CosineRetrievalStrategy,
    HybridRetrievalStrategy,
)
from .augmentation import (
    AugmentedPrompt,
    PromptFormatter,
    SimplePromptFormatter,
    TemplatePromptFormatter,
)

__all__ = [
    # Chunking
    'Chunk',
    'ChunkingStrategy',
    'FixedSizeChunking',
    'SentenceChunking',
    
    # Embedding
    'DocumentEmbedding',
    'EmbeddingProvider',
    'EmbeddingCache',
    'EmbeddingManager',
    
    # Retrieval
    'RetrievalResult',
    'RetrievalStrategy',
    'CosineRetrievalStrategy',
    'HybridRetrievalStrategy',
    
    # Augmentation
    'AugmentedPrompt',
    'PromptFormatter',
    'SimplePromptFormatter',
    'TemplatePromptFormatter',
] 