"""OpenAI LLM provider implementation."""

from typing import List, Optional

from pepperpy.llm.providers.base.base import BaseLLMProvider
from pepperpy.llm.providers.base.types import (
    ChatMessage,
    CompletionOptions,
    LLMResponse,
    ModelParameters,
)


class OpenAIProvider(BaseLLMProvider):
    """Provider implementation for OpenAI LLMs."""

    def __init__(
        self,
        api_key: str,
        organization: Optional[str] = None,
        **kwargs,
    ):
        """Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key
            organization: OpenAI organization ID
            **kwargs: Additional parameters to pass to OpenAI
        """
        self.api_key = api_key
        self.organization = organization
        self.kwargs = kwargs
        self._client = None

    @property
    def client(self):
        """Get OpenAI client."""
        if self._client is None:
            try:
                from openai import OpenAI

                self._client = OpenAI(
                    api_key=self.api_key,
                    organization=self.organization,
                )
            except ImportError:
                raise ImportError(
                    "openai package is required for OpenAIProvider. "
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
        options = options or CompletionOptions(model="gpt-3.5-turbo-instruct")

        # Placeholder implementation
        return LLMResponse(
            text="This is a placeholder response from OpenAI provider.",
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
        options = options or CompletionOptions(model="gpt-3.5-turbo")

        # Placeholder implementation
        return LLMResponse(
            text="This is a placeholder response from OpenAI chat provider.",
            model=options.model,
        )

    def get_models(self) -> List[str]:
        """Get list of available models.

        Returns:
            List[str]: List of model names
        """
        return [
            "gpt-4o",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-instruct",
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
            "gpt-4o": ModelParameters(
                model="gpt-4o",
                context_window=128000,
                max_output_tokens=4096,
                supports_functions=True,
                supports_vision=True,
            ),
            "gpt-4-turbo": ModelParameters(
                model="gpt-4-turbo",
                context_window=128000,
                max_output_tokens=4096,
                supports_functions=True,
                supports_vision=True,
            ),
            "gpt-4": ModelParameters(
                model="gpt-4",
                context_window=8192,
                max_output_tokens=4096,
                supports_functions=True,
                supports_vision=False,
            ),
            "gpt-3.5-turbo": ModelParameters(
                model="gpt-3.5-turbo",
                context_window=16385,
                max_output_tokens=4096,
                supports_functions=True,
                supports_vision=False,
            ),
            "gpt-3.5-turbo-instruct": ModelParameters(
                model="gpt-3.5-turbo-instruct",
                context_window=4096,
                max_output_tokens=4096,
                supports_functions=False,
                supports_vision=False,
            ),
        }

        if model_name not in models:
            raise ValueError(f"Model '{model_name}' not found")

        return models[model_name]
