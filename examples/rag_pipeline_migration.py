#!/usr/bin/env python3
"""Example of migrating a RAG pipeline to the unified pipeline framework.

This example demonstrates the process of migrating an existing RAG pipeline
implementation to use the new unified pipeline framework through the adapter
pattern.
"""

import asyncio
import logging
from typing import List

from pepperpy.core.pipeline.base import PipelineContext
from pepperpy.llm.generation import GenerationProvider
from pepperpy.llm.reranking import RerankerProvider
from pepperpy.llm.utils import Prompt, Response
from pepperpy.rag.document import DocumentStore
from pepperpy.rag.document.core import DocumentChunk
from pepperpy.rag.embedding import EmbeddingProvider
from pepperpy.rag.pipeline.adapter import (
    RAGPipelineBuilderAdapter,
)
from pepperpy.rag.pipeline.stages.generation import GenerationStageConfig
from pepperpy.rag.pipeline.stages.reranking import RerankingStageConfig
from pepperpy.rag.pipeline.stages.retrieval import RetrievalStageConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Mock implementations for demo purposes
class MockEmbeddingProvider(EmbeddingProvider):
    """Mock embedding provider for demonstration."""

    async def embed_query(self, query: str, metadata=None):
        """Mock query embedding."""
        logger.info(f"Embedding query: {query}")
        return [0.1, 0.2, 0.3, 0.4, 0.5]

    async def embed_documents(self, documents: List[str], metadata=None):
        """Mock document embedding."""
        logger.info(f"Embedding {len(documents)} documents")
        return [[0.1, 0.2, 0.3, 0.4, 0.5] for _ in documents]


class MockDocumentStore(DocumentStore):
    """Mock document store for demonstration."""

    async def search(self, embedding, filters=None, limit=3):
        """Mock document search."""
        logger.info(f"Searching documents with limit {limit}")
        return [
            DocumentChunk(
                id=f"doc_{i}",
                content=f"This is document {i} content.",
                metadata={"source": f"source_{i}"},
            )
            for i in range(limit)
        ]


class MockRerankerProvider(RerankerProvider):
    """Mock reranker provider for demonstration."""

    async def rerank(self, query: str, chunks: List[DocumentChunk], metadata=None):
        """Mock reranking."""
        logger.info(f"Reranking {len(chunks)} chunks for query: {query}")
        # Return chunks in reverse order to demonstrate reranking
        return list(reversed(chunks))


class MockGenerationProvider(GenerationProvider):
    """Mock generation provider for demonstration."""

    async def generate(self, prompt: Prompt, metadata=None):
        """Mock generation."""
        logger.info(
            f"Generating response to prompt with {len(prompt.messages)} messages"
        )
        # Create a simple response based on the prompt
        query = next((m.content for m in prompt.messages if m.role == "user"), "")
        return Response(
            text=f"This is a response to the query: {query}",
            model="mock-model",
            usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        )


async def run_example():
    """Run the example."""
    logger.info("Starting RAG pipeline migration example")

    # Create provider instances
    embedding_provider = MockEmbeddingProvider()
    document_store = MockDocumentStore()
    reranker_provider = MockRerankerProvider()
    generation_provider = MockGenerationProvider()

    # Configure stage configs
    retrieval_config = RetrievalStageConfig(
        provider="mock",
        top_k=3,
        similarity_threshold=0.7,
    )

    reranking_config = RerankingStageConfig(
        provider="mock",
        top_k=2,
        score_threshold=0.5,
    )

    generation_config = GenerationStageConfig(
        provider="mock",
        model="mock-model",
        temperature=0.7,
        system_message="You are a helpful assistant that answers questions based on retrieved documents.",
    )

    # Build the pipeline using the adapter
    logger.info("Building RAG pipeline using the adapter")
    pipeline = (
        RAGPipelineBuilderAdapter()
        .with_name("example_rag_pipeline")
        .with_retrieval(
            config=retrieval_config,
            embedding_provider=embedding_provider,
            document_store=document_store,
        )
        .with_reranking(
            config=reranking_config,
            reranker_provider=reranker_provider,
        )
        .with_generation(
            config=generation_config,
            generation_provider=generation_provider,
        )
        .build()
    )

    # Create a context with metadata
    context = PipelineContext()
    context.set("metadata", {"user_id": "user_123", "session_id": "session_456"})

    # Execute the pipeline
    query = "What is the capital of France?"
    logger.info(f"Executing pipeline with query: {query}")

    response = await pipeline.execute_async(query, context)

    # Print the results
    logger.info(f"Response: {response.text}")
    logger.info(f"Model: {response.model}")
    logger.info(f"Usage: {response.usage}")

    # Show context values
    logger.info("Context values after execution:")
    for key in context.keys():
        value = context.get(key)
        value_str = str(value)
        if len(value_str) > 100:
            value_str = value_str[:100] + "..."
        logger.info(f"  {key}: {value_str}")


if __name__ == "__main__":
    asyncio.run(run_example())
