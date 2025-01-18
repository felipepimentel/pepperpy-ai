"""OpenAI API integration."""

from collections.abc import AsyncIterator
from typing import Any, ClassVar

from openai._client import AsyncClient

from pepperpy.llms.base import BaseLLMProvider
from pepperpy.llms.types import ProviderConfig, ProviderStats


class OpenAIError(Exception):
    """OpenAI specific errors."""


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API provider."""

    MODEL_COSTS: ClassVar[dict[str, dict[str, float]]] = {
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-4-32k": {"input": 0.06, "output": 0.12},
        "gpt-3.5-turbo": {"input": 0.001, "output": 0.002},
    }

    def __init__(self, config: ProviderConfig) -> None:
        """Initialize provider.

        Args:
            config: Provider configuration
        """
        super().__init__(config)
        self.client: AsyncClient | None = None
        self.stats = ProviderStats()

    async def initialize(self) -> None:
        """Initialize OpenAI client.

        Raises:
            OpenAIError: If initialization fails
        """
        try:
            api_key = self.config.model_kwargs.get("api_key")
            if not api_key:
                raise OpenAIError("OpenAI API key not provided")

            self.client = AsyncClient(api_key=api_key)
            self._validate_model()

        except Exception as e:
            raise OpenAIError(f"Failed to initialize OpenAI client: {e!s}") from e

    async def generate_stream(
        self,
        prompt: str,
        stop: list[str] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Stream text using OpenAI.

        Args:
            prompt: Input prompt
            stop: Optional stop sequences
            temperature: Optional temperature override
            max_tokens: Optional max tokens override
            **kwargs: Additional parameters

        Returns:
            Async iterator of text chunks

        Raises:
            OpenAIError: If streaming fails
        """
        if not self.client:
            raise OpenAIError("OpenAI client not initialized")

        try:
            # Prepare messages and parameters
            messages = self._prepare_messages(prompt, kwargs)
            params = self._prepare_parameters(
                stop=stop,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                **kwargs,
            )

            # Stream responses
            async for chunk in await self.client.chat.completions.create(
                model=self.config.model_name, messages=messages, **params
            ):
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            raise OpenAIError(f"OpenAI streaming failed: {e!s}") from e

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self.client:
            await self.client.close()
            self.client = None

    def _validate_model(self) -> None:
        """Validate model configuration.

        Raises:
            OpenAIError: If model configuration is invalid
        """
        model = self.config.model_name.lower()

        # Check if model family is supported
        model_family = None
        for family in self.MODEL_COSTS:
            if family in model:
                model_family = family
                break

        if not model_family:
            raise OpenAIError(f"Unsupported model: {model}")

        # Validate temperature
        if not 0 <= self.config.temperature <= 2:
            raise OpenAIError("Temperature must be between 0 and 2")

        # Validate max tokens
        if self.config.max_tokens < 1:
            raise OpenAIError("max_tokens must be positive")

    def _prepare_messages(
        self, prompt: str, kwargs: dict[str, Any]
    ) -> list[dict[str, str]]:
        """Prepare messages for the API call.

        Args:
            prompt: Input prompt
            kwargs: Additional parameters

        Returns:
            List of message dictionaries
        """
        messages = []

        # Add system message if provided
        system_message = kwargs.get("system_message")
        if system_message:
            messages.append({"role": "system", "content": system_message})

        # Add chat history if provided
        chat_history = kwargs.get("chat_history", [])
        messages.extend(chat_history)

        # Add user prompt
        messages.append({"role": "user", "content": prompt})

        return messages

    def _prepare_parameters(
        self,
        stop: list[str] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Prepare parameters for the API call.

        Args:
            stop: Optional stop sequences
            temperature: Optional temperature override
            max_tokens: Optional max tokens override
            **kwargs: Additional parameters

        Returns:
            Dictionary of parameters
        """
        params = {
            "temperature": temperature or self.config.temperature,
            "max_tokens": max_tokens or self.config.max_tokens,
            "stop": stop or self.config.stop_sequences,
        }

        # Add function calling if provided
        functions = kwargs.get("functions")
        if functions:
            params["functions"] = functions
            function_call = kwargs.get("function_call")
            if function_call:
                params["function_call"] = function_call

        # Add other valid parameters
        for key in ["top_p", "presence_penalty", "frequency_penalty"]:
            if key in kwargs:
                params[key] = kwargs[key]

        return params

    def _calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate cost for token usage.

        Args:
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens

        Returns:
            Cost in USD
        """
        model = self.config.model_name.lower()

        # Get cost rates for model family
        for family, rates in self.MODEL_COSTS.items():
            if family in model:
                return round(
                    (prompt_tokens / 1000) * rates["input"]
                    + (completion_tokens / 1000) * rates["output"]
                )

        return 0.0  # Unknown model
