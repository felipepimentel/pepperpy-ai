"""Unit tests for the RAG pipeline adapter."""

import asyncio
import gc
import os
import time
from typing import Any, Protocol, cast, runtime_checkable
from unittest.mock import AsyncMock, MagicMock

import psutil
import pytest
from typing_extensions import assert_type

from pepperpy.core.pipeline import PipelineContext, PipelineStage
from pepperpy.rag.document.core import DocumentChunk
from pepperpy.rag.document.store import DocumentStore
from pepperpy.rag.embedding import EmbeddingProvider
from pepperpy.rag.models import (
    Document,
    GenerationResult,
    Metadata,
)
from pepperpy.rag.pipeline.adapter import (
    GenerationStageAdapter,
    RAGPipelineAdapter,
    RAGPipelineBuilderAdapter,
    RerankingStageAdapter,
    RetrievalStageAdapter,
)
from pepperpy.rag.pipeline.builder import RAGPipelineConfig
from pepperpy.rag.pipeline.stages.generation import GenerationStageConfig
from pepperpy.rag.pipeline.stages.reranking import (
    RerankerProvider,
    RerankingResult,
    RerankingStageConfig,
)
from pepperpy.rag.pipeline.stages.retrieval import (
    RetrievalResult,
    RetrievalStageConfig,
)


# Protocol definitions for type checking
@runtime_checkable
class StageProcessor(Protocol):
    """Protocol for stage processors."""

    async def process(self, input_data: Any, context: PipelineContext) -> Any:
        """Process input data."""
        ...


class MockEmbeddingProvider(EmbeddingProvider):
    """Mock embedding provider for testing."""

    async def embed_query(self, query: str, metadata=None) -> list[float]:
        """Embed a query."""
        return [0.1, 0.2, 0.3]

    async def embed_documents(
        self, documents: list[str], metadata=None
    ) -> list[list[float]]:
        """Embed documents."""
        return [[0.1, 0.2, 0.3] for _ in documents]


class MockDocumentStore(DocumentStore):
    """Mock document store for testing."""

    async def get_document(self, document_id: str) -> Document:
        """Get a document by ID."""
        return Document(content="test content", metadata=Metadata(), id=document_id)

    async def search(self, query: str, top_k: int = 3) -> list[DocumentChunk]:
        """Search for documents."""
        return [DocumentChunk(content="test", metadata=Metadata(), document_id="1")]


class MockRerankerProvider(RerankerProvider):
    """Mock reranker provider for testing."""

    async def rerank(
        self, query: str, chunks: list[DocumentChunk], metadata=None
    ) -> list[DocumentChunk]:
        """Rerank chunks."""
        return chunks


class MockGenerationProvider:
    """Mock generation provider for testing."""

    async def generate(self, query: str, chunks: list[DocumentChunk]) -> str:
        """Generate text."""
        return "Generated text"


class TestRetrievalStageAdapter:
    """Test the retrieval stage adapter."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = RetrievalStageConfig(
            provider="test",
            top_k=3,
            similarity_threshold=0.7,
        )
        self.embedding_provider = MockEmbeddingProvider()
        self.document_store = MockDocumentStore()
        self.stage = RetrievalStageAdapter(
            name="test_retrieval",
            config=self.config,
            embedding_provider=self.embedding_provider,
            document_store=self.document_store,
        )
        # Cast to Any to allow setting _stage
        setattr(self.stage, "_stage", MagicMock())

    def test_init(self):
        """Test initialization."""
        assert self.stage.name == "test_retrieval"

    @pytest.mark.asyncio
    async def test_process(self):
        """Test process method."""
        query = "test query"
        context = PipelineContext()
        chunks = [DocumentChunk(content="test", metadata=Metadata(), document_id="1")]

        # Cast to Any to allow setting process
        stage = getattr(self.stage, "_stage")
        stage.process = AsyncMock(return_value=chunks)

        result = await self.stage.process(query, context)
        assert result is not None
        assert isinstance(result, RetrievalResult)
        assert len(result.chunks) > 0
        assert isinstance(result.chunks[0], DocumentChunk)

    def test_type_compliance(self):
        """Test type compliance of the retrieval stage."""
        assert isinstance(self.stage, PipelineStage)
        assert isinstance(self.stage, StageProcessor)
        assert_type(self.stage.name, str)

    @pytest.mark.asyncio
    async def test_process_empty_query(self):
        """Test processing with empty query."""
        context = PipelineContext()

        with pytest.raises(ValueError, match="Query cannot be empty"):
            await self.stage.process("", context)

    @pytest.mark.asyncio
    async def test_process_no_results(self):
        """Test processing when no documents are found."""
        query = "test query"
        context = PipelineContext()

        stage = getattr(self.stage, "_stage")
        stage.process = AsyncMock(return_value=[])

        result = await self.stage.process(query, context)
        assert result is not None
        assert isinstance(result, RetrievalResult)
        assert len(result.chunks) == 0


class TestRerankingStageAdapter:
    """Test the reranking stage adapter."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = RerankingStageConfig(
            provider="test",
            top_k=3,
            score_threshold=0.5,
        )
        self.reranker_provider = MockRerankerProvider()
        self.stage = RerankingStageAdapter(
            name="test_reranking",
            config=self.config,
            reranker_provider=self.reranker_provider,
        )
        # Cast to Any to allow setting _stage
        setattr(self.stage, "_stage", MagicMock())

    def test_init(self):
        """Test initialization."""
        assert self.stage.name == "test_reranking"

    @pytest.mark.asyncio
    async def test_process(self):
        """Test process method."""
        query = "test query"
        context = PipelineContext()
        context.set("query", query)
        chunks = [DocumentChunk(content="test", metadata=Metadata(), document_id="1")]

        retrieval_result = RetrievalResult(
            chunks=chunks,
        )

        # Cast to Any to allow setting process
        stage = getattr(self.stage, "_stage")
        stage.process = AsyncMock(return_value=chunks)

        result = await self.stage.process(retrieval_result, context)
        assert result is not None
        assert isinstance(result, RerankingResult)
        assert len(result.chunks) > 0
        assert isinstance(result.chunks[0], DocumentChunk)

    def test_type_compliance(self):
        """Test type compliance of the reranking stage."""
        assert isinstance(self.stage, PipelineStage)
        assert isinstance(self.stage, StageProcessor)
        assert_type(self.stage.name, str)

    @pytest.mark.asyncio
    async def test_process_empty_chunks(self):
        """Test processing with empty chunks."""
        query = "test query"
        context = PipelineContext()
        context.set("query", query)

        retrieval_result = RetrievalResult(chunks=[])

        result = await self.stage.process(retrieval_result, context)
        assert result is not None
        assert isinstance(result, RerankingResult)
        assert len(result.chunks) == 0

    @pytest.mark.asyncio
    async def test_process_invalid_input(self):
        """Test processing with invalid input type."""
        context = PipelineContext()

        with pytest.raises(TypeError):
            await self.stage.process(cast(Any, "invalid input"), context)


