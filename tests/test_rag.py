"""Test RAG functionality."""

from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any, Sequence

import pytest
from unittest.mock import AsyncMock, patch

from pepperpy.persistence.storage.chunking import Chunk
from pepperpy.persistence.storage.rag import BaseVectorStore, Document, RAGManager
from pepperpy.providers.llm.base import BaseLLM
from pepperpy.providers.llm.types import LLMResponse, ProviderConfig


class MockVectorStore(BaseVectorStore):
    """Mock vector store for testing."""

    def __init__(self) -> None:
        """Initialize mock store."""
        self.embeddings: list[tuple[str, Sequence[float], dict[str, Any]]] = []

    async def add_embeddings(
        self,
        texts: list[str],
        metadata: list[dict[str, Any]]
    ) -> None:
        """Add embeddings to store."""
        for text, meta in zip(texts, metadata, strict=True):
            self.embeddings.append((text, [0.1, 0.2, 0.3], meta))

    async def search(
        self,
        query: str,
        limit: int = 5,
        min_score: float = 0.0
    ) -> list[tuple[str, float, dict[str, Any]]]:
        """Search for similar embeddings."""
        return [(text, 0.9, meta) for text, _, meta in self.embeddings[:limit]]

    async def clear(self) -> None:
        """Clear all embeddings."""
        self.embeddings.clear()


class MockLLM(BaseLLM):
    """Mock LLM for testing."""

    def __init__(self, config: ProviderConfig) -> None:
        """Initialize mock LLM."""
        super().__init__(config)
        self.cleaned_up = False

    async def initialize(self) -> None:
        """Initialize LLM."""
        self.is_initialized = True

    async def cleanup(self) -> None:
        """Clean up resources."""
        self.cleaned_up = True

    async def generate(self, prompt: str) -> LLMResponse:
        """Generate mock response."""
        return LLMResponse(
            text="Mock response",
            tokens_used=10,
            finish_reason="length",
            model_name="mock-model",
            cost=0.0,
            timestamp=datetime.utcnow(),
            metadata={}
        )

    async def generate_stream(self, prompt: str) -> AsyncIterator[str]:
        """Generate mock stream."""
        yield "Mock"
        yield " "
        yield "response"

    async def get_embedding(self, text: str) -> list[float]:
        """Get mock embedding."""
        return [0.1, 0.2, 0.3]


@pytest.fixture
async def rag_manager() -> AsyncIterator[RAGManager]:
    """Create test RAG manager."""
    manager = RAGManager(
        vector_store=MockVectorStore(),
        llm=MockLLM(ProviderConfig(
            type="mock",
            model_name="mock-model",
            api_key="test"
        ))
    )
    yield manager
    await manager.cleanup()


async def test_add_document(rag_manager: RAGManager) -> None:
    """Test document addition."""
    await rag_manager.add_document(
        content="Test content",
        doc_id="test-doc",
        metadata={"type": "test"}
    )

    assert "test-doc" in rag_manager.documents
    doc = rag_manager.documents["test-doc"]
    assert isinstance(doc, Document)
    assert doc.content == "Test content"
    assert doc.metadata["type"] == "test"


async def test_query(rag_manager: RAGManager) -> None:
    """Test document querying."""
    await rag_manager.add_document(
        content="Test content",
        doc_id="test-doc"
    )

    # Query
    chunks = await rag_manager.query("test query")
    assert isinstance(chunks, list)
    assert len(chunks) > 0
    assert isinstance(chunks[0], Chunk)


async def test_generate_with_context(rag_manager: RAGManager) -> None:
    """Test response generation with context."""
    await rag_manager.add_document(
        content="Test content",
        doc_id="test-doc"
    )

    # Generate with context
    response = await rag_manager.generate_with_context(
        query="test query",
        prompt_template="Context: {context}\nQuery: {query}"
    )

    assert isinstance(response, LLMResponse)
    assert response.text == "Mock response" 