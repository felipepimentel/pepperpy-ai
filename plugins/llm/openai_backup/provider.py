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
from pepperpy.plugin.provider import BasePluginProvider


class OpenAIProvider(LLMProvider, BasePluginProvider):
    """OpenAI LLM provider implementation.

    This provider integrates with OpenAI's API to provide access to GPT models.
    """

    def __init__(self) -> None:
        """Initialize the provider."""
        super().__init__()
        self.client: AsyncOpenAI | None = None

    async def initialize(self) -> None:
        """Initialize the OpenAI client.

        This is called automatically when the provider is first used.
        """
        # Call the base class implementation first
        await super().initialize()

        # Create OpenAI client
        try:
            api_key = self.config.get("api_key")
            if not api_key:
                raise LLMError("API key not provided")

            self.client = AsyncOpenAI(api_key=api_key)
            self.logger.debug(
                f"Initialized with model={self.config.get('model', 'gpt-4-turbo')}"
            )
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

        # Call the base class cleanup
        await super().cleanup()

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
                "model": self.config.get("model", "gpt-4-turbo"),
                "provider": "openai",
            },
        )

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute a task based on input data.

        Args:
            input_data: Input data containing task and parameters

        Returns:
            Task execution result
        """
        # Get task type from input
        task_type = input_data.get("task")

        if not task_type:
            return {"status": "error", "error": "No task specified"}

        try:
            # Handle generate task
            if task_type == "generate":
                messages = input_data.get("messages", [])

                if not messages:
                    return {"status": "error", "error": "No messages provided"}

                # Convert dict messages to Message objects if needed
                parsed_messages = []
                for msg in messages:
                    if isinstance(msg, dict):
                        parsed_messages.append(
                            Message(
                                content=msg.get("content", ""),
                                role=msg.get("role", MessageRole.USER),
                            )
                        )
                    else:
                        parsed_messages.append(msg)

                # Get generation params
                params = input_data.get("params", {})

                # Generate response
                response = await self.generate(parsed_messages, **params)

                return {
                    "status": "success",
                    "response": response.content,
                    "metadata": response.metadata,
                }

            # Handle stream task
            elif task_type == "stream":
                messages = input_data.get("messages", [])

                if not messages:
                    return {"status": "error", "error": "No messages provided"}

                # This is a streaming task, which should be handled differently
                # For the execute method, we'll return an error suggesting to use streaming API
                return {
                    "status": "error",
                    "error": "Streaming not supported via execute(). Use stream() method directly.",
                }

            else:
                return {"status": "error", "error": f"Unknown task type: {task_type}"}

        except Exception as e:
            self.logger.error(f"Error executing task '{task_type}': {e}")
            return {"status": "error", "error": str(e)}

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
            "model": self.config.get("model", "gpt-4-turbo"),
            "temperature": self.config.get("temperature", 0.7),
            "max_tokens": self.config.get("max_tokens", 1024),
            "top_p": self.config.get("top_p", 1.0),
            "presence_penalty": self.config.get("presence_penalty", 0.0),
            "frequency_penalty": self.config.get("frequency_penalty", 0.0),
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
            "model": self.config.get("model", "gpt-4-turbo"),
            "temperature": self.config.get("temperature", 0.7),
            "max_tokens": self.config.get("max_tokens", 1024),
            "top_p": self.config.get("top_p", 1.0),
            "presence_penalty": self.config.get("presence_penalty", 0.0),
            "frequency_penalty": self.config.get("frequency_penalty", 0.0),
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
                            "model": config["model"],
                            "provider": "openai",
                        },
                    )

        except OpenAIError as e:
            raise LLMError(f"OpenAI API error: {e}") from e
        except Exception as e:
            raise LLMError(f"Unexpected error: {e}") from e
