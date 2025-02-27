"""Configuration settings for the RAG system."""

from typing import Optional

from pydantic import BaseModel, Field


class ChunkingConfig(BaseModel):
    """Configuration for document chunking."""

    chunk_size: int = Field(default=512, ge=1, description="Size of chunks in tokens")
    chunk_overlap: int = Field(
        default=50, ge=0, description="Overlap between chunks in tokens"
    )
    min_chunk_size: int = Field(
        default=100, ge=1, description="Minimum chunk size in tokens"
    )
    max_chunk_size: int = Field(
        default=1024, ge=1, description="Maximum chunk size in tokens"
    )
    chunking_strategy: str = Field(
        default="token",
        description="Strategy for chunking (token, sentence, paragraph)",
    )
    preserve_whitespace: bool = Field(
        default=False,
        description="Whether to preserve whitespace in chunks",
    )


class EmbeddingConfig(BaseModel):
    """Configuration for embedding generation."""

    model_name: str = Field(
        default="sentence-transformers/all-mpnet-base-v2",
        description="Name of the embedding model to use",
    )
    batch_size: int = Field(
        default=32, ge=1, description="Batch size for embedding generation"
    )
    cache_dir: Optional[str] = Field(
        default=None,
        description="Directory to cache embeddings",
    )
    normalize_embeddings: bool = Field(
        default=True,
        description="Whether to L2-normalize embeddings",
    )
    embedding_device: str = Field(
        default="cuda",
        description="Device to use for embedding generation (cuda, cpu)",
    )


class IndexConfig(BaseModel):
    """Configuration for vector indexing."""

    index_type: str = Field(
        default="faiss",
        description="Type of vector index to use (faiss, annoy)",
    )
    metric: str = Field(
        default="cosine",
        description="Similarity metric to use (cosine, l2, dot)",
    )
    nprobe: int = Field(
        default=8,
        description="Number of clusters to probe in index search",
    )
    index_path: Optional[str] = Field(
        default=None,
        description="Path to save/load index",
    )
    use_gpu: bool = Field(
        default=True,
        description="Whether to use GPU for index operations",
    )


class RetrievalConfig(BaseModel):
    """Configuration for context retrieval."""

    top_k: int = Field(default=5, ge=1, description="Number of chunks to retrieve")
    min_score: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score for retrieval",
    )
    rerank_top_k: Optional[int] = Field(
        default=None,
        description="Number of results to rerank",
    )
    use_hybrid_search: bool = Field(
        default=False,
        description="Whether to use hybrid search (vector + keyword)",
    )


class AugmentationConfig(BaseModel):
    """Configuration for context augmentation."""

    max_tokens: int = Field(
        default=2048, ge=1, description="Maximum tokens in augmented context"
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Temperature for text generation",
    )
    prompt_template: Optional[str] = Field(
        default=None,
        description="Template for prompt construction",
    )
    include_metadata: bool = Field(
        default=True,
        description="Whether to include chunk metadata in context",
    )


class RagConfig(BaseModel):
    """Main configuration for the RAG system."""

    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    indexing: IndexConfig = Field(default_factory=IndexConfig)
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)
    augmentation: AugmentationConfig = Field(default_factory=AugmentationConfig)
    cache_dir: Optional[str] = Field(
        default=None,
        description="Base directory for all caching",
    )
    debug_mode: bool = Field(
        default=False,
        description="Whether to enable debug mode",
    )

    class Config:
        """Pydantic config."""

        validate_assignment = True
        extra = "forbid"
