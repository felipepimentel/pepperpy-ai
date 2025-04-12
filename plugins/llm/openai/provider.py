"""OpenAI LLM provider implementation for PepperPy."""

from collections.abc import AsyncIterator
from typing import Any

from openai import AsyncOpenAI, OpenAIError
from openai.types.chat import ChatCompletionMessageParam

from pepperpy.llm import (
    GenerationChunk,
    GenerationResult,
    LLMError,
    LLMProvider,
    Message,
    MessageRole,
)
from pepperpy.plugin.plugin import ProviderPlugin


class OpenAIProvider(LLMProvider, ProviderPlugin):
    """OpenAI LLM provider implementation.

    This provider integrates with OpenAI's API to provide access to GPT models.
    """

    # Type-annotated config attributes that match plugin.yaml schema
    api_key: str
    model: str = "gpt-4-turbo"
    temperature: float = 0.7
    max_tokens: int = 1024
    top_p: float = 1.0
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0

    def __init__(self) -> None:
        """Initialize the provider."""
        super().__init__()
        self.client: AsyncOpenAI | None = None

    async def initialize(self) -> None:
        """Initialize the OpenAI client.

        This is called automatically when the provider is first used.
        """
        if self.initialized:
            return

        # Create OpenAI client
        try:
            self.client = AsyncOpenAI(api_key=self.api_key)
            self.logger.debug(f"Initialized with model={self.model}")
            self.initialized = True
        except Exception as e:
            raise LLMError(f"Failed to initialize OpenAI client: {e}") from e

    async def cleanup(self) -> None:
        """Clean up resources.

        This is called automatically when the context manager exits.
        """
        if hasattr(self, "client") and self.client:
            # Close the client if it has a close method
            if hasattr(self.client, "close"):
                await self.client.close()

            self.client = None

        self.initialized = False
        self.logger.debug("Resources cleaned up")

    def _messages_to_openai_format(
        self, messages: list[Message]
    ) -> list[ChatCompletionMessageParam]:
        """Convert PepperPy messages to OpenAI format.

        Args:
            messages: List of messages to convert

        Returns:
            OpenAI-formatted messages
        """
        openai_messages: list[ChatCompletionMessageParam] = []
        for message in messages:
            if message.role == MessageRole.SYSTEM:
                openai_messages.append({"role": "system", "content": message.content})
            elif message.role == MessageRole.USER:
                openai_messages.append({"role": "user", "content": message.content})
            elif message.role == MessageRole.ASSISTANT:
                openai_messages.append(
                    {"role": "assistant", "content": message.content}
                )
            else:
                # Default to user role for unknown roles
                openai_messages.append({"role": "user", "content": message.content})
        return openai_messages

    def _create_generation_result(
        self, response_text: str, messages: list[Message]
    ) -> GenerationResult:
        """Create a GenerationResult from a response text.

        Args:
            response_text: Response text from OpenAI
            messages: Original messages

        Returns:
            GenerationResult object
        """
        return GenerationResult(
            content=response_text,
            messages=messages,
            metadata={
                "model": self.model,
                "provider": "openai",
            },
        )

    async def generate(
        self, messages: list[Message], **kwargs: Any
    ) -> GenerationResult:
        """Generate a response from the OpenAI API.

        Args:
            messages: List of messages for the conversation
            **kwargs: Additional arguments to pass to the API

        Returns:
            GenerationResult containing the response

        Raises:
            LLMError: If generation fails
        """
        if not self.initialized:
            await self.initialize()

        if not self.client:
            raise LLMError("OpenAI client not initialized")

        # Prepare messages
        openai_messages = self._messages_to_openai_format(messages)

        # Merge config with kwargs
        config = {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "presence_penalty": self.presence_penalty,
            "frequency_penalty": self.frequency_penalty,
        }
        config.update(kwargs)

        try:
            response = await self.client.chat.completions.create(
                messages=openai_messages, stream=False, **config
            )

            # Extract response content
            response_text = response.choices[0].message.content or ""

            return self._create_generation_result(response_text, messages)

        except OpenAIError as e:
            raise LLMError(f"OpenAI API error: {e}") from e
        except Exception as e:
            raise LLMError(f"Unexpected error: {e}") from e

    async def stream(
        self, messages: list[Message], **kwargs: Any
    ) -> AsyncIterator[GenerationChunk]:
        """Stream a response from the OpenAI API.

        Args:
            messages: List of messages for the conversation
            **kwargs: Additional arguments to pass to the API

        Yields:
            GenerationChunk objects containing response chunks

        Raises:
            LLMError: If generation fails
        """
        if not self.initialized:
            await self.initialize()

        if not self.client:
            raise LLMError("OpenAI client not initialized")

        # Prepare messages
        openai_messages = self._messages_to_openai_format(messages)

        # Merge config with kwargs
        config = {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "presence_penalty": self.presence_penalty,
            "frequency_penalty": self.frequency_penalty,
        }
        config.update(kwargs)

        try:
            response = await self.client.chat.completions.create(
                messages=openai_messages, stream=True, **config
            )

            async for chunk in response:
                if not chunk.choices:
                    continue

                # Extract delta content
                content = chunk.choices[0].delta.content
                if content:
                    yield GenerationChunk(
                        content=content,
                        metadata={
                            "model": self.model,
                            "provider": "openai",
                        },
                    )

        except OpenAIError as e:
            raise LLMError(f"OpenAI API error: {e}") from e
        except Exception as e:
            raise LLMError(f"Unexpected error: {e}") from e