class TestGenerationStageAdapter:
    """Test the generation stage adapter."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = GenerationStageConfig(
            provider="test",
            model="test-model",
        )
        self.generation_provider = MockGenerationProvider()
        self.stage = GenerationStageAdapter(
            name="test_generation",
            config=self.config,
            generation_provider=self.generation_provider,
        )
        # Cast to Any to allow setting _stage
        setattr(self.stage, "_stage", MagicMock())

    def test_init(self):
        """Test initialization."""
        assert self.stage.name == "test_generation"

    @pytest.mark.asyncio
    async def test_process(self):
        """Test process method."""
        query = "test query"
        context = PipelineContext()
        context.set("query", query)
        chunks = [DocumentChunk(content="test", metadata=Metadata(), document_id="1")]

        reranking_result = RerankingResult(
            chunks=chunks,
        )

        # Cast to Any to allow setting process
        stage = getattr(self.stage, "_stage")
        stage.process = AsyncMock(
            return_value=GenerationResult(
                text="Generated text",
                chunks=chunks,
                query=query,
            )
        )

        result = await self.stage.process(reranking_result, context)
        assert result is not None
        assert isinstance(result, GenerationResult)
        assert result.text == "Generated text"

    def test_type_compliance(self):
        """Test type compliance of the generation stage."""
        assert isinstance(self.stage, PipelineStage)
        assert isinstance(self.stage, StageProcessor)
        assert_type(self.stage.name, str)

    @pytest.mark.asyncio
    async def test_process_empty_chunks(self):
        """Test processing with empty chunks."""
        query = "test query"
        context = PipelineContext()
        context.set("query", query)

        reranking_result = RerankingResult(chunks=[])

        result = await self.stage.process(reranking_result, context)
        assert result is not None
        assert isinstance(result, GenerationResult)
        assert result.text == ""  # Or whatever is appropriate for empty input

    @pytest.mark.asyncio
    async def test_process_invalid_input(self):
        """Test processing with invalid input type."""
        context = PipelineContext()

        with pytest.raises(TypeError):
            await self.stage.process(cast(Any, "invalid input"), context)


class TestRAGPipelineAdapter:
    """Test the RAG pipeline adapter."""

    def setup_method(self):
        """Set up test fixtures."""
        retrieval_config = RetrievalStageConfig(
            provider="test",
            top_k=3,
            similarity_threshold=0.7,
        )
        reranking_config = RerankingStageConfig(
            provider="test",
            top_k=3,
            score_threshold=0.5,
        )
        generation_config = GenerationStageConfig(
            provider="test",
            model="test-model",
        )
        self.config = RAGPipelineConfig(
            name="test_pipeline",
            type="test",
            enabled=True,
            retrieval_config=retrieval_config,
            reranking_config=reranking_config,
            generation_config=generation_config,
        )

        self.embedding_provider = MockEmbeddingProvider()
        self.document_store = MockDocumentStore()
        self.reranker_provider = MockRerankerProvider()
        self.generation_provider = MockGenerationProvider()

        self.pipeline = RAGPipelineAdapter(
            config=self.config,
            embedding_provider=self.embedding_provider,
            document_store=self.document_store,
            reranker_provider=self.reranker_provider,
            generation_provider=self.generation_provider,
        )

        # Mock the stages
        for stage in self.pipeline.stages:
            # Cast to Any to allow setting _stage
            setattr(stage, "_stage", MagicMock())

    def test_init(self):
        """Test initialization."""
        assert self.pipeline.name == "test_pipeline"
        assert len(self.pipeline.stages) == 3
        assert isinstance(self.pipeline.stages[0], PipelineStage)
        assert isinstance(self.pipeline.stages[1], PipelineStage)
        assert isinstance(self.pipeline.stages[2], PipelineStage)

    @pytest.mark.asyncio
    async def test_execute_async(self):
        """Test execute_async method."""
        query = "test query"
        context = PipelineContext()
        chunks = [DocumentChunk(content="test", metadata=Metadata(), document_id="1")]

        # Cast to Any to allow setting process
        for i, stage in enumerate(self.pipeline.stages):
            stage_obj = getattr(stage, "_stage")
            if i < 2:
                stage_obj.process = AsyncMock(return_value=chunks)
            else:
                stage_obj.process = AsyncMock(
                    return_value=GenerationResult(
                        text="Generated text",
                        chunks=chunks,
                        query=query,
                    )
                )

        result = await self.pipeline.execute_async(query, context)
        assert result is not None
        assert isinstance(result, GenerationResult)
        assert result.text == "Generated text"

    def test_type_compliance(self):
        """Test type compliance of the pipeline."""
        assert isinstance(self.pipeline, PipelineStage)
        assert_type(self.pipeline.name, str)

    @pytest.mark.asyncio
    async def test_execute_async_empty_query(self):
        """Test execution with empty query."""
        context = PipelineContext()

        with pytest.raises(ValueError, match="Query cannot be empty"):
            await self.pipeline.execute_async("", context)

    @pytest.mark.asyncio
    async def test_execute_async_disabled_pipeline(self):
        """Test execution with disabled pipeline."""
        self.config.enabled = False
        query = "test query"
        context = PipelineContext()

        with pytest.raises(RuntimeError, match="Pipeline is disabled"):
            await self.pipeline.execute_async(query, context)

    @pytest.mark.asyncio
    async def test_execute_async_missing_context(self):
        """Test execution without context."""
        query = "test query"

        result = await self.pipeline.execute_async(query)
        assert result is not None
        assert isinstance(result, GenerationResult)


class TestRAGPipelineBuilderAdapter:
    """Test the RAG pipeline builder adapter."""

    def setup_method(self):
        """Set up test fixtures."""
        self.builder = RAGPipelineBuilderAdapter()

    def test_init(self):
        """Test initialization."""
        assert not hasattr(self.builder, "config")
        assert not hasattr(self.builder, "embedding_provider")
        assert not hasattr(self.builder, "document_store")
        assert not hasattr(self.builder, "reranker_provider")
        assert not hasattr(self.builder, "generation_provider")

    def test_with_retrieval(self):
        """Test with_retrieval method."""
        config = RetrievalStageConfig(
            provider="test",
            top_k=3,
            similarity_threshold=0.7,
        )
        provider = MockEmbeddingProvider()
        store = MockDocumentStore()

        result = self.builder.with_retrieval(
            config=config,
            embedding_provider=provider,
            document_store=store,
        )
        assert result == self.builder
        assert self.builder._retrieval_config == config
        assert self.builder._embedding_provider == provider
        assert self.builder._document_store == store

    def test_with_reranking(self):
        """Test with_reranking method."""
        config = RerankingStageConfig(
            provider="test",
            top_k=3,
            score_threshold=0.5,
        )
        provider = MockRerankerProvider()

        result = self.builder.with_reranking(
            config=config,
            reranker_provider=provider,
        )
        assert result == self.builder
        assert self.builder._reranking_config == config
        assert self.builder._reranker_provider == provider

    def test_with_generation(self):
        """Test with_generation method."""
        config = GenerationStageConfig(
            provider="test",
            model="test-model",
        )
        provider = MockGenerationProvider()

        result = self.builder.with_generation(
            config=config,
            generation_provider=provider,
        )
        assert result == self.builder
        assert self.builder._generation_config == config
        assert self.builder._generation_provider == provider

    def test_build(self):
        """Test build method."""
        retrieval_config = RetrievalStageConfig(
            provider="test",
            top_k=3,
            similarity_threshold=0.7,
        )
        reranking_config = RerankingStageConfig(
            provider="test",
            top_k=3,
            score_threshold=0.5,
        )
        generation_config = GenerationStageConfig(
            provider="test",
            model="test-model",
        )

        pipeline = (
            self.builder.with_name("test_pipeline")
            .with_retrieval(
                config=retrieval_config,
                embedding_provider=MockEmbeddingProvider(),
                document_store=MockDocumentStore(),
            )
            .with_reranking(
                config=reranking_config,
                reranker_provider=MockRerankerProvider(),
            )
            .with_generation(
                config=generation_config,
                generation_provider=MockGenerationProvider(),
            )
            .build()
        )

        assert isinstance(pipeline, RAGPipelineAdapter)
        assert pipeline.name == "test_pipeline"
        assert len(pipeline.stages) == 3
        assert isinstance(pipeline.stages[0], RetrievalStageAdapter)
        assert isinstance(pipeline.stages[1], RerankingStageAdapter)
        assert isinstance(pipeline.stages[2], GenerationStageAdapter)

    def test_build_without_retrieval(self):
        """Test building without retrieval configuration."""
        with pytest.raises(ValueError, match="Retrieval configuration is required"):
            self.builder.build()

    def test_build_without_generation(self):
        """Test building without generation configuration."""
        config = RetrievalStageConfig(
            provider="test",
            top_k=3,
            similarity_threshold=0.7,
        )
        provider = MockEmbeddingProvider()
        store = MockDocumentStore()

        self.builder.with_retrieval(
            config=config,
            embedding_provider=provider,
            document_store=store,
        )

        with pytest.raises(ValueError, match="Generation configuration is required"):
            self.builder.build()

    def test_build_invalid_name(self):
        """Test building with invalid pipeline name."""
        with pytest.raises(ValueError, match="Pipeline name is required"):
            (
                self.builder.with_retrieval(
                    config=RetrievalStageConfig(
                        provider="test",
                        top_k=3,
                        similarity_threshold=0.7,
                    ),
                    embedding_provider=MockEmbeddingProvider(),
                    document_store=MockDocumentStore(),
                )
                .with_generation(
                    config=GenerationStageConfig(
                        provider="test",
                        model="test-model",
                    ),
                    generation_provider=MockGenerationProvider(),
                )
                .build()
            )


@pytest.fixture
async def initialized_pipeline():
    """Provide initialized pipeline for tests."""
    config = RAGPipelineConfig(
        name="test_pipeline",
        type="test",
        enabled=True,
        retrieval_config=RetrievalStageConfig(
            provider="test",
            top_k=3,
            similarity_threshold=0.7,
        ),
        reranking_config=RerankingStageConfig(
            provider="test",
            top_k=3,
            score_threshold=0.5,
        ),
        generation_config=GenerationStageConfig(
            provider="test",
            model="test-model",
        ),
    )

    pipeline = RAGPipelineAdapter(
        config=config,
        embedding_provider=MockEmbeddingProvider(),
        document_store=MockDocumentStore(),
        reranker_provider=MockRerankerProvider(),
        generation_provider=MockGenerationProvider(),
    )

    yield pipeline


@pytest.mark.performance
class TestRAGPipelinePerformance:
    """Performance tests for the RAG pipeline."""

    def setup_method(self):
        """Set up test fixtures."""
        retrieval_config = RetrievalStageConfig(
            provider="test",
            top_k=3,
            similarity_threshold=0.7,
        )
        reranking_config = RerankingStageConfig(
            provider="test",
            top_k=3,
            score_threshold=0.5,
        )
        generation_config = GenerationStageConfig(
            provider="test",
            model="test-model",
        )
        self.config = RAGPipelineConfig(
            name="test_pipeline",
            type="test",
            enabled=True,
            retrieval_config=retrieval_config,
            reranking_config=reranking_config,
            generation_config=generation_config,
        )

        self.pipeline = RAGPipelineAdapter(
            config=self.config,
            embedding_provider=MockEmbeddingProvider(),
            document_store=MockDocumentStore(),
            reranker_provider=MockRerankerProvider(),
            generation_provider=MockGenerationProvider(),
        )

        # Mock the stages for fast execution
        for stage in self.pipeline.stages:
            setattr(stage, "_stage", MagicMock())
            stage_obj = getattr(stage, "_stage")
            stage_obj.process = AsyncMock(
                return_value=GenerationResult(
                    text="Generated text",
                    chunks=[
                        DocumentChunk(
                            content="test", metadata=Metadata(), document_id="1"
                        )
                    ],
                    query="test",
                )
            )

    @pytest.mark.asyncio
    async def test_response_time(self):
        """Test pipeline response time."""
        query = "test query"
        context = PipelineContext()

        start_time = time.time()
        result = await self.pipeline.execute_async(query, context)
        duration = time.time() - start_time

        assert duration < 0.1  # Response time should be under 100ms
        assert result is not None
        assert isinstance(result, GenerationResult)

    @pytest.mark.asyncio
    async def test_concurrent_execution(self):
        """Test pipeline under concurrent load."""
        num_requests = 100
        queries = ["test query" for _ in range(num_requests)]
        contexts = [PipelineContext() for _ in range(num_requests)]

        start_time = time.time()
        results = await asyncio.gather(*[
            self.pipeline.execute_async(query, context)
            for query, context in zip(queries, contexts)
        ])
        duration = time.time() - start_time

        assert duration < 5.0  # Should handle 100 requests within 5 seconds
        assert len(results) == num_requests
        assert all(isinstance(r, GenerationResult) for r in results)

    def test_memory_usage(self):
        """Test memory usage during pipeline execution."""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # Convert to MB

        # Create multiple pipeline instances
        pipelines = []
        for _ in range(10):
            pipeline = RAGPipelineAdapter(
                config=self.config,
                embedding_provider=MockEmbeddingProvider(),
                document_store=MockDocumentStore(),
                reranker_provider=MockRerankerProvider(),
                generation_provider=MockGenerationProvider(),
            )
            pipelines.append(pipeline)

        current_memory = process.memory_info().rss / 1024 / 1024
        memory_increase = current_memory - initial_memory

        assert memory_increase < 100  # Memory increase should be less than 100MB

        # Cleanup
        del pipelines
        gc.collect()

        final_memory = process.memory_info().rss / 1024 / 1024
        memory_diff = abs(final_memory - initial_memory)

        assert memory_diff < 1  # Memory should be released after cleanup


@pytest.mark.asyncio
async def test_pipeline_error_propagation():
    """Test error propagation through the pipeline stages."""
    config = RAGPipelineConfig(
        name="test_pipeline",
        type="test",
        enabled=True,
        retrieval_config=RetrievalStageConfig(
            provider="test",
            top_k=3,
            similarity_threshold=0.7,
        ),
    )

    pipeline = RAGPipelineAdapter(
        config=config,
        embedding_provider=MockEmbeddingProvider(),
        document_store=MockDocumentStore(),
    )

    # Mock stage to raise an error
    for stage in pipeline.stages:
        setattr(stage, "_stage", MagicMock())
        stage_obj = getattr(stage, "_stage")
        stage_obj.process = AsyncMock(side_effect=ValueError("Test error"))

    with pytest.raises(ValueError, match="Test error"):
        await pipeline.execute_async("test query")


@pytest.mark.asyncio
async def test_pipeline_stage_validation():
    """Test pipeline stage validation during execution."""
    config = RAGPipelineConfig(
        name="test_pipeline",
        type="test",
        enabled=True,
        retrieval_config=RetrievalStageConfig(
            provider="test",
            top_k=3,
            similarity_threshold=0.7,
        ),
    )

    pipeline = RAGPipelineAdapter(
        config=config,
        embedding_provider=MockEmbeddingProvider(),
        document_store=MockDocumentStore(),
    )

    # Mock stage to return invalid type
    for stage in pipeline.stages:
        setattr(stage, "_stage", MagicMock())
        stage_obj = getattr(stage, "_stage")
        stage_obj.process = AsyncMock(return_value="invalid result type")

    with pytest.raises(TypeError):
        await pipeline.execute_async("test query")


@pytest.mark.integration
class TestRAGPipelineIntegration:
    """Integration tests for the RAG pipeline."""

    def setup_method(self):
        """Set up test fixtures."""
        # Use mock providers for testing
        self.embedding_provider = MockEmbeddingProvider()
        self.document_store = MockDocumentStore()
        self.reranker_provider = MockRerankerProvider()
        self.generation_provider = MockGenerationProvider()

        retrieval_config = RetrievalStageConfig(
            provider="test",
            top_k=3,
            similarity_threshold=0.7,
        )
        reranking_config = RerankingStageConfig(
            provider="test",
            top_k=3,
            score_threshold=0.5,
        )
        generation_config = GenerationStageConfig(
            provider="test",
            model="test-model",
        )
        self.config = RAGPipelineConfig(
            name="test_pipeline",
            type="test",
            enabled=True,
            retrieval_config=retrieval_config,
            reranking_config=reranking_config,
            generation_config=generation_config,
        )

        self.pipeline = RAGPipelineAdapter(
            config=self.config,
            embedding_provider=self.embedding_provider,
            document_store=self.document_store,
            reranker_provider=self.reranker_provider,
            generation_provider=self.generation_provider,
        )

    @pytest.mark.asyncio
    async def test_end_to_end_flow(self):
        """Test complete pipeline flow with real components."""
        # Add test documents to store
        documents = [
            Document(
                content="This is a test document about AI.",
                metadata=Metadata(source="test"),
                id="1",
            ),
            Document(
                content="Another document about machine learning.",
                metadata=Metadata(source="test"),
                id="2",
            ),
        ]
        for doc in documents:
            await self.document_store.add_document(doc)

        # Execute pipeline
        query = "What is AI?"
        context = PipelineContext()
        result = await self.pipeline.execute_async(query, context)

        # Verify results
        assert result is not None
        assert isinstance(result, GenerationResult)
        assert result.text
        assert result.chunks
        assert len(result.chunks) > 0
        assert result.query == query

    @pytest.mark.asyncio
    async def test_stage_interaction(self):
        """Test interaction between pipeline stages with real components."""
        # Add a test document
        document = Document(
            content="AI is a field of computer science.",
            metadata=Metadata(source="test"),
            id="1",
        )
        await self.document_store.add_document(document)

        # Execute retrieval stage
        query = "What is AI?"
        context = PipelineContext()
        retrieval_result = await self.pipeline.stages[0].process(query, context)

        assert isinstance(retrieval_result, RetrievalResult)
        assert len(retrieval_result.chunks) > 0

        # Execute reranking stage
        reranking_result = await self.pipeline.stages[1].process(
            retrieval_result, context
        )

        assert isinstance(reranking_result, RerankingResult)
        assert len(reranking_result.chunks) > 0

        # Execute generation stage
        generation_result = await self.pipeline.stages[2].process(
            reranking_result, context
        )

        assert isinstance(generation_result, GenerationResult)
        assert generation_result.text
        assert generation_result.chunks
        assert generation_result.query == query

    @pytest.mark.asyncio
    async def test_context_propagation(self):
        """Test context propagation through pipeline stages."""
        # Add test document
        document = Document(
            content="Test document for context propagation.",
            metadata=Metadata(source="test"),
            id="1",
        )
        await self.document_store.add_document(document)

        # Set up context with custom data
        context = PipelineContext()
        context.set("custom_param", "test_value")
        context.set("temperature", 0.7)

        # Execute pipeline
        query = "Test query"
        result = await self.pipeline.execute_async(query, context)

        # Verify context was propagated
        assert context.get("custom_param") == "test_value"
        assert context.get("temperature") == 0.7
        assert context.get("pipeline_name") == "test_pipeline"
        assert context.get("last_stage") is not None


@pytest.mark.asyncio
async def test_pipeline_state_validation():
    """Test pipeline state validation during execution."""
    config = RAGPipelineConfig(
        name="test_pipeline",
        type="test",
        retrieval_config=RetrievalStageConfig(
            provider="test",
            top_k=3,
            similarity_threshold=0.7,
        ),
    )

    pipeline = RAGPipelineAdapter(
        config=config,
        embedding_provider=MockEmbeddingProvider(),
        document_store=MockDocumentStore(),
    )

    # Test state before execution
    assert pipeline.name == "test_pipeline"
    assert isinstance(pipeline.config, RAGPipelineConfig)
    assert len(pipeline.stages) > 0

    # Execute pipeline
    query = "test query"
    context = PipelineContext()

    # Mock stages
    for stage in pipeline.stages:
        setattr(stage, "_stage", MagicMock())
        stage_obj = getattr(stage, "_stage")
        stage_obj.process = AsyncMock(return_value=[])

    await pipeline.execute_async(query, context)

    # Verify state after execution
    assert context.get("pipeline_name") == "test_pipeline"
    assert context.get("last_stage") is not None
    assert context.get("query") == query


@pytest.mark.asyncio
async def test_pipeline_partial_configuration():
    """Test pipeline with partial stage configuration."""
    # Only retrieval stage configured
    config = RAGPipelineConfig(
        name="test_pipeline",
        type="test",
        enabled=True,
        retrieval_config=RetrievalStageConfig(
            provider="test",
            top_k=3,
            similarity_threshold=0.7,
        ),
    )

    pipeline = RAGPipelineAdapter(
        config=config,
        embedding_provider=MockEmbeddingProvider(),
        document_store=MockDocumentStore(),
    )

    assert len(pipeline.stages) == 1
    assert isinstance(pipeline.stages[0], RetrievalStageAdapter)

    # Mock the stage
    setattr(pipeline.stages[0], "_stage", MagicMock())
    stage_obj = getattr(pipeline.stages[0], "_stage")
    stage_obj.process = AsyncMock(return_value=[])

    # Should work with just retrieval stage
    result = await pipeline.execute_async("test query")
    assert result is not None


@pytest.mark.asyncio
async def test_pipeline_invalid_stage_order():
    """Test pipeline with invalid stage order configuration."""
    config = RAGPipelineConfig(
        name="test_pipeline",
        type="test",
        enabled=True,
        generation_config=GenerationStageConfig(
            provider="test",
            model="test-model",
        ),
        retrieval_config=RetrievalStageConfig(
            provider="test",
            top_k=3,
            similarity_threshold=0.7,
        ),
    )

    with pytest.raises(ValueError, match="Invalid stage order"):
        RAGPipelineAdapter(
            config=config,
            embedding_provider=MockEmbeddingProvider(),
            document_store=MockDocumentStore(),
            generation_provider=MockGenerationProvider(),
        )


class TestRAGPipelineTypeValidation:
    """Type validation tests for the RAG pipeline."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = RAGPipelineConfig(
            name="test_pipeline",
            type="test",
            enabled=True,
            retrieval_config=RetrievalStageConfig(
                provider="test",
                top_k=3,
                similarity_threshold=0.7,
            ),
        )
        self.pipeline = RAGPipelineAdapter(
            config=self.config,
            embedding_provider=MockEmbeddingProvider(),
            document_store=MockDocumentStore(),
        )

    def test_stage_protocol_compliance(self):
        """Test that all stages comply with the StageProcessor protocol."""
        for stage in self.pipeline.stages:
            assert isinstance(stage, StageProcessor)
            assert hasattr(stage, "process")
            assert callable(stage.process)

    def test_config_type_validation(self):
        """Test configuration type validation."""
        # Test with invalid config type
        with pytest.raises(TypeError):
            RAGPipelineAdapter(
                config=cast(Any, {"name": "test"}),  # type: ignore
                embedding_provider=MockEmbeddingProvider(),
                document_store=MockDocumentStore(),
            )

    def test_provider_type_validation(self):
        """Test provider type validation."""
        # Test with invalid provider types
        with pytest.raises(TypeError):
            RAGPipelineAdapter(
                config=self.config,
                embedding_provider=cast(Any, {}),  # type: ignore
                document_store=MockDocumentStore(),
            )

        with pytest.raises(TypeError):
            RAGPipelineAdapter(
                config=self.config,
                embedding_provider=MockEmbeddingProvider(),
                document_store=cast(Any, {}),  # type: ignore
            )


