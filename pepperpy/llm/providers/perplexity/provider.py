"""Perplexity LLM provider implementation."""

from typing import List, Optional

from pepperpy.llm.providers.base.base import BaseLLMProvider
from pepperpy.llm.providers.base.types import (
    ChatMessage,
    CompletionOptions,
    LLMResponse,
    ModelParameters,
)


class PerplexityProvider(BaseLLMProvider):
    """Provider implementation for Perplexity LLMs."""

    def __init__(
        self,
        api_key: str,
        **kwargs,
    ):
        """Initialize Perplexity provider.

        Args:
            api_key: Perplexity API key
            **kwargs: Additional parameters to pass to Perplexity
        """
        self.api_key = api_key
        self.kwargs = kwargs
        self._client = None

    @property
    def client(self):
        """Get Perplexity client."""
        if self._client is None:
            try:
                from openai import OpenAI

                self._client = OpenAI(
                    api_key=self.api_key,
                    base_url="https://api.perplexity.ai",
                )
            except ImportError:
                raise ImportError(
                    "openai package is required for PerplexityProvider. "
                    "Install it with: pip install openai"
                )
        return self._client

    def generate(
        self,
        prompt: str,
        options: Optional[CompletionOptions] = None,
        **kwargs,
    ) -> LLMResponse:
        """Generate text completion.

        Args:
            prompt: Text prompt for completion
            options: Completion options
            **kwargs: Additional parameters for the provider

        Returns:
            LLMResponse: Generated completion response
        """
        options = options or CompletionOptions(model="sonar-medium-online")

        # Placeholder implementation
        return LLMResponse(
            text="This is a placeholder response from Perplexity provider.",
            model=options.model,
        )

    def chat(
        self,
        messages: List[ChatMessage],
        options: Optional[CompletionOptions] = None,
        **kwargs,
    ) -> LLMResponse:
        """Generate chat completion.

        Args:
            messages: List of chat messages
            options: Completion options
            **kwargs: Additional parameters for the provider

        Returns:
            LLMResponse: Generated chat response
        """
        options = options or CompletionOptions(model="sonar-medium-online")

        # Placeholder implementation
        return LLMResponse(
            text="This is a placeholder response from Perplexity chat provider.",
            model=options.model,
        )

    def get_models(self) -> List[str]:
        """Get list of available models.

        Returns:
            List[str]: List of model names
        """
        return [
            "sonar-small-online",
            "sonar-medium-online",
            "sonar-large-online",
            "mixtral-8x7b-instruct",
            "llama-3-70b-instruct",
        ]

    def get_model_parameters(self, model_name: str) -> ModelParameters:
        """Get parameters for a specific model.

        Args:
            model_name: Name of the model

        Returns:
            ModelParameters: Model parameters

        Raises:
            ValueError: If model is not found
        """
        models = {
            "sonar-small-online": ModelParameters(
                model="sonar-small-online",
                context_window=12000,
                max_output_tokens=4096,
                supports_functions=False,
                supports_vision=False,
            ),
            "sonar-medium-online": ModelParameters(
                model="sonar-medium-online",
                context_window=12000,
                max_output_tokens=4096,
                supports_functions=False,
                supports_vision=False,
            ),
            "sonar-large-online": ModelParameters(
                model="sonar-large-online",
                context_window=12000,
                max_output_tokens=4096,
                supports_functions=False,
                supports_vision=False,
            ),
            "mixtral-8x7b-instruct": ModelParameters(
                model="mixtral-8x7b-instruct",
                context_window=8192,
                max_output_tokens=4096,
                supports_functions=False,
                supports_vision=False,
            ),
            "llama-3-70b-instruct": ModelParameters(
                model="llama-3-70b-instruct",
                context_window=8192,
                max_output_tokens=4096,
                supports_functions=False,
                supports_vision=False,
            ),
        }

        if model_name not in models:
            raise ValueError(f"Model '{model_name}' not found")

        return models[model_name]
