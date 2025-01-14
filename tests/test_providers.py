"""Test provider implementations."""

from collections.abc import AsyncGenerator
from typing import NotRequired, TypedDict, cast

from pepperpy.providers.base import BaseProvider
from pepperpy.providers.types import ProviderKwargs
from pepperpy.responses import AIResponse, ResponseMetadata
from pepperpy.types import Message


class TestConfig(TypedDict, total=True):
    """Test provider configuration."""

    name: str
    version: str
    model: str
    api_key: str
    api_base: str
    organization_id: NotRequired[str | None]
    api_version: NotRequired[str | None]
    organization: NotRequired[str | None]
    temperature: NotRequired[float]
    max_tokens: NotRequired[int]
    top_p: NotRequired[float]
    frequency_penalty: NotRequired[float]
    presence_penalty: NotRequired[float]
    timeout: NotRequired[float]
    max_retries: NotRequired[int]
    enabled: NotRequired[bool]


class TestProvider(BaseProvider[TestConfig]):
    """Test provider implementation."""

    def __init__(self, config: TestConfig) -> None:
        """Initialize provider.

        Args:
            config: Provider configuration
        """
        super().__init__(config)
        self.api_key = config.get("api_key", "test_key")

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
                usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                finish_reason="stop",
            ),
        )


async def test_provider_initialization() -> None:
    """Test provider initialization."""
    provider = TestProvider(
        TestConfig(
            name="test",
            version="1.0.0",
            model="test-model",
            api_key="test_key",
            api_base="http://test",
            organization_id=None,
            api_version=None,
            organization=None,
            enabled=True,
            max_retries=3,
        )
    )
    await provider.initialize()
    await provider.cleanup()


async def test_provider_stream() -> None:
    """Test provider stream."""
    provider = TestProvider(
        TestConfig(
            name="test",
            version="1.0.0",
            model="test-model",
            api_key="test_key",
            api_base="http://test",
            organization_id=None,
            api_version=None,
            organization=None,
            enabled=True,
            max_retries=3,
        )
    )
    await provider.initialize()

    messages = [Message(role="user", content="Hello!")]

    async for response in provider.stream(messages):
        assert response["content"] == "Hello, how can I help you?"
        metadata = cast(ResponseMetadata, response["metadata"])
        assert metadata.get("model") == "test-model"
        assert metadata.get("provider") == "test"

    await provider.cleanup()
