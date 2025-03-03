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
    """Base class for LLM providers.

    This class provides a compatibility layer between the new provider interface
    and the existing LLM provider interface in pepperpy/llm/base.py.
    """

    @abstractmethod
    def generate(
        self,
        prompt: str,
        options: Optional[CompletionOptions] = None,
        **kwargs,
    ) -> LLMResponse:
        """Generate text from a prompt.

        Args:
            prompt: The prompt to generate text from
            options: Optional completion options
            **kwargs: Additional provider-specific parameters

        Returns:
            LLMResponse: The generated text and metadata

        """

    @abstractmethod
    def chat(
        self,
        messages: List[ChatMessage],
        options: Optional[CompletionOptions] = None,
        **kwargs,
    ) -> LLMResponse:
        """Generate a response from a chat conversation.

        Args:
            messages: List of chat messages
            options: Optional completion options
            **kwargs: Additional provider-specific parameters

        Returns:
            LLMResponse: The generated response and metadata

        """

    @abstractmethod
    def get_models(self) -> List[str]:
        """Get a list of available models.

        Returns:
            List[str]: List of model identifiers

        """

    @abstractmethod
    def get_model_parameters(self, model_name: str) -> ModelParameters:
        """Get parameters for a specific model.

        Args:
            model_name: Name of the model

        Returns:
            ModelParameters: Model parameters

        """