@pytest.mark.performance
class TestRAGPipelineResourceUsage:
    """Resource usage tests for the RAG pipeline."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = RAGPipelineConfig(
            name="test_pipeline",
            type="test",
            enabled=True,
            retrieval_config=RetrievalStageConfig(
                provider="test",
                top_k=3,
                similarity_threshold=0.7,
            ),
        )

    def test_pipeline_creation_memory(self):
        """Test memory usage during pipeline creation."""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024

        pipelines = []
        for _ in range(1000):  # Create 1000 pipeline instances
            pipeline = RAGPipelineAdapter(
                config=self.config,
                embedding_provider=MockEmbeddingProvider(),
                document_store=MockDocumentStore(),
            )
            pipelines.append(pipeline)

        current_memory = process.memory_info().rss / 1024 / 1024
        memory_per_instance = (current_memory - initial_memory) / 1000

        assert memory_per_instance < 0.1  # Each instance should use less than 0.1MB

        # Cleanup
        del pipelines
        gc.collect()

        final_memory = process.memory_info().rss / 1024 / 1024
        memory_diff = abs(final_memory - initial_memory)

        assert memory_diff < 1  # Memory should be fully released

    @pytest.mark.asyncio
    async def test_pipeline_execution_memory(self):
        """Test memory usage during pipeline execution."""
        pipeline = RAGPipelineAdapter(
            config=self.config,
            embedding_provider=MockEmbeddingProvider(),
            document_store=MockDocumentStore(),
        )

        # Mock stages for consistent memory usage
        for stage in pipeline.stages:
            setattr(stage, "_stage", MagicMock())
            stage_obj = getattr(stage, "_stage")
            stage_obj.process = AsyncMock(return_value=[])

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024

        # Execute pipeline multiple times
        for _ in range(1000):
            await pipeline.execute_async("test query")

        current_memory = process.memory_info().rss / 1024 / 1024
        memory_increase = current_memory - initial_memory

        assert memory_increase < 10  # Total memory increase should be less than 10MB


@pytest.mark.asyncio
class TestRAGPipelineLifecycle:
    """Lifecycle tests for the RAG pipeline."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = RAGPipelineConfig(
            name="test_pipeline",
            type="test",
            retrieval_config=RetrievalStageConfig(
                provider="test",
                top_k=3,
                similarity_threshold=0.7,
            ),
        )
        self.pipeline = RAGPipelineAdapter(
            config=self.config,
            embedding_provider=MockEmbeddingProvider(),
            document_store=MockDocumentStore(),
        )

    @pytest.mark.asyncio
    async def test_stage_lifecycle(self):
        """Test stage lifecycle and state transitions."""
        # Mock stages
        for stage in self.pipeline.stages:
            setattr(stage, "_stage", MagicMock())
            stage_obj = getattr(stage, "_stage")
            stage_obj.process = AsyncMock(return_value=[])

        context = PipelineContext()

        # Test initial state
        assert len(self.pipeline.stages) > 0
        assert context.get_metadata("current_stage") is None

        # Execute pipeline and check state transitions
        await self.pipeline.execute_async("test query", context)

        # Verify stage transitions
        assert context.get_metadata("current_stage") is not None
        assert context.get_metadata("current_stage") == self.pipeline.stages[-1].name
        assert context.get_metadata("stage_index") == len(self.pipeline.stages) - 1

    @pytest.mark.asyncio
    async def test_context_lifecycle(self):
        """Test context lifecycle through pipeline execution."""
        context = PipelineContext()

        # Set initial context state
        context.set("initial_param", "test_value")

        # Mock stages to modify context
        for i, stage in enumerate(self.pipeline.stages):
            setattr(stage, "_stage", MagicMock())
            stage_obj = getattr(stage, "_stage")
            stage_obj.process = AsyncMock(
                side_effect=lambda input_data, ctx: (
                    ctx.set(f"stage_{i}_param", f"value_{i}"),
                    [],
                )[-1]
            )

        # Execute pipeline
        await self.pipeline.execute_async("test query", context)

        # Verify context state transitions
        assert context.get("initial_param") == "test_value"
        for i in range(len(self.pipeline.stages)):
            assert context.get(f"stage_{i}_param") == f"value_{i}"


