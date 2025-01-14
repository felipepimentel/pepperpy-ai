"""Chat conversation module."""

from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from ..config.chat import ChatConfig
from ..exceptions import ConfigurationError
from ..responses import AIResponse
from ..types import MessageRole


@dataclass
class ChatMessage:
    """Chat message type."""

    role: MessageRole
    content: str


@dataclass
class ChatHistory:
    """Chat history type."""

    messages: list[ChatMessage]


@runtime_checkable
class ChatClient(Protocol):
    """Chat client protocol."""

    async def complete(self, prompt: str) -> AIResponse:
        """Complete a prompt.

        Args:
            prompt: The prompt to complete.

        Returns:
            The AI response.
        """
        ...

    def stream(self, prompt: str) -> AsyncGenerator[AIResponse, None]:
        """Stream responses for a prompt.

        Args:
            prompt: The prompt to stream.

        Returns:
            An async generator yielding AI response chunks.
        """
        ...


class ChatConversation:
    """Chat conversation class."""

    def __init__(self, config: ChatConfig) -> None:
        """Initialize chat conversation.

        Args:
            config: Chat configuration.
        """
        self._config = config
        self._client: ChatClient | None = None
        self._history = ChatHistory(messages=[])

    @property
    def history(self) -> ChatHistory:
        """Get conversation history.

        Returns:
            The conversation history.
        """
        return self._history

    async def initialize(self, client: ChatClient) -> None:
        """Initialize chat conversation.

        Args:
            client: Chat client to use.
        """
        self._client = client

    async def complete(self, message: str) -> AIResponse:
        """Complete a message.

        Args:
            message: The message to complete.

        Returns:
            The AI response.

        Raises:
            ConfigurationError: If no AI client is configured.
        """
        if not self._client:
            raise ConfigurationError("No AI client configured", field="client")

        # Add user message to history
        self._history.messages.append(
            ChatMessage(role=MessageRole.USER, content=message)
        )

        # Get response from provider
        response = await self._client.complete(message)

        # Add assistant message to history
        self._history.messages.append(
            ChatMessage(role=MessageRole.ASSISTANT, content=response["content"])
        )

        return response

    async def stream(self, message: str) -> AsyncGenerator[AIResponse, None]:
        """Stream responses for a message.

        Args:
            message: The message to stream.

        Returns:
            An async generator yielding AI response chunks.

        Raises:
            ConfigurationError: If no AI client is configured.
        """
        if not self._client:
            raise ConfigurationError("No AI client configured", field="client")

        # Add user message to history
        self._history.messages.append(
            ChatMessage(role=MessageRole.USER, content=message)
        )

        # Get stream from provider
        async for response in self._client.stream(message):
            # Add assistant message to history
            self._history.messages.append(
                ChatMessage(role=MessageRole.ASSISTANT, content=response["content"])
            )
            yield response

    async def _stream_response(self, prompt: str) -> None:
        """Stream a response from the AI provider.

        Args:
            prompt: The prompt to send.

        Raises:
            ConfigurationError: If no AI client is configured.
        """
        if not self._client:
            raise ConfigurationError("No AI client configured", field="client")

        # Get stream from provider
        async for response in self._client.stream(prompt):
            # Add assistant message to history
            self._history.messages.append(
                ChatMessage(role=MessageRole.ASSISTANT, content=response["content"])
            )
