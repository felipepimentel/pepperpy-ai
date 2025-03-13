"""Pipeline builder for the RAG system."""

from dataclasses import dataclass
from typing import Any, Dict, Optional

from pepperpy.errors import PepperpyError
from pepperpy.llm.generation import GenerationProvider
from pepperpy.llm.reranking import RerankerProvider
from pepperpy.llm.utils import Response
from pepperpy.rag.document.store import DocumentStore
from pepperpy.rag.embedding import EmbeddingProvider
from pepperpy.rag.pipeline.stages.generation import (
    GenerationStage,
    GenerationStageConfig,
)
from pepperpy.rag.pipeline.stages.reranking import (
    RerankingResult,
    RerankingStage,
    RerankingStageConfig,
)
from pepperpy.rag.pipeline.stages.retrieval import (
    RetrievalStage,
    RetrievalStageConfig,
)


@dataclass
class RAGPipelineConfig:
    """Configuration for the RAG pipeline."""

    retrieval: RetrievalStageConfig
    reranking: Optional[RerankingStageConfig] = None
    generation: Optional[GenerationStageConfig] = None


class RAGPipeline:
    """Pipeline for RAG processing."""

    def __init__(
        self,
        config: RAGPipelineConfig,
        embedding_provider: EmbeddingProvider,
        document_store: DocumentStore,
        reranker_provider: Optional[RerankerProvider] = None,
        generation_provider: Optional[GenerationProvider] = None,
    ):
        """Initialize the pipeline.

        Args:
            config: Pipeline configuration
            embedding_provider: Provider for embeddings
            document_store: Store for document retrieval
            reranker_provider: Optional provider for reranking
            generation_provider: Optional provider for generation
        """
        self.config = config

        # Initialize stages with their required providers
        self.retrieval_stage = RetrievalStage(
            embedding_provider=embedding_provider,
            document_store=document_store,
            config=config.retrieval,
        )

        self.reranking_stage = None
        if config.reranking and reranker_provider:
            self.reranking_stage = RerankingStage(
                reranker_provider=reranker_provider, config=config.reranking
            )

        self.generation_stage = None
        if config.generation and generation_provider:
            self.generation_stage = GenerationStage(
                generation_provider=generation_provider, config=config.generation
            )

    async def process(
        self,
        query: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Response:
        """Process a query through the pipeline.

        Args:
            query: User query
            metadata: Optional metadata

        Returns:
            Generated response

        Raises:
            PepperpyError: If processing fails
        """
        try:
            # Retrieve relevant chunks
            retrieval_result = self.retrieval_stage.process(query)
            chunks = retrieval_result.documents

            # Rerank chunks if configured
            if self.reranking_stage:
                reranking_result = self.reranking_stage.process(retrieval_result)
                chunks = reranking_result.documents

            # Generate response if configured
            if self.generation_stage:
                # Create a reranking result if we didn't have a reranking stage
                if not self.reranking_stage:
                    reranking_result = RerankingResult(documents=chunks, query=query)

                generation_result = self.generation_stage.process(reranking_result)

                return Response(
                    text=generation_result.response,
                    usage={
                        "total_tokens": 0,
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                    },
                    metadata=metadata or {},
                )

            # Return empty response if no generation stage
            return Response(
                text="",
                usage={"total_tokens": 0, "prompt_tokens": 0, "completion_tokens": 0},
                metadata=metadata or {},
            )

        except Exception as e:
            raise PepperpyError(f"Error in RAG pipeline: {e}")


class RAGPipelineBuilder:
    """Builder for RAG pipelines."""

    def __init__(self):
        """Initialize the builder."""
        self.retrieval_config: Optional[RetrievalStageConfig] = None
        self.reranking_config: Optional[RerankingStageConfig] = None
        self.generation_config: Optional[GenerationStageConfig] = None
        self.embedding_provider: Optional[EmbeddingProvider] = None
        self.document_store: Optional[DocumentStore] = None
        self.reranker_provider: Optional[RerankerProvider] = None
        self.generation_provider: Optional[GenerationProvider] = None

    def with_retrieval(
        self,
        config: RetrievalStageConfig,
        embedding_provider: EmbeddingProvider,
        document_store: DocumentStore,
    ) -> "RAGPipelineBuilder":
        """Add retrieval stage.

        Args:
            config: Stage configuration
            embedding_provider: Provider for embeddings
            document_store: Store for document retrieval

        Returns:
            Self for chaining
        """
        self.retrieval_config = config
        self.embedding_provider = embedding_provider
        self.document_store = document_store
        return self

    def with_reranking(
        self,
        config: RerankingStageConfig,
        reranker_provider: RerankerProvider,
    ) -> "RAGPipelineBuilder":
        """Add reranking stage.

        Args:
            config: Stage configuration
            reranker_provider: Provider for reranking

        Returns:
            Self for chaining
        """
        self.reranking_config = config
        self.reranker_provider = reranker_provider
        return self

    def with_generation(
        self,
        config: GenerationStageConfig,
        generation_provider: GenerationProvider,
    ) -> "RAGPipelineBuilder":
        """Add generation stage.

        Args:
            config: Stage configuration
            generation_provider: Provider for generation

        Returns:
            Self for chaining
        """
        self.generation_config = config
        self.generation_provider = generation_provider
        return self

    def build(self) -> RAGPipeline:
        """Build the pipeline.

        Returns:
            Configured pipeline

        Raises:
            PepperpyError: If configuration is invalid
        """
        if not self.retrieval_config:
            raise PepperpyError("Retrieval stage is required")

        if not self.embedding_provider:
            raise PepperpyError("Embedding provider is required")

        if not self.document_store:
            raise PepperpyError("Document store is required")

        config = RAGPipelineConfig(
            retrieval=self.retrieval_config,
            reranking=self.reranking_config,
            generation=self.generation_config,
        )

        return RAGPipeline(
            config=config,
            embedding_provider=self.embedding_provider,
            document_store=self.document_store,
            reranker_provider=self.reranker_provider,
            generation_provider=self.generation_provider,
        )


# Export all classes
__all__ = [
    "RAGPipelineConfig",
    "RAGPipeline",
    "RAGPipelineBuilder",
]
