"""Example utilities."""

from collections.abc import AsyncGenerator

from pepperpy_ai.ai_types import AIMessage, AIResponse
from pepperpy_ai.client import AIClient
from pepperpy_ai.config import AIConfig


class ExampleAIClient(AIClient):
    """Example AI client implementation."""

    def __init__(self) -> None:
        """Initialize client."""
        self._initialized = False
        self._config = AIConfig(
            name="example-client",
            provider="example",
            model="example-model",
            api_key="dummy-key",
        )

    @property
    def config(self) -> AIConfig:
        """Get client configuration."""
        return self._config

    @property
    def is_initialized(self) -> bool:
        """Check if client is initialized."""
        return self._initialized

    async def initialize(self) -> None:
        """Initialize client."""
        self._initialized = True

    async def cleanup(self) -> None:
        """Cleanup client resources."""
        self._initialized = False

    async def complete(self, prompt: str) -> AIResponse:
        """Complete prompt."""
        return AIResponse(
            content=f"Example response to: {prompt}",
            messages=[
                AIMessage(role="assistant", content=f"Example response to: {prompt}")
            ],
        )

    async def stream(self, prompt: str) -> AsyncGenerator[AIResponse, None]:
        """Stream responses."""
        chunks = [
            "This ",
            "is ",
            "an ",
            "example ",
            "streaming ",
            "response ",
            "to: ",
            prompt,
        ]

        for chunk in chunks:
            yield AIResponse(
                content=chunk, messages=[AIMessage(role="assistant", content=chunk)]
            )

    async def get_embedding(self, text: str) -> list[float]:
        """Get embedding for text.

        Args:
            text: Text to embed

        Returns:
            Example embedding vector
        """
        # Return a dummy embedding vector for example purposes
        return [0.0] * 10
