"""Base class for LLM providers.

This module defines the base class for LLM (Large Language Model) providers.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from pepperpy.llm.providers.base.types import (
    ChatMessage,
    CompletionOptions,
    LLMResponse,
    ModelParameters,
)


class LLMProviderBase(ABC):
    """Base class for LLM providers."""

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def get_models(self) -> List[str]:
        """Get list of available models.

        Returns:
            List[str]: List of model names
        """
        pass

    @abstractmethod
    def get_model_parameters(self, model_name: str) -> ModelParameters:
        """Get parameters for a specific model.

        Args:
            model_name: Name of the model

        Returns:
            ModelParameters: Model parameters

        Raises:
            ValueError: If model is not found
        """
        pass
