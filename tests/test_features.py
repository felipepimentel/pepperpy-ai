"""Tests for conversation, memory, and RAG features."""

import json
import os
from datetime import datetime
from typing import AsyncGenerator, Dict, List, Any, AsyncIterator

import pytest
from pepperpy.data_stores.conversation import Conversation, Message, MessageRole
from pepperpy.data_stores.memory import MemoryManager
from pepperpy.data_stores.rag import RAGManager
from pepperpy.data_stores.chunking import ChunkManager
from pepperpy.llms.base_llm import BaseLLM
from pepperpy.llms.types import LLMResponse, ProviderConfig


class MockLLM(BaseLLM):
    """Mock LLM for testing."""

    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)
        self.is_initialized = False

    async def initialize(self) -> None:
        self.is_initialized = True

    async def cleanup(self) -> None:
        self.is_initialized = False

    async def generate(self, prompt: str) -> LLMResponse:
        return LLMResponse(
            text="Mock response",
            tokens_used=10,
            cost=0.001,
            model_name="mock-model",
            timestamp=datetime.now()
        )

    async def generate_stream(self, prompt: str) -> AsyncIterator[str]:
        yield "Mock"
        yield " "
        yield "response"

    async def get_embedding(self, text: str) -> List[float]:
        return [0.1, 0.2, 0.3]


@pytest.fixture
async def mock_llm() -> AsyncIterator[MockLLM]:
    """Create a mock LLM."""
    config = ProviderConfig(
        type="mock",
        model_name="mock-model",
        api_key="mock-key",
        temperature=0.7,
        max_tokens=1000
    )
    llm = MockLLM(config)
    await llm.initialize()
    yield llm
    await llm.cleanup()


@pytest.fixture
def conversation() -> Conversation:
    """Create a conversation."""
    return Conversation()


@pytest.fixture
async def memory_manager() -> AsyncIterator[MemoryManager]:
    """Create a memory manager."""
    manager = MemoryManager()
    yield manager
    await manager.cleanup()


@pytest.fixture
async def rag_manager(mock_llm: MockLLM) -> AsyncIterator[RAGManager]:
    """Create a RAG manager."""
    manager = RAGManager(
        llm=mock_llm,
        chunk_manager=ChunkManager()
    )
    yield manager
    await manager.cleanup()


async def test_conversation_management(conversation: Conversation) -> None:
    """Test conversation management."""
    # Add messages
    conversation.add_message(
        Message(
            role=MessageRole.SYSTEM,
            content="You are a helpful assistant.",
            timestamp=datetime.now()
        )
    )
    conversation.add_message(
        Message(
            role=MessageRole.USER,
            content="Hello!",
            timestamp=datetime.now()
        )
    )
    conversation.add_message(
        Message(
            role=MessageRole.ASSISTANT,
            content="Hi there!",
            timestamp=datetime.now()
        )
    )

    # Check message roles
    assert len(conversation.messages) == 3
    assert conversation.messages[0].role == MessageRole.SYSTEM
    assert conversation.messages[1].role == MessageRole.USER
    assert conversation.messages[2].role == MessageRole.ASSISTANT

    # Save and load conversation
    conversation.save_to_json("test_conversation.json")
    loaded_conversation = Conversation.load_from_json("test_conversation.json")
    assert len(loaded_conversation.messages) == 3
    assert loaded_conversation.messages[0].role == MessageRole.SYSTEM

    # Clean up
    os.remove("test_conversation.json")


async def test_memory_management(memory_manager: MemoryManager) -> None:
    """Test memory management."""
    # Add memories
    await memory_manager.add_memory(
        content="User likes Python",
        importance=0.8,
        metadata={"type": "preference"}
    )
    await memory_manager.add_memory(
        content="User is learning AI",
        importance=0.9,
        metadata={"type": "activity"}
    )

    # Query memories
    memories = await memory_manager.query(
        "What does the user like?",
        limit=5
    )
    assert len(memories) > 0

    # Save and load memories
    await memory_manager.save_memories("test_memories.json")
    await memory_manager.load_memories("test_memories.json")
    assert len(await memory_manager.query("", limit=10)) > 0

    # Clean up
    os.remove("test_memories.json")


async def test_rag_management(rag_manager: RAGManager) -> None:
    """Test RAG management."""
    # Add document
    await rag_manager.add_document(
        content="PepperPy is a Python framework for AI agents.",
        doc_id="doc1",
        metadata={"type": "documentation"}
    )

    # Generate with context
    response = await rag_manager.generate_with_context(
        query="What is PepperPy?",
        prompt_template=(
            "Based on the following context, answer the question:\n\n"
            "Context:\n{context}\n\n"
            "Question: {query}\n\n"
            "Answer:"
        )
    )
    assert isinstance(response, LLMResponse)
    assert response.text == "Mock response"

    # Save and load documents
    await rag_manager.save_documents("test_documents.json")
    await rag_manager.load_documents("test_documents.json")
    assert len(rag_manager.documents) > 0

    # Clean up
    os.remove("test_documents.json") 