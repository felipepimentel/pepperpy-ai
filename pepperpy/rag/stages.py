"""RAG Pipeline Stages.

This module provides the core implementations of the different pipeline stages
used in the RAG (Retrieval Augmented Generation) process, including retrieval,
reranking, and generation.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Sequence

from pepperpy.core.errors import PepperPyError
from pepperpy.rag.interfaces import (
    EmbeddingProvider,
    GenerationProvider,
    PipelineStage,
    RerankerProvider,
)
from pepperpy.rag.models import (
    Document,
    DocumentChunk,
    GenerationResult,
    RerankingResult,
    RetrievalResult,
    ScoredChunk,
)


# Base stage configuration
@dataclass
class StageConfig:
    """Base configuration for pipeline stages.

    This class defines the base configuration for all pipeline stages.
    """

    name: str = "stage"
    type: str = ""
    enabled: bool = True
    params: Dict[str, Any] = field(default_factory=dict)


# Retrieval stage
@dataclass
class RetrievalStageConfig(StageConfig):
    """Configuration for the retrieval stage.

    This class defines the configuration for the retrieval stage,
    which retrieves relevant documents based on a query.
    """

    top_k: int = 5

    def __post_init__(self):
        """Initialize the retrieval stage configuration."""
        if not self.type:
            self.type = "retrieval"


class RetrievalStage(PipelineStage):
    """Retrieval stage for the RAG pipeline.

    This stage retrieves relevant documents based on a query.
    """

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        document_store: Any,  # DocumentStore
        config: Optional[RetrievalStageConfig] = None,
    ):
        """Initialize the retrieval stage.

        Args:
            embedding_provider: The embedding provider
            document_store: The document store
            config: The stage configuration
        """
        self.embedding_provider = embedding_provider
        self.document_store = document_store
        self.config = config or RetrievalStageConfig(name="retrieval", type="retrieval")

    async def process(self, inputs: Any, **kwargs: Any) -> Any:
        """Process the inputs (query) to retrieve relevant documents.

        Args:
            inputs: The query to process
            **kwargs: Additional arguments for processing

        Returns:
            The retrieval results
        """
        # If inputs is a string, treat it as a query
        if isinstance(inputs, str):
            return await self._process_query(inputs)
        else:
            raise PepperPyError(f"Expected string query, got {type(inputs).__name__}")

    async def _process_query(self, query: str) -> RetrievalResult:
        """Process a query to retrieve relevant documents.

        Args:
            query: The query to process

        Returns:
            The retrieval results
        """
        try:
            # Generate embedding for the query
            query_embedding = await self.embedding_provider.embed(query)

            # Search for similar documents
            chunks, scores = await self.document_store.search(
                query_embedding, top_k=self.config.top_k
            )

            # Create scored chunks
            scored_chunks = []
            for i in range(len(chunks)):
                chunk = chunks[i]
                score = scores[i] if i < len(scores) else 0.0

                scored_chunks.append(ScoredChunk(chunk=chunk, score=score))

            # Return the retrieval result
            return RetrievalResult(
                chunks=scored_chunks,
                query=query,
                metadata={"query_embedding": query_embedding},
            )
        except Exception as e:
            raise PepperPyError(f"Retrieval failed: {str(e)}") from e


# Reranking stage
@dataclass
class RerankingStageConfig(StageConfig):
    """Configuration for the reranking stage.

    This class defines the configuration for the reranking stage,
    which reranks retrieved documents for better relevance.
    """

    top_k: int = 3

    def __post_init__(self):
        """Initialize the reranking stage configuration."""
        if not self.type:
            self.type = "reranking"


class RerankingStage(PipelineStage):
    """Reranking stage for the RAG pipeline.

    This stage reranks retrieved documents for better relevance.
    """

    def __init__(
        self,
        reranker_provider: RerankerProvider,
        config: Optional[RerankingStageConfig] = None,
    ):
        """Initialize the reranking stage.

        Args:
            reranker_provider: The reranker provider
            config: The stage configuration
        """
        self.reranker_provider = reranker_provider
        self.config = config or RerankingStageConfig(name="reranking", type="reranking")

    async def process(self, inputs: Any, **kwargs: Any) -> Any:
        """Process the inputs (retrieval result) to rerank documents.

        Args:
            inputs: The retrieval results to process
            **kwargs: Additional arguments for processing

        Returns:
            The reranking results
        """
        # If inputs is a RetrievalResult, process it
        if isinstance(inputs, RetrievalResult):
            return await self._process_retrieval_result(inputs)
        else:
            raise PepperPyError(
                f"Expected RetrievalResult, got {type(inputs).__name__}"
            )

    async def _process_retrieval_result(
        self, retrieval_result: RetrievalResult
    ) -> RerankingResult:
        """Process retrieval results to rerank documents.

        Args:
            retrieval_result: The retrieval results to process

        Returns:
            The reranking results
        """
        try:
            # Get the query from the retrieval result
            query = retrieval_result.query

            # Extract chunks from the retrieval result
            chunks = [scored_chunk.chunk for scored_chunk in retrieval_result.chunks]

            # Convert DocumentChunk to Document for the reranker if needed
            documents = []
            for chunk in chunks:
                if isinstance(chunk, DocumentChunk):
                    # Create a Document from the DocumentChunk
                    doc = Document(
                        content=chunk.content,
                        metadata=chunk.metadata,
                        id=chunk.id,
                    )
                    documents.append(doc)
                elif isinstance(chunk, Document):
                    documents.append(chunk)
                else:
                    raise PepperPyError(
                        f"Unexpected chunk type: {type(chunk).__name__}"
                    )

            # Rerank the documents
            scored_chunks_result = await self.reranker_provider.rerank(query, documents)

            # Limit to top_k
            scored_chunks = scored_chunks_result[: self.config.top_k]

            # Return the reranking result
            return RerankingResult(
                chunks=scored_chunks,
                query=query,
                original_chunks=retrieval_result.chunks,
                metadata={},
            )
        except Exception as e:
            raise PepperPyError(f"Reranking failed: {str(e)}") from e


# Generation stage
@dataclass
class GenerationStageConfig(StageConfig):
    """Configuration for the generation stage.

    This class defines the configuration for the generation stage,
    which generates text based on retrieved documents.
    """

    prompt_template: str = "Based on the following documents, answer the question:\n\nDocuments: {documents}\n\nQuestion: {query}\n\nAnswer:"
    document_separator: str = "\n---\n"

    def __post_init__(self):
        """Initialize the generation stage configuration."""
        if not self.type:
            self.type = "generation"


class GenerationStage(PipelineStage):
    """Generation stage for the RAG pipeline.

    This stage generates text based on retrieved documents.
    """

    def __init__(
        self,
        generation_provider: GenerationProvider,
        config: Optional[GenerationStageConfig] = None,
    ):
        """Initialize the generation stage.

        Args:
            generation_provider: The generation provider
            config: The stage configuration
        """
        self.generation_provider = generation_provider
        self.config = config or GenerationStageConfig(
            name="generation", type="generation"
        )

    async def process(self, inputs: Any, **kwargs: Any) -> Any:
        """Process the inputs (reranking result) to generate text.

        Args:
            inputs: The reranking results to process
            **kwargs: Additional arguments for processing

        Returns:
            The generation results
        """
        # If inputs is a RerankingResult, process it
        if isinstance(inputs, RerankingResult):
            return await self._process_reranking_result(inputs)
        else:
            raise PepperPyError(
                f"Expected RerankingResult, got {type(inputs).__name__}"
            )

    async def _process_reranking_result(
        self, reranking_result: RerankingResult
    ) -> GenerationResult:
        """Process reranking results to generate text.

        Args:
            reranking_result: The reranking results to process

        Returns:
            The generation results
        """
        try:
            # Get the query from the reranking result
            query = reranking_result.query

            # Extract chunks from the reranking result
            chunks = [scored_chunk.chunk for scored_chunk in reranking_result.chunks]

            # Prepare documents text
            documents_text = self._prepare_documents_text(chunks)

            # Format the prompt
            prompt = self.config.prompt_template.format(
                documents=documents_text, query=query
            )

            # Generate text
            generated_text = await self.generation_provider.generate(prompt)

            # Return the generation result
            return GenerationResult(
                text=generated_text,
                chunks=reranking_result.chunks,
                query=query,
                metadata={"prompt": prompt},
            )
        except Exception as e:
            raise PepperPyError(f"Generation failed: {str(e)}") from e

    def _prepare_documents_text(self, chunks: Sequence[DocumentChunk]) -> str:
        """Prepare the documents text for the prompt.

        Args:
            chunks: The document chunks to prepare

        Returns:
            The prepared documents text
        """
        # Convert chunks to text
        documents_texts = []
        for i, chunk in enumerate(chunks):
            # Add document number and content
            document_text = f"Document {i + 1}: {chunk.content}"
            documents_texts.append(document_text)

        # Join the documents
        return self.config.document_separator.join(documents_texts)
