"""Function module."""

from typing import Any, AsyncGenerator, Callable, Coroutine

from .ai_types import Message
from .responses import AIResponse
from .providers.base import BaseProvider


async def stream_with_callback(
    provider: BaseProvider,
    messages: list[Message],
    callback: Callable[[AIResponse], Coroutine[Any, Any, None]],
) -> None:
    """Stream responses with callback.

    Args:
        provider: The provider to use
        messages: List of messages to send to the provider
        callback: The callback to call with each response
    """
    async for response in provider.stream(messages):
        await callback(response)
