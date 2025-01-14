"""AI types module."""

from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import Any, TypedDict

from .types import Message, Role


@dataclass
class AIResponse:
    """AI response."""

    id: str
    created: int
    model: str
    role: Role
    content: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


class AIKwargs(TypedDict):
    """AI kwargs."""

    model: str | None
    temperature: float | None
    max_tokens: int | None


class AIClient:
    """AI client."""

    async def chat(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> AIResponse:
        """Chat with the AI.

        Args:
            messages: Messages to send to the AI.
            model: Model to use.
            temperature: Temperature to use.
            max_tokens: Maximum number of tokens to generate.
            **kwargs: Additional arguments.

        Returns:
            AI response.
        """
        raise NotImplementedError

    async def stream(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> AsyncGenerator[AIResponse, None]:
        """Stream chat with the AI.

        Args:
            messages: Messages to send to the AI.
            model: Model to use.
            temperature: Temperature to use.
            max_tokens: Maximum number of tokens to generate.
            **kwargs: Additional arguments.

        Returns:
            AI response generator.
        """
        raise NotImplementedError
