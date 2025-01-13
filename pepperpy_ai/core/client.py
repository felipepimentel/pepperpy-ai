"""AI client module."""

from collections.abc import AsyncGenerator

from ..types import Message
from .responses import AIResponse


class AIClient:
    """AI client interface."""

    async def stream(
        self,
        messages: list[Message],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AsyncGenerator[AIResponse, None]:
        """Stream responses from the AI model.

        Args:
            messages: List of messages to send to the model.
            model: Model to use for the request.
            temperature: Temperature to use for the request.
            max_tokens: Maximum number of tokens to generate.

        Returns:
            AsyncGenerator yielding AIResponse objects.
        """
        raise NotImplementedError
