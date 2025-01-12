"""Function module."""

from collections.abc import Callable, Coroutine
from typing import Any

from .ai_types import Message
from .providers.base import BaseProvider
from .responses import AIResponse


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
