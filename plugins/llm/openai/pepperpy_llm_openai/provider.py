"""
OpenAI LLM Provider.

Provider implementation for OpenAI language models.
"""

from collections.abc import AsyncIterator
from typing import Any

from pepperpy.llm.base import BaseLLMProvider, LLMConfigError, LLMProviderError, Message


class OpenAIProvider(BaseLLMProvider):
    """OpenAI LLM provider implementation."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize OpenAI provider.

        Args:
            config: Provider configuration with:
                - api_key: OpenAI API key
                - model: Model name (default: gpt-3.5-turbo)
                - organization: Optional organization ID
        """
        super().__init__(config)
        self.api_key = self.config.get("api_key")
        self.model = self.config.get("model", "gpt-3.5-turbo")
        self.organization = self.config.get("organization")
        # Type annotation helps the linter understand this won't be None after initialization
        self.client: Any = None
        self.initialized = False

    async def initialize(self) -> None:
        """Initialize the OpenAI provider.

        This method creates the OpenAI client instance.

        Raises:
            LLMConfigError: If API key is missing
        """
        if self.initialized:
            return

        if not self.api_key:
            raise LLMConfigError("OpenAI API key is required")

        try:
            # Dynamically import OpenAI to avoid hard dependency
            from openai import AsyncOpenAI

            # Initialize the client
            client_args = {
                "api_key": self.api_key,
            }

            if self.organization:
                client_args["organization"] = self.organization

            self.client = AsyncOpenAI(**client_args)
            self.initialized = True
        except ImportError:
            raise LLMConfigError(
                "OpenAI package not installed. Please install with: pip install openai"
            )
        except Exception as e:
            raise LLMProviderError(f"Failed to initialize OpenAI client: {e!s}")

    async def _ensure_initialized(self) -> None:
        """Ensure the provider is initialized."""
        if not self.initialized:
            await self.initialize()

    async def complete(self, prompt: str, **kwargs: Any) -> str:
        """Complete a text prompt using OpenAI.

        Args:
            prompt: Text prompt to complete
            **kwargs: Additional options like:
                - max_tokens: Maximum tokens to generate
                - temperature: Sampling temperature
                - top_p: Nucleus sampling parameter
                - stop: Stop sequences

        Returns:
            Completion text

        Raises:
            LLMProviderError: If completion fails
        """
        await self._ensure_initialized()

        try:
            # Use chat completion with a user message for the prompt
            messages = [{"role": "user", "content": prompt}]
            response = await self.client.chat.completions.create(
                model=kwargs.get("model", self.model),
                messages=messages,
                max_tokens=kwargs.get("max_tokens"),
                temperature=kwargs.get("temperature", 0.7),
                top_p=kwargs.get("top_p", 1.0),
                stop=kwargs.get("stop"),
            )

            return response.choices[0].message.content or ""
        except Exception as e:
            raise LLMProviderError(f"OpenAI completion failed: {e!s}")

    async def chat(
        self, messages: list[Message | dict[str, str]], **kwargs: Any
    ) -> str:
        """Generate a chat response using OpenAI.

        Args:
            messages: List of messages
            **kwargs: Additional options like:
                - model: Model override
                - max_tokens: Maximum tokens to generate
                - temperature: Sampling temperature
                - top_p: Nucleus sampling parameter
                - stop: Stop sequences

        Returns:
            Response text

        Raises:
            LLMProviderError: If chat completion fails
        """
        await self._ensure_initialized()

        try:
            # Convert messages to the format expected by OpenAI
            openai_messages = []
            for msg in messages:
                if isinstance(msg, Message):
                    openai_messages.append(msg.to_dict())
                else:
                    openai_messages.append(msg)

            response = await self.client.chat.completions.create(
                model=kwargs.get("model", self.model),
                messages=openai_messages,
                max_tokens=kwargs.get("max_tokens"),
                temperature=kwargs.get("temperature", 0.7),
                top_p=kwargs.get("top_p", 1.0),
                stop=kwargs.get("stop"),
            )

            return response.choices[0].message.content or ""
        except Exception as e:
            raise LLMProviderError(f"OpenAI chat completion fails: {e!s}")

    async def stream_chat(
        self, messages: list[Message | dict[str, str]], **kwargs: Any
    ) -> AsyncIterator[str]:
        """Stream a chat response from OpenAI.

        Args:
            messages: List of messages
            **kwargs: Additional options like:
                - model: Model override
                - temperature: Sampling temperature
                - top_p: Nucleus sampling parameter
                - stop: Stop sequences

        Yields:
            Response chunks

        Raises:
            LLMProviderError: If streaming fails
        """
        await self._ensure_initialized()

        try:
            # Convert messages to the format expected by OpenAI
            openai_messages = []
            for msg in messages:
                if isinstance(msg, Message):
                    openai_messages.append(msg.to_dict())
                else:
                    openai_messages.append(msg)

            response_stream = await self.client.chat.completions.create(
                model=kwargs.get("model", self.model),
                messages=openai_messages,
                temperature=kwargs.get("temperature", 0.7),
                top_p=kwargs.get("top_p", 1.0),
                stop=kwargs.get("stop"),
                stream=True,
            )

            async for chunk in response_stream:
                delta = chunk.choices[0].delta
                if delta.content:
                    yield delta.content
        except Exception as e:
            raise LLMProviderError(f"OpenAI streaming failed: {e!s}")

    async def embed(self, text: str, **kwargs: Any) -> list[float]:
        """Generate embeddings for text using OpenAI.

        Args:
            text: Text to embed
            **kwargs: Additional options like:
                - model: Embedding model to use (default: text-embedding-ada-002)

        Returns:
            Embedding vector

        Raises:
            LLMProviderError: If embedding fails
        """
        await self._ensure_initialized()

        try:
            # Use the embeddings API
            embedding_model = kwargs.get("model", "text-embedding-ada-002")
            response = await self.client.embeddings.create(
                model=embedding_model,
                input=text,
            )

            return response.data[0].embedding
        except Exception as e:
            raise LLMProviderError(f"OpenAI embedding failed: {e!s}")
