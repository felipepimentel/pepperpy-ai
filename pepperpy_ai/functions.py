"""AI function utilities."""

from collections.abc import AsyncGenerator
from typing import Protocol, runtime_checkable

from .ai_types import AIResponse
from .client import AIClient


@runtime_checkable
class EmbeddingClient(Protocol):
    """Protocol for clients that support embeddings."""

    async def get_embedding(self, text: str) -> list[float]:
        """Get embedding for text."""
        ...


@runtime_checkable
class StreamingClient(Protocol):
    """Protocol for clients that support streaming."""

    async def stream(self, prompt: str) -> AsyncGenerator[AIResponse, None]:
        """Stream responses."""
        ...


async def stream_response(
    client: AIClient, prompt: str
) -> AsyncGenerator[AIResponse, None]:
    """Stream response from client.

    Args:
        client: AI client
        prompt: Prompt to stream

    Yields:
        AI response chunks

    Raises:
        TypeError: If client doesn't support streaming
    """
    if not hasattr(client, "stream"):
        raise TypeError("Client does not support streaming")

    async for response in client.stream(prompt):
        yield response


async def get_embedding(client: AIClient, text: str) -> list[float]:
    """Get embedding from client.

    Args:
        client: AI client
        text: Text to embed

    Returns:
        Embedding vector

    Raises:
        TypeError: If client doesn't support embeddings
    """
    if not isinstance(client, EmbeddingClient):
        raise TypeError("Client does not support embeddings")

    return await client.get_embedding(text)
