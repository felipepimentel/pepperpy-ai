"""Chat conversation implementation."""

from collections.abc import AsyncGenerator
from typing import Protocol, runtime_checkable

from ..ai_types import AIResponse
from ..client import AIClient
from .config import ChatConfig
from .types import ChatHistory, ChatMessage


@runtime_checkable
class StreamingClient(Protocol):
    """Protocol for clients that support streaming."""

    async def stream(self, prompt: str) -> AsyncGenerator[AIResponse, None]:
        """Stream responses."""
        ...


class ChatConversation:
    """Chat conversation implementation."""

    def __init__(self, config: ChatConfig, client: AIClient) -> None:
        """Initialize conversation."""
        self.config = config
        self._client = client
        self._history = ChatHistory()
        self._initialized = False

    @property
    def history(self) -> list[ChatMessage]:
        """Get conversation history."""
        return self._history.messages

    async def initialize(self) -> None:
        """Initialize conversation."""
        if not self._initialized:
            await self._client.initialize()
            if self.config.system_message:
                self._history.messages.append(
                    ChatMessage(
                        role=self.config.system_role, content=self.config.system_message
                    )
                )
            self._initialized = True

    async def cleanup(self) -> None:
        """Cleanup conversation."""
        if self._initialized:
            await self._client.cleanup()
            self._initialized = False

    async def send(self, message: str) -> AIResponse:
        """Send message to conversation.

        Args:
            message: Message to send

        Returns:
            AI response

        Raises:
            RuntimeError: If conversation is not initialized
        """
        if not self._initialized:
            raise RuntimeError("Conversation not initialized")

        # Add user message
        self._history.messages.append(
            ChatMessage(role=self.config.user_role, content=message)
        )

        # Get response from client and ensure correct type
        response = await self._client.complete(message)

        # Add assistant message
        self._history.messages.append(
            ChatMessage(role=self.config.assistant_role, content=response.content)
        )

        return response

    async def stream(self, message: str) -> AsyncGenerator[AIResponse, None]:
        """Stream conversation response.

        Args:
            message: Message to send

        Yields:
            AI response chunks

        Raises:
            RuntimeError: If conversation is not initialized
            TypeError: If client doesn't support streaming
        """
        if not self._initialized:
            raise RuntimeError("Conversation not initialized")

        if not hasattr(self._client, "stream"):
            raise TypeError("Client does not support streaming")

        # Add user message
        self._history.messages.append(
            ChatMessage(role=self.config.user_role, content=message)
        )

        # Stream response
        content = ""
        # Get response stream from client
        async for chunk in self._client.stream(message):
            response = chunk
            content += response.content
            yield response

        # Add complete assistant message
        self._history.messages.append(
            ChatMessage(role=self.config.assistant_role, content=content)
        )
