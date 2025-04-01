"""OpenAI provider for LLM tasks.

This module provides a provider for OpenAI's language models, including GPT-3.5 and GPT-4.
"""

from typing import Any, List, Optional, Union

import openai
from openai.types.chat import ChatCompletion
from pepperpy.core.logging import get_logger
from pepperpy.llm.base import LLMProvider, Message
from pepperpy.plugins.plugin import PepperpyPlugin


class OpenAIProvider(LLMProvider, PepperpyPlugin):
    """OpenAI provider for LLM tasks."""

    name = "openai"
    version = "0.1.0"
    description = "OpenAI provider for language model tasks"
    author = "PepperPy Team"

    # Attributes auto-bound from plugin.yaml with default fallback values
    api_key: str = ""
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop: Optional[Union[str, List[str]]] = None
    client: Optional[openai.AsyncClient] = None
    logger = get_logger(__name__)

    async def initialize(self) -> None:
        """Initialize the provider.

        This method is called automatically when the provider is first used.
        """
        if self.initialized:
            return

        # Create OpenAI client
        self.client = openai.AsyncClient(api_key=self.api_key)

        self.initialized = True
        self.logger.debug(f"Initialized with model={self.model}")

    async def cleanup(self) -> None:
        """Clean up provider resources.

        This method is called automatically when the context manager exits.
        """
        if self.client:
            await self.client.close()
            self.client = None

        self.initialized = False
        self.logger.debug("Resources cleaned up")

    async def chat_completion(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        stop: Optional[Union[str, List[str]]] = None,
        **kwargs: Any,
    ) -> ChatCompletion:
        """Generate a chat completion.

        Args:
            messages: List of messages in the conversation
            model: Model to use (defaults to self.model)
            temperature: Sampling temperature (defaults to self.temperature)
            max_tokens: Maximum number of tokens to generate (defaults to self.max_tokens)
            top_p: Nucleus sampling parameter (defaults to self.top_p)
            frequency_penalty: Frequency penalty (defaults to self.frequency_penalty)
            presence_penalty: Presence penalty (defaults to self.presence_penalty)
            stop: Stop sequences (defaults to self.stop)
            **kwargs: Additional arguments to pass to the API

        Returns:
            Chat completion response

        Raises:
            RuntimeError: If provider is not initialized
            openai.OpenAIError: If API request fails
        """
        if not self.initialized:
            raise RuntimeError("Provider not initialized")

        if not self.client:
            raise RuntimeError("OpenAI client not initialized")

        # Convert messages to OpenAI format
        openai_messages = [
            {
                "role": msg.role.value,
                "content": msg.content,
            }
            for msg in messages
        ]

        # Use provided values or fall back to instance defaults
        completion = await self.client.chat.completions.create(
            model=model or self.model,
            messages=openai_messages,
            temperature=temperature or self.temperature,
            max_tokens=max_tokens or self.max_tokens,
            top_p=top_p or self.top_p,
            frequency_penalty=frequency_penalty or self.frequency_penalty,
            presence_penalty=presence_penalty or self.presence_penalty,
            stop=stop or self.stop,
            **kwargs,
        )

        return completion
