"""Test utilities."""

from collections.abc import AsyncGenerator
from typing import Any, cast

from pepperpy_ai.ai_types import Message
from pepperpy_ai.exceptions import ProviderError
from pepperpy_ai.providers.base import BaseProvider
from pepperpy_ai.providers.config import ProviderConfig, ProviderSettings
from pepperpy_ai.responses import AIResponse, ResponseMetadata


class TestProvider(BaseProvider):
    """Test provider for testing."""

    def __init__(self, config: ProviderConfig, api_key: str) -> None:
        """Initialize test provider.

        Args:
            config: Provider configuration.
            api_key: API key.
        """
        super().__init__(config=config, api_key=api_key)
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize provider."""
        self._initialized = True

    async def cleanup(self) -> None:
        """Clean up provider."""
        self._initialized = False

    async def stream(
        self,
        messages: list[Message],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> AsyncGenerator[AIResponse, None]:
        """Stream responses from provider.

        Args:
            messages: Messages to send.
            model: Model to use.
            temperature: Temperature to use.
            max_tokens: Maximum tokens to generate.
            kwargs: Additional arguments.

        Yields:
            AIResponse: Response from provider.

        Raises:
            ProviderError: If provider is not initialized.
        """
        if not self._initialized:
            raise ProviderError(
                "Provider not initialized", provider="test", operation="stream"
            )

        # Simulate streaming response
        metadata: ResponseMetadata = {
            "model": model or "test-model",
            "provider": "test",
            "usage": {"total_tokens": 1},
            "finish_reason": "stop",
        }
        yield AIResponse(content="test", metadata=metadata)


def create_test_config(
    name: str = "test",
    version: str = "1.0.0",
    model: str | None = None,
    api_key: str | None = None,
    api_base: str | None = None,
    **kwargs: Any,
) -> ProviderConfig:
    """Create test provider configuration.

    Args:
        name: Provider name.
        version: Provider version.
        model: Model name.
        api_key: API key.
        api_base: API base URL.
        kwargs: Additional settings.

    Returns:
        ProviderConfig: Provider configuration.
    """
    settings = cast(
        ProviderSettings,
        {"model": model, "api_key": api_key, "api_base": api_base, **kwargs},
    )
    return ProviderConfig(
        name=name,
        version=version,
        settings=settings,
    )
