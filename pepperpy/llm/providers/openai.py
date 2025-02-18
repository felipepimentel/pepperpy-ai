"""OpenAI provider for LLM capability."""

import os
from typing import Any, Dict, List, Optional

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel, Field

from pepperpy.llm.base import BaseLLMProvider


class OpenAIConfig(BaseModel):
    """Configuration for OpenAI provider."""

    api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API key. If not provided, uses OPENAI_API_KEY environment variable.",
    )
    model: str = Field(
        default="gpt-3.5-turbo", description="Model to use for completions."
    )
    temperature: float = Field(
        default=0.7, description="Controls randomness in the output.", ge=0.0, le=2.0
    )
    max_tokens: Optional[int] = Field(
        default=None, description="Maximum number of tokens to generate."
    )


class OpenAIProvider(BaseLLMProvider):
    """OpenAI implementation of LLM provider."""

    def __init__(self, **config: Any):
        """Initialize provider with configuration.

        Args:
            **config: Configuration parameters
        """
        self.config = OpenAIConfig(**config)
        self.client = AsyncOpenAI(
            api_key=self.config.api_key or os.getenv("OPENAI_API_KEY")
        )

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
        response = await self.client.chat.completions.create(
            model=self.config.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature or self.config.temperature,
            max_tokens=max_tokens or self.config.max_tokens,
            stop=stop,
            **kwargs,
        )
        return response.choices[0].message.content

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
        # Convert messages to proper type
        chat_messages: List[ChatCompletionMessageParam] = [
            {"role": msg["role"], "content": msg["content"]} for msg in messages
        ]

        response = await self.client.chat.completions.create(
            model=self.config.model,
            messages=chat_messages,
            temperature=temperature or self.config.temperature,
            max_tokens=max_tokens or self.config.max_tokens,
            stop=stop,
            **kwargs,
        )
        return response.choices[0].message.content

    async def embed(self, text: str, **kwargs: Any) -> List[float]:
        """Generate embeddings for the given text.

        Args:
            text: Input text to embed
            **kwargs: Additional provider-specific parameters

        Returns:
            List of embedding values
        """
        response = await self.client.embeddings.create(
            model="text-embedding-ada-002", input=text, **kwargs
        )
        return response.data[0].embedding
