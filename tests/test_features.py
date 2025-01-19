"""Tests for conversation, memory, and RAG features."""

import os
from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any, Dict

import pytest

from pepperpy.data_stores.chunking import Chunk
from pepperpy.data_stores.conversation import Conversation, Message, MessageRole
from pepperpy.data_stores.memory import MemoryManager
from pepperpy.data_stores.rag import RAGManager
from pepperpy.llms.base_llm import BaseLLM
from pepperpy.llms.types import LLMResponse, ProviderConfig


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
async def conversation() -> AsyncIterator[Conversation]:
    """Create test conversation."""
    conv = Conversation(max_messages=5)
    yield conv
    conv.clear_history()


@pytest.fixture
async def memory_manager() -> AsyncIterator[MemoryManager]:
    """Create test memory manager."""
    manager = MemoryManager()
    yield manager
    manager.clear_history()


@pytest.fixture
async def rag_manager() -> AsyncIterator[RAGManager]:
    """Create test RAG manager."""
    manager = RAGManager(
        llm=MockLLM(ProviderConfig(
            type="mock",
            model_name="mock-model",
            api_key="test"
        ))
    )
    yield manager
    await manager.cleanup()


def test_conversation_features(conversation: Conversation) -> None:
    """Test conversation features."""
    # Add messages
    message = conversation.add_message(
        content="Test message",
        role=MessageRole.USER,
        metadata={"test": True}
    )

    assert isinstance(message, Message)
    assert message.content == "Test message"
    assert message.role == MessageRole.USER
    assert message.metadata["test"] is True
    assert isinstance(message.timestamp, datetime)

    # Get context
    context = conversation.get_context_window(include_metadata=True)
    assert len(context) == 1
    assert context[0]["content"] == "Test message"
    assert context[0]["metadata"]["test"] is True

    # Clear history
    conversation.clear_history()
    assert len(conversation.messages) == 0


def test_memory_features(memory_manager: MemoryManager) -> None:
    """Test memory features."""
    # Add message
    message = memory_manager.add_message(
        content="Test message",
        role=MessageRole.USER,
        metadata={"test": True}
    )

    assert isinstance(message, Message)
    assert message.content == "Test message"
    assert message.role == MessageRole.USER
    assert message.metadata["test"] is True

    # Get context
    context = memory_manager.get_context_window(include_metadata=True)
    assert len(context) == 1
    assert context[0]["content"] == "Test message"
    assert context[0]["metadata"]["test"] is True

    # Clear history
    memory_manager.clear_history()
    assert len(memory_manager.get_context_window()) == 0


async def test_rag_features(rag_manager: RAGManager) -> None:
    """Test RAG features."""
    # Add document
    await rag_manager.add_document(
        content="Test content",
        doc_id="test-doc",
        metadata={"type": "test"}
    )

    # Save documents
    await rag_manager.save_documents("test_documents.json")

    # Load documents
    await rag_manager.load_documents("test_documents.json")

    # Query
    chunks = await rag_manager.query("test query")
    assert isinstance(chunks, list)
    assert len(chunks) > 0
    assert isinstance(chunks[0], Chunk)

    # Generate with context
    response = await rag_manager.generate_with_context(
        query="test query",
        prompt_template="Context: {context}\nQuery: {query}"
    )
    assert isinstance(response, LLMResponse)
    assert response.text == "Mock response"

    # Clean up
    os.remove("test_documents.json") 