@pytest.mark.asyncio
class TestRAGPipelineEdgeCases:
    """Edge case tests for the RAG pipeline."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = RAGPipelineConfig(
            name="test_pipeline",
            type="test",
            retrieval_config=RetrievalStageConfig(
                provider="test",
                top_k=3,
                similarity_threshold=0.7,
            ),
        )
        self.pipeline = RAGPipelineAdapter(
            config=self.config,
            embedding_provider=MockEmbeddingProvider(),
            document_store=MockDocumentStore(),
        )

    @pytest.mark.asyncio
    async def test_empty_stage_result(self):
        """Test handling of empty results from stages."""
        # Mock stages to return empty results
        for stage in self.pipeline.stages:
            setattr(stage, "_stage", MagicMock())
            stage_obj = getattr(stage, "_stage")
            stage_obj.process = AsyncMock(return_value=[])

        result = await self.pipeline.execute_async("test query")
        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_invalid_stage_result(self):
        """Test handling of invalid results from stages."""
        # Mock stage to return invalid result type
        stage = self.pipeline.stages[0]
        setattr(stage, "_stage", MagicMock())
        stage_obj = getattr(stage, "_stage")
        stage_obj.process = AsyncMock(return_value=123)  # Invalid type

        with pytest.raises(TypeError, match="Invalid result type"):
            await self.pipeline.execute_async("test query")

    @pytest.mark.asyncio
    async def test_stage_timeout(self):
        """Test handling of stage timeout."""
        # Mock stage to simulate timeout
        stage = self.pipeline.stages[0]
        setattr(stage, "_stage", MagicMock())
        stage_obj = getattr(stage, "_stage")
        stage_obj.process = AsyncMock(side_effect=asyncio.TimeoutError())

        with pytest.raises(asyncio.TimeoutError):
            await self.pipeline.execute_async("test query")

    @pytest.mark.asyncio
    async def test_concurrent_stage_execution(self):
        """Test concurrent execution of pipeline stages."""
        num_requests = 5
        queries = ["test query" for _ in range(num_requests)]

        # Mock stages with varying delays
        for stage in self.pipeline.stages:
            setattr(stage, "_stage", MagicMock())
            stage_obj = getattr(stage, "_stage")
            stage_obj.process = AsyncMock(
                side_effect=lambda input_data, context: asyncio.sleep(0.1)
            )

        # Execute queries concurrently
        start_time = time.time()
        await asyncio.gather(*[self.pipeline.execute_async(query) for query in queries])
        duration = time.time() - start_time

        # Should take ~0.1s, not 0.5s (if truly concurrent)
        assert duration < 0.2


class TestRAGPipelineTypeSystem:
    """Type system tests for the RAG pipeline."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = RAGPipelineConfig(
            name="test_pipeline",
            type="test",
            retrieval_config=RetrievalStageConfig(
                provider="test",
                top_k=3,
                similarity_threshold=0.7,
            ),
        )
        self.pipeline = RAGPipelineAdapter(
            config=self.config,
            embedding_provider=MockEmbeddingProvider(),
            document_store=MockDocumentStore(),
        )

    def test_generic_type_compliance(self):
        """Test compliance with generic type constraints."""
        # Verify PipelineStage generic type parameters
        stage = self.pipeline.stages[0]
        assert_type(stage, PipelineStage)

        # Test with explicit type parameters
        retrieval_stage = cast(PipelineStage[str, RetrievalResult], stage)
        assert isinstance(retrieval_stage, PipelineStage)

    def test_protocol_implementations(self):
        """Test protocol implementations and runtime checks."""
        # Test StageProcessor protocol compliance
        for stage in self.pipeline.stages:
            assert isinstance(stage, StageProcessor)

            # Verify protocol attributes
            assert hasattr(stage, "process")
            assert asyncio.iscoroutinefunction(stage.process)

    def test_type_covariance(self):
        """Test type covariance in pipeline stages."""

        # Mock a derived result type
        class DerivedResult(RetrievalResult):
            pass

        # Mock stage returning derived type
        stage = self.pipeline.stages[0]
        setattr(stage, "_stage", MagicMock())
        stage_obj = getattr(stage, "_stage")
        stage_obj.process = AsyncMock(return_value=DerivedResult(chunks=[]))

        # Should accept derived type
        assert isinstance(stage_obj.process.return_value, RetrievalResult)


