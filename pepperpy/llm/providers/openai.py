"""OpenAI provider for LLM capability."""

import os
from typing import Any, Dict, List, Optional, cast

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel, Field

from pepperpy.llm.base import BaseLLMProvider, LLMError, LLMResponse


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

        Raises:
            LLMError: If configuration is invalid
        """
        try:
            self.config = OpenAIConfig(**config)
            self.client = AsyncOpenAI(
                api_key=self.config.api_key or os.getenv("OPENAI_API_KEY")
            )
        except Exception as e:
            raise LLMError(
                "Failed to initialize OpenAI provider",
                provider="openai",
                model=config.get("model"),
                details={"error": str(e)},
            )

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
        try:
            response = await self.client.chat.completions.create(
                model=self.config.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature or self.config.temperature,
                max_tokens=max_tokens or self.config.max_tokens,
                stop=stop,
                **kwargs,
            )
            return LLMResponse(
                content=response.choices[0].message.content,
                metadata={
                    "model": self.config.model,
                    "finish_reason": response.choices[0].finish_reason,
                    "usage": response.usage.model_dump() if response.usage else {},
                },
            )
        except Exception as e:
            raise LLMError(
                "Failed to generate completion",
                provider="openai",
                model=self.config.model,
                details={"error": str(e), "prompt": prompt[:100]},
            )

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
        try:
            # Convert messages to proper type
            chat_messages = cast(
                List[ChatCompletionMessageParam],
                [{"role": msg["role"], "content": msg["content"]} for msg in messages],
            )

            response = await self.client.chat.completions.create(
                model=self.config.model,
                messages=chat_messages,
                temperature=temperature or self.config.temperature,
                max_tokens=max_tokens or self.config.max_tokens,
                stop=stop,
                **kwargs,
            )
            return LLMResponse(
                content=response.choices[0].message.content,
                metadata={
                    "model": self.config.model,
                    "finish_reason": response.choices[0].finish_reason,
                    "usage": response.usage.model_dump() if response.usage else {},
                },
            )
        except Exception as e:
            raise LLMError(
                "Failed to generate chat completion",
                provider="openai",
                model=self.config.model,
                details={
                    "error": str(e),
                    "messages": [m.get("content", "")[:50] for m in messages[-2:]],
                },
            )

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
        try:
            response = await self.client.embeddings.create(
                model="text-embedding-ada-002", input=text, **kwargs
            )
            return response.data[0].embedding
        except Exception as e:
            raise LLMError(
                "Failed to generate embeddings",
                provider="openai",
                model="text-embedding-ada-002",
                details={"error": str(e), "text": text[:100]},
            )
