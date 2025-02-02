"""Test cases for the provider engine module."""

# Standard library imports
from collections.abc import AsyncGenerator, Generator
from typing import Any

# Third-party imports
import pytest

# Local imports
from pepperpy.providers.domain import ProviderError
from pepperpy.providers.engine import ProviderEngine
from pepperpy.providers.provider import ProviderConfig
from pepperpy.providers.services.openai import OpenAIProvider


@pytest.fixture(autouse=True)
def cleanup_providers() -> Generator[None, None, None]:
    """Clean up provider registry between tests."""
    ProviderEngine._providers.clear()
    yield
    ProviderEngine._providers.clear()


@pytest.fixture
def mock_provider() -> type[OpenAIProvider]:
    """Create a mock provider."""

    class MockOpenAIProvider(OpenAIProvider):
        """Mock OpenAI provider implementation."""

        def __init__(self, config: ProviderConfig) -> None:
            """Initialize mock provider."""
            super().__init__(config)
            self._initialized = False

        async def initialize(self) -> None:
            """Initialize the provider."""
            self._initialized = True

        async def complete(
            self,
            prompt: str,
            *,
            temperature: float = 0.7,
            max_tokens: int | None = None,
            stream: bool = False,
            **kwargs: Any,
        ) -> str | AsyncGenerator[str, None]:
            """Complete a prompt using the test engine provider.

            Args:
                prompt: The prompt to complete
                temperature: Controls randomness (0.0 to 1.0)
                max_tokens: Maximum tokens to generate
                stream: Whether to stream the response
                **kwargs: Additional provider-specific parameters

            Returns:
                Generated text or async generator of text chunks if streaming

            Raises:
                ProviderError: If the API call fails
            """
            if stream:

                async def response_generator() -> AsyncGenerator[str, None]:
                    yield "Test"
                    yield " engine"
                    yield " streaming"

                return response_generator()
            return "Test engine response"

        async def cleanup(self) -> None:
            """Clean up resources."""
            self._initialized = False

    return MockOpenAIProvider


@pytest.fixture
def engine() -> ProviderEngine:
    """Create a provider engine."""
    return ProviderEngine()


@pytest.mark.asyncio
async def test_register_provider(
    engine: ProviderEngine, mock_provider: type[OpenAIProvider]
) -> None:
    """Test registering a provider."""
    engine.register_provider("test", mock_provider)
    assert "test" in engine.list_providers()


@pytest.mark.asyncio
async def test_register_duplicate_provider(
    engine: ProviderEngine, mock_provider: type[OpenAIProvider]
) -> None:
    """Test registering a duplicate provider."""
    engine.register_provider("test", mock_provider)
    with pytest.raises(ProviderError):
        engine.register_provider("test", mock_provider)


@pytest.mark.asyncio
async def test_create_provider(
    engine: ProviderEngine, mock_provider: type[OpenAIProvider]
) -> None:
    """Test creating a provider."""
    engine.register_provider("test", mock_provider)
    provider = engine.create_provider(
        "test", api_key="test-key", model="test-model", timeout=30, max_retries=3
    )
    assert isinstance(provider, mock_provider)


@pytest.mark.asyncio
async def test_create_nonexistent_provider(engine: ProviderEngine) -> None:
    """Test creating a nonexistent provider."""
    with pytest.raises(ProviderError):
        engine.create_provider("nonexistent", api_key="test-key", model="test-model")


@pytest.mark.asyncio
async def test_initialize_provider(
    engine: ProviderEngine, mock_provider: type[OpenAIProvider]
) -> None:
    """Test initializing a provider."""
    engine.register_provider("test", mock_provider)
    provider = engine.create_provider("test", api_key="test-key", model="test-model")
    await provider.initialize()
    assert provider._initialized


@pytest.mark.asyncio
async def test_cleanup_provider(
    engine: ProviderEngine, mock_provider: type[OpenAIProvider]
) -> None:
    """Test cleaning up a provider."""
    engine.register_provider("test", mock_provider)
    provider = engine.create_provider("test", api_key="test-key", model="test-model")
    await provider.initialize()
    await provider.cleanup()
    assert not provider._initialized


@pytest.mark.asyncio
async def test_provider_lifecycle(
    engine: ProviderEngine, mock_provider: type[OpenAIProvider]
) -> None:
    """Test provider lifecycle."""
    engine.register_provider("test", mock_provider)
    provider = engine.create_provider("test", api_key="test-key", model="test-model")
    await provider.initialize()
    response = await provider.complete("test prompt")
    assert response == "Test engine response"
    await provider.cleanup()
    assert not provider._initialized


@pytest.mark.asyncio
async def test_multiple_providers(engine: ProviderEngine) -> None:
    """Test managing multiple providers."""

    class Provider1(OpenAIProvider):
        """First test provider."""

        async def initialize(self) -> None:
            """Initialize the provider."""
            pass

        async def complete(
            self,
            prompt: str,
            *,
            temperature: float = 0.7,
            max_tokens: int | None = None,
            stream: bool = False,
            **kwargs: Any,
        ) -> str | AsyncGenerator[str, None]:
            """Complete a prompt using the test provider.

            Args:
                prompt: The prompt to complete
                temperature: Controls randomness (0.0 to 1.0)
                max_tokens: Maximum tokens to generate
                stream: Whether to stream the response
                **kwargs: Additional provider-specific parameters

            Returns:
                Generated text or async generator of text chunks if streaming

            Raises:
                ProviderError: If the API call fails
            """
            if stream:

                async def response_generator() -> AsyncGenerator[str, None]:
                    yield "Test"
                    yield " provider1"
                    yield " streaming"

                return response_generator()
            return "provider1 response"

        async def cleanup(self) -> None:
            """Clean up resources."""
            pass

    class Provider2(OpenAIProvider):
        """Second test provider."""

        async def initialize(self) -> None:
            """Initialize the provider."""
            pass

        async def complete(
            self,
            prompt: str,
            *,
            temperature: float = 0.7,
            max_tokens: int | None = None,
            stream: bool = False,
            **kwargs: Any,
        ) -> str | AsyncGenerator[str, None]:
            """Complete a prompt using the test provider.

            Args:
                prompt: The prompt to complete
                temperature: Controls randomness (0.0 to 1.0)
                max_tokens: Maximum tokens to generate
                stream: Whether to stream the response
                **kwargs: Additional provider-specific parameters

            Returns:
                Generated text or async generator of text chunks if streaming

            Raises:
                ProviderError: If the API call fails
            """
            if stream:

                async def response_generator() -> AsyncGenerator[str, None]:
                    yield "Test"
                    yield " provider2"
                    yield " streaming"

                return response_generator()
            return "provider2 response"

        async def cleanup(self) -> None:
            """Clean up resources."""
            pass

    engine.register_provider("provider1", Provider1)
    engine.register_provider("provider2", Provider2)

    provider1 = engine.create_provider(
        "provider1", api_key="test-key-1", model="test-model"
    )
    provider2 = engine.create_provider(
        "provider2", api_key="test-key-2", model="test-model"
    )

    await provider1.initialize()
    await provider2.initialize()

    response1 = await provider1.complete("test prompt")
    response2 = await provider2.complete("test prompt")

    assert response1 == "provider1 response"
    assert response2 == "provider2 response"

    await provider1.cleanup()
    await provider2.cleanup()
