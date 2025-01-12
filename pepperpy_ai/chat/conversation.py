"""Chat conversation module."""

from collections.abc import AsyncGenerator
from typing import Protocol, runtime_checkable

from ..exceptions import ConfigurationError
from ..responses import AIResponse
from .config import ChatConfig
from .types import ChatHistory, ChatMessage, ChatRole


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

    async def stream(self, prompt: str) -> AsyncGenerator[AIResponse, None]:
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
            config: The chat configuration.
        """
        self.config = config
        self._client: ChatClient | None = None
        self._history = ChatHistory()

    @property
    def history(self) -> ChatHistory:
        """Get conversation history.

        Returns:
            The chat history.
        """
        return self._history

    async def initialize(self, client: ChatClient) -> None:
        """Initialize conversation with client.

        Args:
            client: The chat client to use.
        """
        self._client = client

    async def complete(self, message: str) -> AIResponse:
        """Complete a message.

        Args:
            message: The message to send.

        Returns:
            The AI response.

        Raises:
            ConfigurationError: If no client is configured.
        """
        if not self._client:
            raise ConfigurationError("No AI client configured", field="client")

        # Add user message to history
        self._history.messages.append(
            ChatMessage(role=ChatRole.USER, content=message)
        )

        # Get response from provider
        response = await self._client.complete(message)

        # Add assistant message to history
        self._history.messages.append(
            ChatMessage(role=ChatRole.ASSISTANT, content=response.content)
        )

        return response

    async def stream(self, message: str) -> AsyncGenerator[AIResponse, None]:
        """Stream a response from the AI provider.

        Args:
            message: The message to send.

        Returns:
            An async generator yielding AI response chunks.

        Raises:
            ConfigurationError: If no client is configured.
        """
        if not self._client:
            raise ConfigurationError("No AI client configured", field="client")

        # Add user message to history
        self._history.messages.append(
            ChatMessage(role=ChatRole.USER, content=message)
        )

        # Stream response from provider
        stream = await self._client.stream(message)
        async for response in stream:
            # Add assistant message to history
            self._history.messages.append(
                ChatMessage(role=ChatRole.ASSISTANT, content=response.content)
            )
            yield response

    async def _stream_response(self, prompt: str) -> None:
        """Stream a response from the AI provider.

        Args:
            prompt: The prompt to send.
        """
        if not self._client:
            raise ConfigurationError("No AI client configured", field="client")

        stream = await self._client.stream(prompt)
        async for response in stream:
            # Add assistant message to history
            self._history.messages.append(
                ChatMessage(role=ChatRole.ASSISTANT, content=response.content)
            )