@pytest.mark.performance
class TestRAGPipelineResourceManagement:
    """Resource management tests for the RAG pipeline."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = RAGPipelineConfig(
            name="test_pipeline",
            type="test",
            retrieval_config=RetrievalStageConfig(
                provider="test",
                top_k=3,
                similarity_threshold=0.7,
            ),
        )

    def test_pipeline_resource_cleanup(self):
        """Test resource cleanup after pipeline operations."""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024

        # Create and destroy multiple pipelines
        for _ in range(100):
            pipeline = RAGPipelineAdapter(
                config=self.config,
                embedding_provider=MockEmbeddingProvider(),
                document_store=MockDocumentStore(),
            )
            del pipeline
            gc.collect()

        final_memory = process.memory_info().rss / 1024 / 1024
        memory_diff = abs(final_memory - initial_memory)

        assert memory_diff < 1  # Memory should be fully released

    def test_context_resource_cleanup(self):
        """Test context resource cleanup."""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024

        # Create and destroy multiple contexts with data
        for _ in range(1000):
            context = PipelineContext()
            context.set("large_data", "x" * 1000)  # Add some data
            del context
            gc.collect()

        final_memory = process.memory_info().rss / 1024 / 1024
        memory_diff = abs(final_memory - initial_memory)

        assert memory_diff < 1  # Memory should be fully released

    @pytest.mark.asyncio
    async def test_stage_resource_cleanup(self):
        """Test stage resource cleanup."""
        pipeline = RAGPipelineAdapter(
            config=self.config,
            embedding_provider=MockEmbeddingProvider(),
            document_store=MockDocumentStore(),
        )

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024

        # Execute pipeline multiple times with large data
        for _ in range(100):
            context = PipelineContext()
            context.set("large_data", "x" * 1000)

            # Mock stages
            for stage in pipeline.stages:
                setattr(stage, "_stage", MagicMock())
                stage_obj = getattr(stage, "_stage")
                stage_obj.process = AsyncMock(return_value=[])

            await pipeline.execute_async("test query", context)
            del context
            gc.collect()

        final_memory = process.memory_info().rss / 1024 / 1024
        memory_diff = abs(final_memory - initial_memory)

        assert memory_diff < 1  # Memory should be fully released


@pytest.mark.integration
class TestRAGPipelineErrorScenarios:
    """Integration tests for pipeline error scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = RAGPipelineConfig(
            name="test_pipeline",
            type="test",
            retrieval_config=RetrievalStageConfig(
                provider="test",
                top_k=3,
                similarity_threshold=0.7,
            ),
        )
        self.pipeline = RAGPipelineAdapter(
            config=self.config,
            embedding_provider=MockEmbeddingProvider(),
            document_store=MockDocumentStore(),
        )

    @pytest.mark.asyncio
    async def test_retrieval_stage_error(self):
        """Test error handling in retrieval stage."""
        # Mock retrieval stage to raise error
        stage = self.pipeline.stages[0]
        setattr(stage, "_stage", MagicMock())
        stage_obj = getattr(stage, "_stage")
        stage_obj.process = AsyncMock(side_effect=ValueError("Retrieval error"))

        context = PipelineContext()
        with pytest.raises(ValueError, match="Retrieval error"):
            await self.pipeline.execute_async("test query", context)

        # Verify error is recorded in context
        assert context.get_metadata("error_stage") == "test_retrieval"
        assert "Retrieval error" in str(context.get_metadata("error_message"))

    @pytest.mark.asyncio
    async def test_document_store_error(self):
        """Test error handling when document store fails."""
        # Mock document store to raise error
        document_store = MockDocumentStore()
        document_store.search = AsyncMock(
            side_effect=ConnectionError("DB connection failed")
        )

        pipeline = RAGPipelineAdapter(
            config=self.config,
            embedding_provider=MockEmbeddingProvider(),
            document_store=document_store,
        )

        with pytest.raises(ConnectionError, match="DB connection failed"):
            await pipeline.execute_async("test query")

    @pytest.mark.asyncio
    async def test_embedding_provider_error(self):
        """Test error handling when embedding provider fails."""
        # Mock embedding provider to raise error
        embedding_provider = MockEmbeddingProvider()
        embedding_provider.embed_query = AsyncMock(
            side_effect=RuntimeError("Embedding service unavailable")
        )

        pipeline = RAGPipelineAdapter(
            config=self.config,
            embedding_provider=embedding_provider,
            document_store=MockDocumentStore(),
        )

        with pytest.raises(RuntimeError, match="Embedding service unavailable"):
            await pipeline.execute_async("test query")


