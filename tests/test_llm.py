"""Tests for LLM functionality."""

from collections.abc import AsyncIterator

import pytest

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
            cost=0.0
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
def config() -> ProviderConfig:
    """Create test config."""
    return ProviderConfig(
        type="mock",
        model_name="mock-model",
        api_key="test-key"
    )


@pytest.fixture
async def llm(config: ProviderConfig) -> AsyncIterator[MockLLM]:
    """Create test LLM."""
    llm = MockLLM(config)
    await llm.initialize()
    yield llm
    await llm.cleanup()


async def test_initialize(llm: MockLLM) -> None:
    """Test initialization."""
    assert llm.is_initialized


async def test_generate(llm: MockLLM) -> None:
    """Test text generation."""
    response = await llm.generate("Test prompt")
    assert isinstance(response, LLMResponse)
    assert response.text == "Mock response"
    assert response.tokens_used == 10
    assert response.finish_reason == "length"
    assert response.model_name == "mock-model"
    assert response.cost == 0.0


async def test_generate_stream(llm: MockLLM) -> None:
    """Test stream generation."""
    chunks = []
    async for chunk in llm.generate_stream("Test prompt"):
        chunks.append(chunk)
    assert chunks == ["Mock", " ", "response"]


async def test_get_embedding(llm: MockLLM) -> None:
    """Test embedding generation."""
    embedding = await llm.get_embedding("Test text")
    assert isinstance(embedding, list)
    assert len(embedding) == 3
    assert embedding == [0.1, 0.2, 0.3]


async def test_cleanup(llm: MockLLM) -> None:
    """Test cleanup."""
    await llm.cleanup()
    assert llm.cleaned_up 