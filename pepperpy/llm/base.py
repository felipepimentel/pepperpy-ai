"""Base interfaces for LLM capability."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


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
    ) -> str:
        """Generate text completion for the given prompt.

        Args:
            prompt: The input prompt
            temperature: Controls randomness in the output
            max_tokens: Maximum number of tokens to generate
            stop: List of strings that will stop generation
            **kwargs: Additional provider-specific parameters

        Returns:
            Generated text completion
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
    ) -> str:
        """Generate chat completion for the given messages.

        Args:
            messages: List of messages in the conversation
            temperature: Controls randomness in the output
            max_tokens: Maximum number of tokens to generate
            stop: List of strings that will stop generation
            **kwargs: Additional provider-specific parameters

        Returns:
            Generated chat completion
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
        """
        pass