class TestRAGPipelineConfiguration:
    """Tests for pipeline configuration validation."""

    def test_invalid_retrieval_config(self):
        """Test validation of invalid retrieval configuration."""
        config = RAGPipelineConfig(
            name="test_pipeline",
            type="test",
            retrieval_config=RetrievalStageConfig(
                provider="test",
                top_k=-1,  # Invalid value
                similarity_threshold=0.7,
            ),
        )

        with pytest.raises(ValueError, match="top_k must be positive"):
            RAGPipelineAdapter(
                config=config,
                embedding_provider=MockEmbeddingProvider(),
                document_store=MockDocumentStore(),
            )

    def test_invalid_reranking_config(self):
        """Test validation of invalid reranking configuration."""
        config = RAGPipelineConfig(
            name="test_pipeline",
            type="test",
            retrieval_config=RetrievalStageConfig(
                provider="test",
                top_k=3,
                similarity_threshold=0.7,
            ),
            reranking_config=RerankingStageConfig(
                provider="test",
                top_k=5,  # Invalid: larger than retrieval top_k
                score_threshold=0.5,
            ),
        )

        with pytest.raises(
            ValueError, match="Reranking top_k cannot be larger than retrieval top_k"
        ):
            RAGPipelineAdapter(
                config=config,
                embedding_provider=MockEmbeddingProvider(),
                document_store=MockDocumentStore(),
                reranker_provider=MockRerankerProvider(),
            )

    def test_invalid_generation_config(self):
        """Test validation of invalid generation configuration."""
        config = RAGPipelineConfig(
            name="test_pipeline",
            type="test",
            retrieval_config=RetrievalStageConfig(
                provider="test",
                top_k=3,
                similarity_threshold=0.7,
            ),
            generation_config=GenerationStageConfig(
                provider="test",
                model="",  # Invalid: empty model name
            ),
        )

        with pytest.raises(ValueError, match="Model name cannot be empty"):
            RAGPipelineAdapter(
                config=config,
                embedding_provider=MockEmbeddingProvider(),
                document_store=MockDocumentStore(),
                generation_provider=MockGenerationProvider(),
            )


