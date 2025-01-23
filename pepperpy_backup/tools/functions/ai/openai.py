"""OpenAI API integration."""

from typing import Any, ClassVar

from openai._client import AsyncClient
from openai.types.chat import ChatCompletionUserMessageParam


class OpenAIError(Exception):
    """OpenAI API error."""

    pass


class OpenAIProvider:
    """OpenAI API provider."""

    MODEL_COSTS: ClassVar[dict[str, dict[str, float]]] = {
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-4-32k": {"input": 0.06, "output": 0.12},
        "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
    }

    def __init__(self, config: dict[str, Any]) -> None:
        """Initialize OpenAI provider.

        Args:
            config: Provider configuration
        """
        self.config = config
        self.client: AsyncClient | None = None

    async def initialize(self) -> None:
        """Initialize OpenAI client.

        Raises:
            OpenAIError: If initialization fails
        """
        try:
            api_key = self.config.get("api_key")
            if not api_key:
                raise ValueError("OpenAI API key not provided")

            self.client = AsyncClient(api_key=api_key)

        except Exception as e:
            msg = f"Failed to initialize OpenAI client: {e!s}"
            raise OpenAIError(msg) from e

    def _prepare_messages(self, prompt: str) -> list[ChatCompletionUserMessageParam]:
        """Prepare messages for OpenAI API.

        Args:
            prompt: Text prompt

        Returns:
            List of message dictionaries
        """
        return [{"role": "user", "content": prompt}]

    def _prepare_parameters(
        self,
        stop: list[str] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """Prepare parameters for OpenAI API.

        Args:
            stop: Optional stop sequences
            temperature: Optional temperature override
            max_tokens: Optional max tokens override

        Returns:
            Dictionary of API parameters
        """
        params = {"model": self.config.get("model")}

        if stop:
            params["stop"] = stop
        if temperature is not None:
            params["temperature"] = temperature
        if max_tokens:
            params["max_tokens"] = max_tokens

        return params
