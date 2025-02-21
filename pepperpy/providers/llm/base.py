"""Base LLM provider interface.

This module defines the base interface for language model providers.
It includes:
- Base LLM provider interface
- LLM configuration
- Common LLM types
"""

from abc import abstractmethod
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel

from pepperpy.providers.base import BaseProvider, ProviderConfig


class LLMMessage(BaseModel):
    """Language model message.

    Attributes:
        role: Message role (system, user, assistant)
        content: Message content
        name: Optional name for the message sender
    """

    role: str
    content: str
    name: Optional[str] = None


class LLMConfig(ProviderConfig):
    """Language model configuration.

    Attributes:
        model: Model identifier
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
        stop: Optional stop sequences
        presence_penalty: Presence penalty value
        frequency_penalty: Frequency penalty value
    """

    model: str
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    stop: Optional[Union[str, List[str]]] = None
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0


class LLMResponse(BaseModel):
    """Language model response.

    Attributes:
        id: Response identifier
        content: Generated content
        model: Model used for generation
        usage: Token usage statistics
        finish_reason: Reason for completion
    """

    id: UUID
    content: str
    model: str
    usage: Dict[str, int]
    finish_reason: Optional[str] = None


class BaseLLMProvider(BaseProvider[LLMResponse]):
    """Base class for language model providers.

    This class defines the interface that all LLM providers must implement.
    """

    def __init__(self, config: LLMConfig) -> None:
        """Initialize LLM provider.

        Args:
            config: LLM configuration
        """
        super().__init__(config)
        self.model = config.model
        self.temperature = config.temperature
        self.max_tokens = config.max_tokens
        self.stop = config.stop
        self.presence_penalty = config.presence_penalty
        self.frequency_penalty = config.frequency_penalty

    @abstractmethod
    async def generate(
        self,
        messages: List[LLMMessage],
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a response from the language model.

        Args:
            messages: List of messages for context
            **kwargs: Additional provider-specific parameters

        Returns:
            Model response

        Raises:
            ProviderError: If generation fails
        """
        pass

    @abstractmethod
    async def validate(self) -> None:
        """Validate provider configuration and state.

        Raises:
            ConfigurationError: If validation fails
        """
        pass

    @abstractmethod
    async def get_token_count(self, text: str) -> int:
        """Get the number of tokens in the text.

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens

        Raises:
            ProviderError: If token counting fails
        """
        pass
