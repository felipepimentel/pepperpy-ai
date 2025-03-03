from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class LLMMessage:
    """Message for LLM interaction."""

    def __init__(
        self,
        role: str,
        content: str,
        name: Optional[str] = None,
    ):
        self.role = role
        self.content = content
        self.name = name


class CompletionOptions:
    """Options for LLM completion."""

    def __init__(
        self,
        model: str = "default",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        top_p: float = 1.0,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0,
        stop: Optional[List[str]] = None,
    ):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.frequency_penalty = frequency_penalty
        self.presence_penalty = presence_penalty
        self.stop = stop or []


class LLMResponse:
    """Response from LLM."""

    def __init__(
        self,
        text: str = "",
        model: str = "unknown",
        usage: Optional[Dict[str, int]] = None,
        finish_reason: Optional[str] = None,
    ):
        self.text = text
        self.model = model
        self.usage = usage or {}
        self.finish_reason = finish_reason


class ModelParameters:
    """Parameters for a specific LLM model."""

    def __init__(
        self,
        model: str = "unknown",
        context_window: int = 4096,
        max_output_tokens: int = 2048,
        supports_functions: bool = False,
        supports_vision: bool = False,
    ):
        self.model = model
        self.context_window = context_window
        self.max_output_tokens = max_output_tokens
        self.supports_functions = supports_functions
        self.supports_vision = supports_vision


class LLMProviderBase(ABC):
    """Base class for LLM providers."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        options: Optional[CompletionOptions] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate text completion.
        
        Args:
            prompt: The text prompt to generate from
            options: Completion options
            **kwargs: Additional provider-specific parameters
            
        Returns:
            LLMResponse object with the generated text

        """

    @abstractmethod
    async def generate_async(
        self,
        prompt: str,
        options: Optional[CompletionOptions] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate text completion asynchronously.
        
        Args:
            prompt: The text prompt to generate from
            options: Completion options
            **kwargs: Additional provider-specific parameters
            
        Returns:
            LLMResponse object with the generated text

        """

    @abstractmethod
    def embed(
        self,
        text: str,
        dimensions: Optional[int] = None,
        **kwargs: Any,
    ) -> List[float]:
        """Generate embeddings for the given text.
        
        Args:
            text: The text to generate embeddings for
            dimensions: Optional number of dimensions for the embeddings
            **kwargs: Additional provider-specific parameters
            
        Returns:
            List of embedding values

        """

    @abstractmethod
    async def generate_response(self, messages: List[LLMMessage], **kwargs: Any) -> LLMResponse:
        """Generate a response from the language model.
        
        Args:
            messages: List of messages in the conversation
            **kwargs: Additional provider-specific parameters
            
        Returns:
            LLMResponse object with the generated text

        """

    @abstractmethod
    async def validate(self) -> None:
        """Validate provider configuration and state.
        
        Raises:
            Exception: If the provider is not properly configured

        """

    @abstractmethod
    def get_models(self) -> List[str]:
        """Get list of available models.
        
        Returns:
            List of model identifiers

        """

    @abstractmethod
    def get_model_parameters(self, model_name: str) -> ModelParameters:
        """Get parameters for a specific model.
        
        Args:
            model_name: The name of the model
            
        Returns:
            ModelParameters object with the model's parameters

        """
