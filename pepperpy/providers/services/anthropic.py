"""Anthropic provider implementation for the Pepperpy framework.

This module provides integration with Anthropic's API, supporting both completion
and streaming capabilities.
"""

from collections.abc import AsyncIterator
from typing import Any, cast
from uuid import UUID, uuid4

from anthropic import AsyncAnthropic
from anthropic.types import MessageParam
from pydantic import SecretStr

from pepperpy.core.types import Message, Response, ResponseStatus
from pepperpy.providers.base import BaseProvider, ProviderConfig


class AnthropicConfig(ProviderConfig):
    """Anthropic provider configuration."""

    api_key: SecretStr
    model: str = "claude-3-opus-20240229"
    temperature: float = 0.7
    max_tokens: int = 2048


class AnthropicProvider(BaseProvider):
    """Provider implementation for Anthropic's API."""

    def __init__(self, config: AnthropicConfig):
        """Initialize Anthropic provider with configuration."""
        super().__init__(config)
        self.config = config
        self.client = AsyncAnthropic(api_key=config.api_key.get_secret_value())

    def _convert_messages(self, messages: list[Message]) -> list[MessageParam]:
        """Convert internal message format to Anthropic format."""
        converted: list[MessageParam] = []
        for msg in messages:
            role = "user" if msg.sender == "user" else "assistant"
            converted.append(
                cast(MessageParam, {"role": role, "content": str(msg.content)})
            )
        return converted

    def _extract_text_content(self, content: list[Any]) -> str:
        """Extract text content from Anthropic response."""
        if not content:
            return ""
        text_parts = []
        for block in content:
            # Handle both dictionary and object formats
            if isinstance(block, dict):
                text = block.get("text", "")
                if text:
                    text_parts.append(text)
            else:
                # Try to get text content from object attributes
                try:
                    text = getattr(block, "text", None)
                    if text:
                        text_parts.append(str(text))
                except (AttributeError, TypeError):
                    continue
        return " ".join(text_parts)

    async def generate(self, messages: list[Message], **kwargs: Any) -> Response:
        """Generate a response from Anthropic."""
        try:
            response = await self.client.messages.create(
                messages=self._convert_messages(messages),
                model=kwargs.get("model", self.config.model),
                temperature=kwargs.get("temperature", self.config.temperature),
                max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
            )

            content = self._extract_text_content(response.content)
            return Response(
                id=UUID(response.id),
                message_id=messages[-1].id,
                content={"text": content},
                status=ResponseStatus.SUCCESS,
                metadata={
                    "model": response.model,
                    "usage": response.usage.dict() if response.usage else {},
                },
            )

        except Exception as e:
            return Response(
                id=uuid4(),
                message_id=messages[-1].id if messages else uuid4(),
                content={"error": str(e)},
                status=ResponseStatus.ERROR,
                metadata={"error": str(e)},
            )

    def stream(self, messages: list[Message], **kwargs: Any) -> AsyncIterator[Response]:
        """Stream responses from Anthropic.

        Args:
            messages: List of messages to generate from
            **kwargs: Additional arguments to pass to the API

        Returns:
            AsyncIterator[Response]: Stream of responses

        Raises:
            Exception: If streaming fails
        """

        async def stream_impl() -> AsyncIterator[Response]:
            try:
                stream = await self.client.messages.create(
                    messages=self._convert_messages(messages),
                    model=kwargs.get("model", self.config.model),
                    temperature=kwargs.get("temperature", self.config.temperature),
                    max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
                    stream=True,
                )

                message_id = None
                model = None

                async for event in stream:
                    # Check if event is a MessageStreamEvent
                    if not hasattr(event, "type"):
                        continue

                    if event.type == "message_start":
                        message_id = event.message.id
                        model = event.message.model
                    elif event.type == "content_block_delta":
                        # Extract text content from the delta event
                        # Use Any type to handle different delta types
                        delta: Any = event.delta
                        text = None

                        # Try to get text content from the delta
                        if hasattr(delta, "text"):
                            text = str(delta.text)

                        if text:
                            yield Response(
                                id=uuid4(),  # Each chunk gets a unique ID
                                message_id=messages[-1].id,
                                content={"text": text},
                                status=ResponseStatus.SUCCESS,
                                metadata={
                                    "model": model,
                                    "message_id": message_id,
                                    "index": 0,
                                },
                            )

            except Exception as e:
                yield Response(
                    id=uuid4(),
                    message_id=messages[-1].id if messages else uuid4(),
                    content={"error": str(e)},
                    status=ResponseStatus.ERROR,
                    metadata={"error": str(e)},
                )

        return stream_impl()
