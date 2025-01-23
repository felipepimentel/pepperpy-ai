"""Tests for the agent factory and dependency injection system."""

import pytest
from typing import Any, Dict, Optional

from pepperpy.interfaces import (
    LLMProvider,
    VectorStoreProvider,
    EmbeddingProvider,
)
from pepperpy.agents.base import BaseAgent
from pepperpy.agents.factory import AgentFactory

class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing."""
    
    def __init__(self):
        """Initialize the mock provider."""
        self.initialized = False
        self.cleaned_up = False
    
    async def initialize(self) -> None:
        """Initialize the provider."""
        self.initialized = True
    
    async def cleanup(self) -> None:
        """Clean up the provider."""
        self.cleaned_up = True
    
    async def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate text."""
        return f"Mock response to: {prompt}"

class MockVectorStoreProvider(VectorStoreProvider):
    """Mock vector store provider for testing."""
    
    def __init__(self):
        """Initialize the mock provider."""
        self.initialized = False
        self.cleaned_up = False
        self.stored_vectors: Dict[str, Any] = {}
    
    async def initialize(self) -> None:
        """Initialize the provider."""
        self.initialized = True
    
    async def cleanup(self) -> None:
        """Clean up the provider."""
        self.cleaned_up = True
    
    async def store(self, vectors: Dict[str, Any]) -> None:
        """Store vectors."""
        self.stored_vectors.update(vectors)
    
    async def query(self, query: Any, **kwargs: Any) -> Dict[str, Any]:
        """Query vectors."""
        return {"query": query, "results": self.stored_vectors}

class MockEmbeddingProvider(EmbeddingProvider):
    """Mock embedding provider for testing."""
    
    def __init__(self):
        """Initialize the mock provider."""
        self.initialized = False
        self.cleaned_up = False
    
    async def initialize(self) -> None:
        """Initialize the provider."""
        self.initialized = True
    
    async def cleanup(self) -> None:
        """Clean up the provider."""
        self.cleaned_up = True
    
    async def embed(self, text: str) -> Dict[str, Any]:
        """Generate embeddings."""
        return {"text": text, "embedding": [0.1, 0.2, 0.3]}

@BaseAgent.register("mock")
class MockAgent(BaseAgent):
    """Mock agent for testing."""
    
    async def process(self, input_data: Any) -> Any:
        """Process input data."""
        response = await self.llm.generate(str(input_data))
        
        if self.vector_store:
            await self.vector_store.store({"input": input_data})
            results = await self.vector_store.query(input_data)
            response += f"\nVector store results: {results}"
            
        if self.embeddings:
            embedding = await self.embeddings.embed(str(input_data))
            response += f"\nEmbedding: {embedding}"
            
        return response

@pytest.fixture
def factory():
    """Create an agent factory for testing."""
    return AgentFactory()

@pytest.fixture
def llm_provider():
    """Create a mock LLM provider."""
    return MockLLMProvider()

@pytest.fixture
def vector_store():
    """Create a mock vector store provider."""
    return MockVectorStoreProvider()

@pytest.fixture
def embeddings():
    """Create a mock embeddings provider."""
    return MockEmbeddingProvider()

@pytest.mark.asyncio
async def test_minimal_agent_creation(factory, llm_provider):
    """Test creating an agent with only required dependencies."""
    # Configure factory
    factory.with_llm(llm_provider)
    
    # Create agent
    agent = await factory.create(
        "mock",
        capabilities={},
        config={}
    )
    
    # Verify dependencies
    assert agent.llm is llm_provider
    assert agent.vector_store is None
    assert agent.embeddings is None
    assert agent.is_initialized
    assert llm_provider.initialized

@pytest.mark.asyncio
async def test_full_agent_creation(factory, llm_provider, vector_store, embeddings):
    """Test creating an agent with all dependencies."""
    # Configure factory
    (factory
        .with_llm(llm_provider)
        .with_vector_store(vector_store)
        .with_embeddings(embeddings)
    )
    
    # Create agent
    agent = await factory.create(
        "mock",
        capabilities={},
        config={}
    )
    
    # Verify dependencies
    assert agent.llm is llm_provider
    assert agent.vector_store is vector_store
    assert agent.embeddings is embeddings
    assert agent.is_initialized
    assert llm_provider.initialized
    assert vector_store.initialized
    assert embeddings.initialized

@pytest.mark.asyncio
async def test_agent_cleanup(factory, llm_provider, vector_store, embeddings):
    """Test agent cleanup properly cleans up dependencies."""
    # Configure factory
    (factory
        .with_llm(llm_provider)
        .with_vector_store(vector_store)
        .with_embeddings(embeddings)
    )
    
    # Create and cleanup agent
    agent = await factory.create(
        "mock",
        capabilities={},
        config={}
    )
    await agent.cleanup()
    
    # Verify cleanup
    assert not agent.is_initialized
    assert llm_provider.cleaned_up
    assert vector_store.cleaned_up
    assert embeddings.cleaned_up

@pytest.mark.asyncio
async def test_agent_processing(factory, llm_provider, vector_store, embeddings):
    """Test agent processing uses all dependencies correctly."""
    # Configure factory
    (factory
        .with_llm(llm_provider)
        .with_vector_store(vector_store)
        .with_embeddings(embeddings)
    )
    
    # Create agent
    agent = await factory.create(
        "mock",
        capabilities={},
        config={}
    )
    
    # Process input
    result = await agent.process("test input")
    
    # Verify all providers were used
    assert "Mock response to: test input" in result
    assert "Vector store results:" in result
    assert "Embedding:" in result
    assert "test input" in vector_store.stored_vectors

@pytest.mark.asyncio
async def test_missing_llm_provider(factory):
    """Test error when LLM provider is missing."""
    with pytest.raises(ValueError, match="LLM provider not set"):
        await factory.create(
            "mock",
            capabilities={},
            config={}
        )

@pytest.mark.asyncio
async def test_invalid_agent_type(factory, llm_provider):
    """Test error when agent type is invalid."""
    factory.with_llm(llm_provider)
    
    with pytest.raises(ValueError, match="Agent 'invalid' not registered"):
        await factory.create(
            "invalid",
            capabilities={},
            config={}
        ) 