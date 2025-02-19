"""Base interfaces for LLM capability."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class LLMError(Exception):
    """Base class for LLM-related errors."""

    def __init__(
        self,
        message: str,
        *,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the error.

        Args:
            message: Error message
            provider: Optional provider name that caused the error
            model: Optional model name that caused the error
            details: Optional additional details
        """
        super().__init__(message)
        self.provider = provider
        self.model = model
        self.details = details or {}


class LLMResponse(BaseModel):
    """Response from LLM generation."""

    content: str = Field(description="Generated text content")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the generation",
    )


class BaseLLMProvider(ABC):
    """Base class for LLM providers."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        *,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stop: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate text completion for the given prompt.

        Args:
            prompt: The input prompt
            temperature: Controls randomness in the output
            max_tokens: Maximum number of tokens to generate
            stop: List of strings that will stop generation
            **kwargs: Additional provider-specific parameters

        Returns:
            LLMResponse containing generated text and metadata

        Raises:
            LLMError: If generation fails
        """
        pass

    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        *,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stop: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate chat completion for the given messages.

        Args:
            messages: List of messages in the conversation
            temperature: Controls randomness in the output
            max_tokens: Maximum number of tokens to generate
            stop: List of strings that will stop generation
            **kwargs: Additional provider-specific parameters

        Returns:
            LLMResponse containing generated text and metadata

        Raises:
            LLMError: If generation fails
        """
        pass

    @abstractmethod
    async def embed(self, text: str, **kwargs: Any) -> List[float]:
        """Generate embeddings for the given text.

        Args:
            text: Input text to embed
            **kwargs: Additional provider-specific parameters

        Returns:
            List of embedding values

        Raises:
            LLMError: If embedding generation fails
        """
        pass
