"""
Unit tests for base provider functionality.
"""

import pytest

from pepperpy.core.utils.errors import ProviderError
from pepperpy.providers.base.provider import (
    BaseProvider,
    LLMProvider,
    VectorStoreProvider,
    EmbeddingProvider,
    MemoryProvider,
)


class TestBaseProvider(BaseProvider):
    """Test provider implementation."""
    
    async def initialize(self) -> None:
        """Initialize the provider."""
        await super().initialize()
    
    async def shutdown(self) -> None:
        """Shutdown the provider."""
        await super().shutdown()


@pytest.mark.asyncio
async def test_provider_lifecycle(test_config):
    """Test provider initialization and shutdown."""
    provider = TestBaseProvider(config=test_config)
    
    assert not provider.is_initialized
    await provider.initialize()
    assert provider.is_initialized
    
    await provider.shutdown()
    assert not provider.is_initialized


@pytest.mark.asyncio
async def test_provider_config(test_config):
    """Test provider configuration."""
    provider = TestBaseProvider(config=test_config)
    assert provider.config == test_config
    
    provider_no_config = TestBaseProvider()
    assert provider_no_config.config == {}


@pytest.mark.asyncio
async def test_ensure_initialized():
    """Test initialization check."""
    provider = TestBaseProvider()
    
    with pytest.raises(ProviderError) as exc_info:
        provider._ensure_initialized()
    assert "not initialized" in str(exc_info.value)
    
    await provider.initialize()
    provider._ensure_initialized()  # Should not raise


class TestLLMProvider(LLMProvider):
    """Test LLM provider implementation."""
    
    async def initialize(self) -> None:
        """Initialize the provider."""
        await super().initialize()
    
    async def shutdown(self) -> None:
        """Shutdown the provider."""
        await super().shutdown()
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate text."""
        self._ensure_initialized()
        return prompt.upper()


@pytest.mark.asyncio
async def test_llm_provider():
    """Test LLM provider functionality."""
    provider = TestLLMProvider()
    await provider.initialize()
    
    result = await provider.generate("hello")
    assert result == "HELLO"
    
    await provider.shutdown()


class TestVectorStoreProvider(VectorStoreProvider):
    """Test vector store provider implementation."""
    
    async def initialize(self) -> None:
        """Initialize the provider."""
        await super().initialize()
    
    async def shutdown(self) -> None:
        """Shutdown the provider."""
        await super().shutdown()
    
    async def store(self, vectors, metadata=None):
        """Store vectors."""
        self._ensure_initialized()
        return "test_id"
    
    async def search(self, query_vector, k=5):
        """Search vectors."""
        self._ensure_initialized()
        return [{"id": "test_id", "score": 0.9}]


@pytest.mark.asyncio
async def test_vector_store_provider():
    """Test vector store provider functionality."""
    provider = TestVectorStoreProvider()
    await provider.initialize()
    
    vector_id = await provider.store([0.1, 0.2, 0.3])
    assert vector_id == "test_id"
    
    results = await provider.search([0.1, 0.2, 0.3])
    assert len(results) == 1
    assert results[0]["id"] == "test_id"
    
    await provider.shutdown()


class TestEmbeddingProvider(EmbeddingProvider):
    """Test embedding provider implementation."""
    
    async def initialize(self) -> None:
        """Initialize the provider."""
        await super().initialize()
    
    async def shutdown(self) -> None:
        """Shutdown the provider."""
        await super().shutdown()
    
    async def embed(self, text: str) -> list[float]:
        """Generate embeddings."""
        self._ensure_initialized()
        return [0.1, 0.2, 0.3]


@pytest.mark.asyncio
async def test_embedding_provider():
    """Test embedding provider functionality."""
    provider = TestEmbeddingProvider()
    await provider.initialize()
    
    embeddings = await provider.embed("test text")
    assert isinstance(embeddings, list)
    assert all(isinstance(x, float) for x in embeddings)
    
    await provider.shutdown()


class TestMemoryProvider(MemoryProvider):
    """Test memory provider implementation."""
    
    def __init__(self, *args, **kwargs):
        """Initialize the provider."""
        super().__init__(*args, **kwargs)
        self._storage = {}
    
    async def initialize(self) -> None:
        """Initialize the provider."""
        await super().initialize()
    
    async def shutdown(self) -> None:
        """Shutdown the provider."""
        await super().shutdown()
    
    async def store(self, key: str, value: str) -> None:
        """Store a value."""
        self._ensure_initialized()
        self._storage[key] = value
    
    async def retrieve(self, key: str):
        """Retrieve a value."""
        self._ensure_initialized()
        return self._storage.get(key)
    
    async def clear(self) -> None:
        """Clear storage."""
        self._ensure_initialized()
        self._storage.clear()


@pytest.mark.asyncio
async def test_memory_provider():
    """Test memory provider functionality."""
    provider = TestMemoryProvider()
    await provider.initialize()
    
    await provider.store("test_key", "test_value")
    value = await provider.retrieve("test_key")
    assert value == "test_value"
    
    await provider.clear()
    value = await provider.retrieve("test_key")
    assert value is None
    
    await provider.shutdown() 