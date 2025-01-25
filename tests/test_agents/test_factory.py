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
    """Mock LLM provider."""
    
    def __init__(self):
        """Initialize provider."""
        self._initialized = False
        self._cleaned_up = False
        
    @property
    def name(self) -> str:
        """Get provider name."""
        return "mock_llm"
        
    @property
    def config(self) -> dict:
        """Get provider configuration."""
        return {}
        
    @property
    def is_initialized(self) -> bool:
        """Whether provider is initialized."""
        return self._initialized
        
    async def initialize(self) -> None:
        """Initialize provider."""
        self._initialized = True
    
    async def cleanup(self) -> None:
        """Clean up provider."""
        self._cleaned_up = True
        
    def validate(self) -> None:
        """Validate provider state."""
        pass
        
    async def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate text."""
        return "mock response"

class MockVectorStoreProvider(VectorStoreProvider):
    """Mock vector store provider."""
    
    def __init__(self):
        """Initialize provider."""
        self._initialized = False
        self._cleaned_up = False
        
    @property
    def name(self) -> str:
        """Get provider name."""
        return "mock_vector_store"
        
    @property
    def config(self) -> dict:
        """Get provider configuration."""
        return {}
        
    @property
    def is_initialized(self) -> bool:
        """Whether provider is initialized."""
        return self._initialized
        
    async def initialize(self) -> None:
        """Initialize provider."""
        self._initialized = True
    
    async def cleanup(self) -> None:
        """Clean up provider."""
        self._cleaned_up = True
        
    def validate(self) -> None:
        """Validate provider state."""
        pass
        
    async def store(self, vectors: Dict[str, Any]) -> None:
        """Store vectors."""
        pass
        
    async def query(self, query: Any, **kwargs: Any) -> Dict[str, Any]:
        """Query vectors."""
        return {"mock": "results"}

class MockEmbeddingProvider(EmbeddingProvider):
    """Mock embedding provider."""
    
    def __init__(self):
        """Initialize provider."""
        self._initialized = False
        self._cleaned_up = False
        
    @property
    def name(self) -> str:
        """Get provider name."""
        return "mock_embeddings"
        
    @property
    def config(self) -> dict:
        """Get provider configuration."""
        return {}
        
    @property
    def is_initialized(self) -> bool:
        """Whether provider is initialized."""
        return self._initialized
        
    async def initialize(self) -> None:
        """Initialize provider."""
        self._initialized = True
    
    async def cleanup(self) -> None:
        """Clean up provider."""
        self._cleaned_up = True
        
    def validate(self) -> None:
        """Validate provider state."""
        pass
        
    async def embed(self, text: str) -> Dict[str, Any]:
        """Generate embeddings."""
        return {"mock": "embeddings"}

@BaseAgent.register("mock")
class MockAgent(BaseAgent):
    """Mock agent."""
    
    async def process(self, input_data: Any) -> Any:
        """Process input data."""
        return "mock result"

@pytest.fixture
def factory():
    """Create agent factory."""
    return AgentFactory()

@pytest.fixture
def llm_provider():
    """Create mock LLM provider."""
    return MockLLMProvider()

@pytest.fixture
def vector_store():
    """Create mock vector store provider."""
    return MockVectorStoreProvider()

@pytest.fixture
def embeddings():
    """Create mock embeddings provider."""
    return MockEmbeddingProvider()

@pytest.mark.asyncio
async def test_minimal_agent_creation(factory, llm_provider):
    """Test creating agent with minimal dependencies."""
    # Configure factory
    factory.with_llm(llm_provider)
    
    # Create agent
    agent = await factory.create(
        agent_type="mock",
        capabilities={},
        config={"name": "test"},
    )
    
    # Verify agent
    assert agent.is_initialized
    assert agent.name == "test"
    assert agent.llm == llm_provider
    assert agent.vector_store is None
    assert agent.embeddings is None

@pytest.mark.asyncio
async def test_full_agent_creation(factory, llm_provider, vector_store, embeddings):
    """Test creating agent with all dependencies."""
    # Configure factory
    factory.with_llm(llm_provider)
    factory.with_vector_store(vector_store)
    factory.with_embeddings(embeddings)
    
    # Create agent
    agent = await factory.create(
        agent_type="mock",
        capabilities={},
        config={"name": "test"},
    )
    
    # Verify agent
    assert agent.is_initialized
    assert agent.name == "test"
    assert agent.llm == llm_provider
    assert agent.vector_store == vector_store
    assert agent.embeddings == embeddings

@pytest.mark.asyncio
async def test_agent_cleanup(factory, llm_provider, vector_store, embeddings):
    """Test agent cleanup."""
    # Configure factory
    factory.with_llm(llm_provider)
    factory.with_vector_store(vector_store)
    factory.with_embeddings(embeddings)
    
    # Create and cleanup agent
    agent = await factory.create(
        agent_type="mock",
        capabilities={},
        config={"name": "test"},
    )
    await agent.cleanup()
    
    # Verify cleanup
    assert not agent.is_initialized
    assert llm_provider._cleaned_up
    assert vector_store._cleaned_up
    assert embeddings._cleaned_up

@pytest.mark.asyncio
async def test_agent_processing(factory, llm_provider, vector_store, embeddings):
    """Test agent processing."""
    # Configure factory
    factory.with_llm(llm_provider)
    factory.with_vector_store(vector_store)
    factory.with_embeddings(embeddings)
    
    # Create agent
    agent = await factory.create(
        agent_type="mock",
        capabilities={},
        config={"name": "test"},
    )
    
    # Process input
    result = await agent.process("test input")
    assert result == "mock result"

@pytest.mark.asyncio
async def test_missing_llm_provider(factory):
    """Test error when LLM provider is missing."""
    with pytest.raises(ValueError, match="LLM provider not set"):
        await factory.create(
            agent_type="mock",
            capabilities={},
            config={"name": "test"},
        )

@pytest.mark.asyncio
async def test_invalid_agent_type(factory, llm_provider):
    """Test error with invalid agent type."""
    factory.with_llm(llm_provider)
    
    with pytest.raises(ValueError, match="Agent 'invalid' not registered"):
        await factory.create(
            agent_type="invalid",
            capabilities={},
            config={"name": "test"},
        ) 