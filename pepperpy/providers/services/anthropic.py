"""Anthropic provider implementation for the Pepperpy framework.

This module provides integration with Anthropic's API, supporting both completion
and streaming capabilities.
"""

from collections.abc import AsyncIterator
from typing import Any, Literal, cast
from uuid import UUID, uuid4

from anthropic import AsyncAnthropic, AsyncStream
from anthropic._types import NotGiven
from anthropic.types import (
    ContentBlock,
    ContentBlockDeltaEvent,
    ContentBlockStartEvent,
    ContentBlockStopEvent,
    Message,
    MessageDeltaEvent,
    MessageParam,
    MessageStartEvent,
    MessageStopEvent,
)
from loguru import logger
from pydantic import ConfigDict, Field, SecretStr

from pepperpy.core.types import Message as PepperpyMessage
from pepperpy.core.types import MessageType, Response, ResponseStatus
from pepperpy.providers.base import (
    BaseProvider,
    GenerateKwargs,
    ProviderConfig,
    StreamKwargs,
)
from pepperpy.providers.domain import (
    ProviderAPIError,
    ProviderConfigError,
    ProviderError,
)

MessageRole = Literal["user", "assistant"]


class AnthropicConfig(ProviderConfig):
    """Anthropic provider configuration."""

    provider_type: str = Field(default="anthropic", description="The type of provider")
    api_key: SecretStr = Field(..., description="Anthropic API key")
    model: str = Field(default="claude-3-opus-20240229", description="Model to use")
    temperature: float = Field(default=0.7, description="Sampling temperature")
    max_tokens: int = Field(default=2048, description="Maximum tokens to generate")
    stop_sequences: list[str] | None = Field(
        default=None, description="Optional stop sequences"
    )
    timeout: float = Field(default=30.0, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum number of retries")

    model_config = ConfigDict(extra="forbid")


class AnthropicProvider(BaseProvider):
    """Anthropic provider implementation."""

    def __init__(self, config: ProviderConfig) -> None:
        """Initialize provider.

        Args:
            config: Provider configuration
        """
        # Convert to AnthropicConfig if needed
        anthropic_config = (
            config
            if isinstance(config, AnthropicConfig)
            else AnthropicConfig(**config.model_dump())
        )
        super().__init__(anthropic_config)
        self._client: AsyncAnthropic | None = None
        self._config = anthropic_config

    async def initialize(self) -> None:
        """Initialize provider resources.

        Raises:
            ProviderError: If initialization fails
        """
        try:
            self._client = AsyncAnthropic(
                api_key=self._config.api_key.get_secret_value(),
            )
            logger.info("Initialized Anthropic provider", model=self._config.model)
        except Exception as e:
            msg = str(e)
            raise ProviderError(msg) from e

    async def cleanup(self) -> None:
        """Clean up provider resources."""
        if self._client:
            try:
                await self._client.close()
                self._client = None
                logger.info("Cleaned up Anthropic provider")
            except Exception as e:
                logger.error("Error during cleanup", error=str(e))
                raise ProviderError(f"Cleanup failed: {e}") from e

    def _convert_messages(self, messages: list[PepperpyMessage]) -> list[MessageParam]:
        """Convert internal message format to Anthropic format.

        Args:
            messages: List of messages to convert

        Returns:
            List of Anthropic message parameters
        """
        converted: list[MessageParam] = []
        for msg in messages:
            content = str(msg.content.get("text", ""))
            if msg.type == MessageType.QUERY:
                converted.append({"role": "user", "content": content})
            elif msg.type == MessageType.RESPONSE:
                converted.append({"role": "assistant", "content": content})
            # Skip system messages as they're not supported by Anthropic
        return converted

    async def generate(
        self, messages: list[PepperpyMessage], **kwargs: GenerateKwargs
    ) -> Response:
        """Generate a response from Anthropic.

        Args:
            messages: List of messages to generate from
            **kwargs: Additional arguments to pass to the API

        Returns:
            Generated response

        Raises:
            ProviderError: If generation fails
        """
        try:
            if not self._client:
                raise ProviderError("Provider not initialized")

            model_params = kwargs.get("model_params", {})
            stop_sequences = kwargs.get("stop_sequences")
            stop: list[str] | NotGiven = (
                cast(list[str], stop_sequences)
                if isinstance(stop_sequences, list)
                else NotGiven()
            )

            response = await self._client.messages.create(
                messages=self._convert_messages(messages),
                model=str(model_params.get("model", self._config.model)),
                max_tokens=int(model_params.get("max_tokens", self._config.max_tokens)),
                temperature=float(
                    model_params.get("temperature", self._config.temperature)
                ),
                stop_sequences=stop if stop is not NotGiven() else NotGiven(),
                stream=False,
            )

            # Extract text from the first content block
            content_text = ""
            if response.content and len(response.content) > 0:
                first_block = response.content[0]
                if isinstance(first_block, ContentBlock):
                    content_text = getattr(first_block, "text", "") or ""

            return Response(
                id=uuid4(),  # Anthropic doesn't provide message IDs
                message_id=messages[-1].id,
                content={"text": content_text},
                status=ResponseStatus.SUCCESS,
                metadata={
                    "model": response.model,
                    "usage": response.usage.model_dump() if response.usage else {},
                },
            )

        except Exception as error:
            return Response(
                id=uuid4(),
                message_id=messages[-1].id if messages else uuid4(),
                content={"error": str(error)},
                status=ResponseStatus.ERROR,
                metadata={"error": str(error)},
            )

    async def stream(
        self, messages: list[PepperpyMessage], **kwargs: StreamKwargs
    ) -> AsyncIterator[Response]:
        """Stream responses from Anthropic.

        Args:
            messages: List of messages to generate from
            **kwargs: Additional arguments to pass to the API

        Returns:
            AsyncIterator[Response]: Stream of responses

        Raises:
            ProviderError: If streaming fails
        """
        try:
            if not self._client:
                raise ProviderError("Provider not initialized")

            model_params = kwargs.get("model_params", {})
            stop_sequences = kwargs.get("stop_sequences")
            stop: list[str] | NotGiven = (
                cast(list[str], stop_sequences)
                if isinstance(stop_sequences, list)
                else NotGiven()
            )

            stream = await self._client.messages.create(
                messages=self._convert_messages(messages),
                model=str(model_params.get("model", self._config.model)),
                max_tokens=int(model_params.get("max_tokens", self._config.max_tokens)),
                temperature=float(
                    model_params.get("temperature", self._config.temperature)
                ),
                stop_sequences=stop if stop is not NotGiven() else NotGiven(),
                stream=True,
            )

            async for event in stream:
                if isinstance(event, (MessageStartEvent, MessageStopEvent)):
                    continue
                if isinstance(event, MessageDeltaEvent):
                    delta = event.delta
                    if hasattr(delta, "content") and delta.content:
                        for content_block in delta.content:
                            if isinstance(content_block, ContentBlock):
                                text = getattr(content_block, "text", "")
                                if text:
                                    yield Response(
                                        id=uuid4(),
                                        message_id=messages[-1].id,
                                        content={"text": text},
                                        status=ResponseStatus.SUCCESS,
                                        metadata={
                                            "model": getattr(event, "model", "unknown"),
                                            "type": "delta",
                                        },
                                    )

        except Exception as error:
            yield Response(
                id=uuid4(),
                message_id=messages[-1].id if messages else uuid4(),
                content={"error": str(error)},
                status=ResponseStatus.ERROR,
                metadata={"error": str(error)},
            )
