"""OpenRouter API integration."""

from typing import Any

from pepperpy.llms.base import BaseLLMProvider
from pepperpy.llms.types import ProviderConfig, ProviderStats


class OpenRouterProvider(BaseLLMProvider):
    """OpenRouter API provider."""

    def __init__(self, config: ProviderConfig) -> None:
        """Initialize provider.

        Args:
            config: Provider configuration
        """
        super().__init__(config)
        self.stats = ProviderStats()
        self.costs = {
            "anthropic": {
                "claude-3-opus": {"input": 0.015, "output": 0.075},
                "claude-3-sonnet": {"input": 0.003, "output": 0.015},
                "claude-3-haiku": {"input": 0.0015, "output": 0.0075},
                "claude-2": {"input": 0.008, "output": 0.024},
                "claude-instant": {"input": 0.0008, "output": 0.0024},
            },
            "openai": {
                "gpt-4": {"input": 0.03, "output": 0.06},
                "gpt-4-32k": {"input": 0.06, "output": 0.12},
                "gpt-3.5-turbo": {"input": 0.001, "output": 0.002},
            },
        }

    async def _prepare_messages(
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

        # Add route prefix if provided
        route_prefix = self.config.model_kwargs.get("route_prefix")
        if route_prefix:
            params["route"] = route_prefix

        # Add other valid parameters
        for key in ["top_p", "presence_penalty", "frequency_penalty"]:
            if key in kwargs:
                params[key] = kwargs[key]

        return params

    def _calculate_cost(
        self, prompt_tokens: int, completion_tokens: int, model: str
    ) -> float:
        """Calculate cost for token usage.

        Args:
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            model: Model identifier

        Returns:
            Cost in USD
        """
        provider = model.split("/")[0] if "/" in model else "unknown"
        model_name = model.split("/")[1] if "/" in model else model

        # Get cost rates for provider/model
        if provider in self.costs and model_name in self.costs[provider]:
            rates = self.costs[provider][model_name]
            return round(
                (prompt_tokens / 1000) * rates["input"]
                + (completion_tokens / 1000) * rates["output"]
            )

        return 0.0  # Unknown model
