"""StackSpot provider implementation."""

from collections.abc import AsyncGenerator
from typing import Any

from ..ai_types import AIMessage, AIResponse
from ..llm.base import LLMClient
from ..llm.config import LLMConfig


class StackSpotProvider(LLMClient):
    """StackSpot provider implementation."""

    def __init__(self, config: LLMConfig) -> None:
        """Initialize provider."""
        super().__init__(config)
        self._client: Any = None
        self._base_url = "https://api.stackspot.com/v1"

    async def _setup(self) -> None:
        """Setup provider resources."""
        # Implementação específica do StackSpot
        pass

    async def _teardown(self) -> None:
        """Teardown provider resources."""
        self._client = None

    async def complete(self, prompt: str) -> AIResponse:
        """Complete prompt.

        Args:
            prompt: Prompt to complete

        Returns:
            AI response

        Raises:
            RuntimeError: If provider not initialized
        """
        if not self.is_initialized or not self._client:
            raise RuntimeError("Provider not initialized")

        try:
            response = await self._client.chat.completions.create(
                model=self.config.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                **self.config.settings,
            )

            return AIResponse(
                content=response.choices[0].message.content,
                messages=[
                    AIMessage(
                        role="assistant", content=response.choices[0].message.content
                    )
                ],
            )
        except Exception as e:
            raise RuntimeError("Completion failed") from e

    async def stream(self, prompt: str) -> AsyncGenerator[AIResponse, None]:
        """Stream responses.

        Args:
            prompt: Prompt to stream

        Returns:
            AsyncGenerator that yields AI response chunks

        Raises:
            RuntimeError: If provider not initialized
        """
        return self._stream(prompt)

    async def _stream(self, prompt: str) -> AsyncGenerator[AIResponse, None]:
        if not self.is_initialized or not self._client:
            raise RuntimeError("Provider not initialized")

        try:
            stream = await self._client.chat.completions.create(
                model=self.config.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                stream=True,
                **self.config.settings,
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield AIResponse(
                        content=chunk.choices[0].delta.content,
                        messages=[
                            AIMessage(
                                role="assistant", content=chunk.choices[0].delta.content
                            )
                        ],
                    )
        except Exception as e:
            raise RuntimeError("Streaming failed") from e
