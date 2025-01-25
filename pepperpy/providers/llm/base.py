"""
Base LLM provider interface for Pepperpy.
"""
from abc import abstractmethod
from dataclasses import dataclass
from typing import Any, AsyncIterator, Dict, List, Optional, Union

from pepperpy.core.utils.errors import ProviderError
from pepperpy.providers.base.provider import BaseProvider


@dataclass
class LLMMessage:
    """Message for LLM conversation."""
    role: str
    content: str
    name: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = None


@dataclass
class LLMResponse:
    """Response from LLM."""
    content: str
    role: str = "assistant"
    finish_reason: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    function_call: Optional[Dict[str, Any]] = None
    usage: Optional[Dict[str, int]] = None


@dataclass
class LLMConfig:
    """Configuration for LLM generation."""
    temperature: float = 0.7
    top_p: float = 1.0
    max_tokens: Optional[int] = None
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0
    stop: Optional[Union[str, List[str]]] = None
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[Union[str, Dict[str, Any]]] = None
    response_format: Optional[Dict[str, str]] = None
    seed: Optional[int] = None


class LLMProvider(BaseProvider):
    """Base class for LLM providers."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the LLM provider.
        
        Args:
            config: Optional configuration dictionary.
        """
        super().__init__(config)
        self.config = config or {}
        self._model: Optional[str] = self.config.get("model")
        self._timeout: int = self.config.get("timeout", 30)

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        config: Optional[LLMConfig] = None,
    ) -> LLMResponse:
        """Generate text from a prompt.
        
        Args:
            prompt: Input prompt.
            config: Optional generation configuration.
            
        Returns:
            Generated response.
            
        Raises:
            ProviderError: If generation fails.
        """
        raise NotImplementedError

    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        config: Optional[LLMConfig] = None,
    ) -> AsyncIterator[LLMResponse]:
        """Generate text from a prompt with streaming.
        
        Args:
            prompt: Input prompt.
            config: Optional generation configuration.
            
        Yields:
            Generated response chunks.
            
        Raises:
            ProviderError: If generation fails.
        """
        raise NotImplementedError

    @abstractmethod
    async def chat(
        self,
        messages: List[LLMMessage],
        config: Optional[LLMConfig] = None,
    ) -> LLMResponse:
        """Generate response in a chat conversation.
        
        Args:
            messages: Conversation history.
            config: Optional generation configuration.
            
        Returns:
            Generated response.
            
        Raises:
            ProviderError: If generation fails.
        """
        raise NotImplementedError

    @abstractmethod
    async def chat_stream(
        self,
        messages: List[LLMMessage],
        config: Optional[LLMConfig] = None,
    ) -> AsyncIterator[LLMResponse]:
        """Generate response in a chat conversation with streaming.
        
        Args:
            messages: Conversation history.
            config: Optional generation configuration.
            
        Yields:
            Generated response chunks.
            
        Raises:
            ProviderError: If generation fails.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_token_count(self, text: str) -> int:
        """Get the number of tokens in a text.
        
        Args:
            text: Input text.
            
        Returns:
            Number of tokens.
            
        Raises:
            ProviderError: If token counting fails.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_metadata(self) -> Dict[str, Any]:
        """Get provider metadata.
        
        Returns:
            Dictionary containing:
                - model_name: Name of the LLM model
                - context_window: Maximum context window size
                - max_tokens: Maximum tokens in response
                - supports_streaming: Whether streaming is supported
                - supports_tools: Whether function/tool calling is supported
                - provider_name: Name of the provider service
        """
        raise NotImplementedError

    async def validate_prompt(self, prompt: str) -> None:
        """Validate a prompt.
        
        Args:
            prompt: Prompt to validate.
            
        Raises:
            ProviderError: If prompt is invalid.
        """
        if not prompt:
            raise ProviderError("Empty prompt")
            
        token_count = await self.get_token_count(prompt)
        metadata = await self.get_metadata()
        
        if token_count > metadata["context_window"]:
            raise ProviderError(
                f"Prompt too long. Has {token_count} tokens, "
                f"maximum is {metadata['context_window']}"
            )

    async def validate_messages(self, messages: List[LLMMessage]) -> None:
        """Validate chat messages.
        
        Args:
            messages: Messages to validate.
            
        Raises:
            ProviderError: If messages are invalid.
        """
        if not messages:
            raise ProviderError("Empty message list")
            
        total_tokens = 0
        for msg in messages:
            if not msg.content and not msg.function_call and not msg.tool_calls:
                raise ProviderError(f"Empty message content for role {msg.role}")
            total_tokens += await self.get_token_count(msg.content or "")
            
        metadata = await self.get_metadata()
        if total_tokens > metadata["context_window"]:
            raise ProviderError(
                f"Messages too long. Have {total_tokens} tokens, "
                f"maximum is {metadata['context_window']}"
            ) 