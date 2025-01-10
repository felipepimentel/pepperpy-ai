"""Example utilities."""

from collections.abc import AsyncGenerator

from pepperpy_ai.ai_types import AIMessage, AIResponse
from pepperpy_ai.llm.config import LLMConfig


class ExampleAIClient:
    """Example AI client implementation."""

    def __init__(self) -> None:
        """Initialize client."""
        self._config = LLMConfig(
            name="example",
            provider="example",
            api_key="dummy-key",
            model="gpt-3.5-turbo",
            temperature=0.7,
            max_tokens=150,
        )
        self._client = None
        self._initialized = False

    @property
    def config(self) -> LLMConfig:
        """Get client configuration."""
        return self._config

    @property
    def is_initialized(self) -> bool:
        """Check if client is initialized."""
        return self._initialized

    async def initialize(self) -> None:
        """Initialize client."""
        await self._setup()
        self._initialized = True

    async def cleanup(self) -> None:
        """Cleanup client resources."""
        await self._teardown()
        self._initialized = False

    async def _setup(self) -> None:
        """Setup client resources."""
        # Dummy implementation
        pass

    async def _teardown(self) -> None:
        """Teardown client resources."""
        self._client = None

    async def complete(self, prompt: str) -> AIResponse:
        """Complete prompt.

        Args:
            prompt: Prompt to complete

        Returns:
            AI response
        """
        message = AIMessage(role="assistant", content=f"Example response to: {prompt}")
        return AIResponse(content=message.content, messages=[message])

    async def stream(self, prompt: str) -> AsyncGenerator[AIResponse, None]:
        """Stream responses.

        Args:
            prompt: Prompt to stream responses for

        Yields:
            AI responses
        """
        response = await self.complete(prompt)
        yield response

    async def get_embedding(self, text: str) -> list[float]:
        """Get text embedding.

        Args:
            text: Text to get embedding for

        Returns:
            Text embedding vector

        Note:
            This is a dummy implementation that returns an empty vector.
            In a real application, you would want to implement actual embedding logic.
        """
        return []