class TestRAGPipelineStageComposition:
    """Tests for pipeline stage composition."""

    def setup_method(self):
        """Set up test fixtures."""
        self.retrieval_config = RetrievalStageConfig(
            provider="test",
            top_k=3,
            similarity_threshold=0.7,
        )
        self.reranking_config = RerankingStageConfig(
            provider="test",
            top_k=3,
            score_threshold=0.5,
        )
        self.generation_config = GenerationStageConfig(
            provider="test",
            model="test-model",
        )

    def test_retrieval_only_pipeline(self):
        """Test pipeline with only retrieval stage."""
        config = RAGPipelineConfig(
            name="test_pipeline",
            type="test",
            retrieval_config=self.retrieval_config,
        )

        pipeline = RAGPipelineAdapter(
            config=config,
            embedding_provider=MockEmbeddingProvider(),
            document_store=MockDocumentStore(),
        )

        assert len(pipeline.stages) == 1
        assert isinstance(pipeline.stages[0], RetrievalStageAdapter)

    def test_retrieval_reranking_pipeline(self):
        """Test pipeline with retrieval and reranking stages."""
        config = RAGPipelineConfig(
            name="test_pipeline",
            type="test",
            retrieval_config=self.retrieval_config,
            reranking_config=self.reranking_config,
        )

        pipeline = RAGPipelineAdapter(
            config=config,
            embedding_provider=MockEmbeddingProvider(),
            document_store=MockDocumentStore(),
            reranker_provider=MockRerankerProvider(),
        )

        assert len(pipeline.stages) == 2
        assert isinstance(pipeline.stages[0], RetrievalStageAdapter)
        assert isinstance(pipeline.stages[1], RerankingStageAdapter)

    def test_full_pipeline(self):
        """Test pipeline with all stages."""
        config = RAGPipelineConfig(
            name="test_pipeline",
            type="test",
            retrieval_config=self.retrieval_config,
            reranking_config=self.reranking_config,
            generation_config=self.generation_config,
        )

        pipeline = RAGPipelineAdapter(
            config=config,
            embedding_provider=MockEmbeddingProvider(),
            document_store=MockDocumentStore(),
            reranker_provider=MockRerankerProvider(),
            generation_provider=MockGenerationProvider(),
        )

        assert len(pipeline.stages) == 3
        assert isinstance(pipeline.stages[0], RetrievalStageAdapter)
        assert isinstance(pipeline.stages[1], RerankingStageAdapter)
        assert isinstance(pipeline.stages[2], GenerationStageAdapter)


