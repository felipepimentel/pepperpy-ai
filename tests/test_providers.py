"""Test provider implementations."""

from collections.abc import AsyncGenerator
from typing import NotRequired, TypedDict, cast

from pepperpy_ai.providers.base import BaseProvider
from pepperpy_ai.providers.types import ProviderKwargs
from pepperpy_ai.responses import AIResponse, ResponseMetadata
from pepperpy_ai.types import Message, MessageRole


class TestConfig(TypedDict, total=False):
    """Test provider configuration."""

    api_key: NotRequired[str]
    model: NotRequired[str]
    temperature: NotRequired[float]
    max_tokens: NotRequired[int]
    top_p: NotRequired[float]
    frequency_penalty: NotRequired[float]
    presence_penalty: NotRequired[float]
    timeout: NotRequired[float]


class TestProvider(BaseProvider[TestConfig]):
    """Test provider implementation."""

    def __init__(self, config: TestConfig) -> None:
        """Initialize provider.

        Args:
            config: Provider configuration
        """
        super().__init__(config, api_key=config.get("api_key", "test_key"))

    async def initialize(self) -> None:
        """Initialize provider."""
        pass

    async def cleanup(self) -> None:
        """Cleanup provider."""
        pass

    async def stream(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: ProviderKwargs,
    ) -> AsyncGenerator[AIResponse, None]:
        """Stream responses from provider.

        Args:
            messages: List of messages to send
            model: Model to use for completion
            temperature: Temperature to use for completion
            max_tokens: Maximum number of tokens to generate
            **kwargs: Additional provider-specific parameters

        Returns:
            AsyncGenerator yielding AIResponse objects
        """
        yield AIResponse(
            content="Hello, how can I help you?",
            metadata=ResponseMetadata(
                model=model or "test-model",
                provider="test",
            ),
        )


async def test_provider_initialization() -> None:
    """Test provider initialization."""
    provider = TestProvider(TestConfig({"model": "test-model"}))
    await provider.initialize()
    await provider.cleanup()


async def test_provider_stream() -> None:
    """Test provider stream."""
    provider = TestProvider(TestConfig({"model": "test-model"}))
    await provider.initialize()

    messages = [Message(role=MessageRole.USER, content="Hello!")]

    async for response in provider.stream(messages):
        metadata = cast(ResponseMetadata, response.metadata)
        assert response.content == "Hello, how can I help you?"
        assert metadata.get("model") == "test-model"
        assert metadata.get("provider") == "test"

    await provider.cleanup()
