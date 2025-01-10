"""OpenRouter provider implementation."""

from typing import Any

from .base import AIProvider


class OpenRouterProvider(AIProvider):
    """OpenRouter AI provider implementation."""

    async def generate_response(
        self,
        *,
        prompt: str,
        system_message: str | None = None,
        conversation_history: list[dict[str, Any]] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Generate a response using OpenRouter.

        Args:
            prompt: The prompt to send
            system_message: Optional system message
            conversation_history: Optional conversation history
            metadata: Optional metadata

        Returns:
            The generated response
        """
        # Implementation here
        return "OpenRouter response"