@pytest.mark.performance
class TestRAGPipelineMemoryLeaks:
    """Tests for memory leaks in pipeline operations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = RAGPipelineConfig(
            name="test_pipeline",
            type="test",
            retrieval_config=RetrievalStageConfig(
                provider="test",
                top_k=3,
                similarity_threshold=0.7,
            ),
        )

    @pytest.mark.asyncio
    async def test_repeated_pipeline_creation(self):
        """Test memory usage with repeated pipeline creation and destruction."""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024

        for _ in range(1000):
            pipeline = RAGPipelineAdapter(
                config=self.config,
                embedding_provider=MockEmbeddingProvider(),
                document_store=MockDocumentStore(),
            )
            await pipeline.execute_async("test query")
            del pipeline
            gc.collect()

        final_memory = process.memory_info().rss / 1024 / 1024
        memory_diff = abs(final_memory - initial_memory)

        assert memory_diff < 1  # Memory should be fully released

    @pytest.mark.asyncio
    async def test_large_document_processing(self):
        """Test memory usage with large document processing."""
        document_store = MockDocumentStore()
        pipeline = RAGPipelineAdapter(
            config=self.config,
            embedding_provider=MockEmbeddingProvider(),
            document_store=document_store,
        )

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024

        # Process large documents
        for _ in range(100):
            large_doc = Document(
                content="x" * 1000000,  # 1MB of text
                metadata=Metadata(),
                id="test",
            )
            await document_store.add_document(large_doc)
            await pipeline.execute_async("test query")
            del large_doc
            gc.collect()

        final_memory = process.memory_info().rss / 1024 / 1024
        memory_diff = abs(final_memory - initial_memory)

        assert memory_diff < 10  # Memory increase should be limited

    @pytest.mark.asyncio
    async def test_concurrent_memory_usage(self):
        """Test memory usage under concurrent load."""
        pipeline = RAGPipelineAdapter(
            config=self.config,
            embedding_provider=MockEmbeddingProvider(),
            document_store=MockDocumentStore(),
        )

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024

        # Execute concurrent requests
        num_requests = 100
        queries = ["test query" for _ in range(num_requests)]
        contexts = [PipelineContext() for _ in range(num_requests)]

        # Mock stages for consistent memory usage
        for stage in pipeline.stages:
            setattr(stage, "_stage", MagicMock())
            stage_obj = getattr(stage, "_stage")
            stage_obj.process = AsyncMock(return_value=[])

        await asyncio.gather(*[
            pipeline.execute_async(query, context)
            for query, context in zip(queries, contexts)
        ])

        # Force garbage collection
        del contexts
        gc.collect()

        final_memory = process.memory_info().rss / 1024 / 1024
        memory_diff = abs(final_memory - initial_memory)

        assert memory_diff < 5  # Memory increase should be limited
