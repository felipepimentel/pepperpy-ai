"""
OpenAI LLM provider for PepperPy

This provider implements a llm plugin for the PepperPy framework.
"""

import sys
from collections.abc import AsyncIterator
import collections.abc
from typing import dict, list, Any

from pepperpy.core.errors import PepperpyError
from pepperpy.llm.base import LLMProvider
from pepperpy.plugin import ProviderPlugin
from pepperpy.llm.base import LlmError
from pepperpy.llm.base import LlmError

logger = logger.getLogger(__name__)


# Use LLMError from core errors
class LLMError(class LLMError(PepperpyError):
    """Error raised by LLM providers."""):
    """
    Llm llmerror provider.
    
    This provider implements llmerror functionality for the PepperPy llm framework.
    """

    pass


class GenerationResult:
    """Result of a text generation."""

    def __init__(self, content: str, **kwargs: Any):
        """Initialize the result.

        Args:
            content: Generated content
            **kwargs: Additional metadata
        """
        self.content = content
        self.metadata = kwargs

    def __str__(self) -> str:


    """Return the content as string.



    Returns:


        Return description


    """
        return self.content


class GenerationChunk:
    """Chunk of a streaming generation result."""

    def __init__(self, content: str, **kwargs: Any):
        """Initialize the chunk.

        Args:
            content: Chunk content
            **kwargs: Additional metadata
        """
        self.content = content
        self.metadata = kwargs

    def __str__(self) -> str:


    """Return the content as string.



    Returns:


        Return description


    """
        return self.content


class OpenAIProvider(LLMProvider, BasePluginProvider):
    """
    OpenAI LLM provider for PepperPy

    This provider implements openai for llm.
    """

    async def initialize(self) -> None:
 """Initialize the provider.

        This method is called automatically when the provider is first used.
 """
        # Skip if already initialized
        if self.initialized:
            return

        # Call the base class implementation first
        await super().initialize()

        # Initialize OpenAI client
        try:
            api_key = self.api_key
            if not api_key:
                raise LLMError("OpenAI API key not provided")

            # Import OpenAI library dynamically to avoid dependency issues
            try:
                # Only import if needed and available
                if not hasattr(self, "client"):
                    import openai

                    # In newer versions of openai library, AsyncOpenAI is in the root module
                    # In older versions, it might have a different structure
                    # Try both patterns to be compatible
                    try:
                        self.client = openai.AsyncOpenAI(
                            api_key=api_key,
                            organization=self.organization,
                        )
                    except AttributeError:
                        # Fall back to older client pattern if available
                        self.client = openai.OpenAI(
                            api_key=api_key,
                            organization=self.organization,
                        )
            except ImportError:
                self.logger.warning(
                    "OpenAI package not installed. Will use mock responses."
                )
                self.client = None

            self.logger.debug(
                f"Initialized with model={self.model}"
            )
        except Exception as e:
            raise LLMError(f"Failed to initialize OpenAI client: {e}") from e

    async def cleanup(self) -> None:
 """Clean up provider resources.

        This method is called automatically when the context manager exits.
 """
        # Clean up client if it exists
        if hasattr(self, "client") and self.client:
            # Close the client if it has a close method
            if hasattr(self.client, "close"):
                await self.client.close()

            self.client = None

        # Call the base class cleanup
        await super().cleanup()

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
            raise LlmError("No task specified")

        try:
            # Ensure initialization
            if not self.initialized:
                await self.initialize()

            # Handle different task types
            if task_type == "chat":
                messages = input_data.get("messages", [])
                response = await self.generate(
                    messages, **input_data.get("options", {})
                )
                return {"status": "success", "result": response.content}
            elif task_type == "stream":
                messages = input_data.get("messages", [])
                # For simplicity, we'll just generate and yield as a single chunk
                response = await self.generate(
                    messages, **input_data.get("options", {})
                )
                return {"status": "success", "result": response.content}
            else:
                raise LlmError(f"Unknown task type: {task_type)"}

        except Exception as e:
            self.logger.error(f"Error executing task '{task_type}': {e}")
            return {"status": "error", "message": str(e)}

    def _convert_messages(self, messages: list[Any]) -> list[dict[str, Any]]:
        """Convert PepperPy messages to OpenAI format.

        Args:
            messages: list of messages to convert

        Returns:
            list of OpenAI-formatted messages
        """
        openai_messages = []

        for msg in messages:
            if isinstance(msg, dict):
                # Already in dict format, ensure it has role and content
                if "role" not in msg or "content" not in msg:
                    raise LLMError(f"Invalid message format: {msg}")
                openai_messages.append(msg)
            elif hasattr(msg, "role") and hasattr(msg, "content"):
                # Convert Message-like object to dict
                openai_messages.append({"role": msg.role, "content": msg.content})
            else:
                raise LLMError(f"Unsupported message type: {type(msg).__name__}")

        return openai_messages

    async def generate(self, messages: list[Any], **kwargs: Any) -> GenerationResult:
        """Generate a response using the LLM.

        Args:
            messages: list of messages to generate a response for
            **kwargs: Additional parameters for the generation

        Returns:
            Generated response
        """
        if not self.initialized:
            await self.initialize()

        try:
            # Convert messages to OpenAI format
            openai_messages = self._convert_messages(messages)

            # Get parameters with defaults from config
            model = kwargs.get("model", self.model)
            temperature = kwargs.get("temperature", self.temperature)
            max_tokens = kwargs.get("max_tokens", self.max_tokens)

            # If client exists, call OpenAI API
            if self.client:
                try:
                    response = await self.client.chat.completions.create(
                        model=model,
                        messages=openai_messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        top_p=kwargs.get("top_p", self.top_p),
                        presence_penalty=kwargs.get(
                            "presence_penalty", self.presence_penalty
                        ),
                        frequency_penalty=kwargs.get(
                            "frequency_penalty",
                            self.frequency_penalty,
                        ),
                    )

                    # Extract and return the response content
                    usage = None
                    if hasattr(response, "usage"):
                        try:
                            usage = response.usage.model_dump()
                        except AttributeError:
                            usage = vars(response.usage)

                    return GenerationResult(
                        content=response.choices[0].message.content,
                        model=model,
                        usage=usage,
                    )
                except AttributeError:
                    # Fall back to mock response on error
                    self.logger.warning(
                        "Error using OpenAI client, falling back to mock response"
                    )
                    return self._mock_response(model)
            else:
                # No client, use mock
                return self._mock_response(model)

        except Exception as e:
            # Handle OpenAI errors if available
            if "openai" in sys.modules:
                openai = sys.modules["openai"]
                if hasattr(openai, "OpenAIError") and isinstance(e, openai.OpenAIError):
                    raise LLMError(f"OpenAI API error: {e}") from e
            raise LLMError(f"Error generating response: {e}") from e

    def _mock_response(self, model: str) -> GenerationResult:
        """Create a mock response for testing without OpenAI.

        Args:
            model: Model name

        Returns:
            Mock response
        """
        self.logger.warning(f"Using mock response for model {model}")
        return GenerationResult(
            content=f"This is a mock response from the OpenAI provider using {model}.",
            model=model,
        )

    async def stream(
        self, messages: list[Any], **kwargs: Any
    ) -> AsyncIterator[GenerationChunk]:
        """Stream a response using the LLM.

        Args:
            messages: list of messages to generate a response for
            **kwargs: Additional parameters for the generation

        Returns:
            Iterator of response chunks
        """
        if not self.initialized:
            await self.initialize()

        try:
            # If no client or errors, use mock streaming
            if not self.client:
                yield GenerationChunk(content="This is a mock ")
                yield GenerationChunk(content="streaming response ")
                yield GenerationChunk(content="from the OpenAI provider.")
                return

            # Convert messages to OpenAI format
            openai_messages = self._convert_messages(messages)

            # Get parameters with defaults from config
            model = kwargs.get("model", self.model)
            temperature = kwargs.get("temperature", self.temperature)
            max_tokens = kwargs.get("max_tokens", self.max_tokens)

            try:
                # Call OpenAI API with streaming
                stream = await self.client.chat.completions.create(
                    model=model,
                    messages=openai_messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    top_p=kwargs.get("top_p", self.top_p),
                    presence_penalty=kwargs.get(
                        "presence_penalty", self.presence_penalty
                    ),
                    frequency_penalty=kwargs.get(
                        "frequency_penalty", self.frequency_penalty
                    ),
                    stream=True,
                )

                # Stream the response
                async for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        yield GenerationChunk(
                            content=chunk.choices[0].delta.content,
                        )
            except (AttributeError, Exception):
                # Mock streaming on any error
                self.logger.warning(
                    "Error using OpenAI client, falling back to mock streaming"
                )
                yield GenerationChunk(content="This is a mock ")
                yield GenerationChunk(content="streaming response ")
                yield GenerationChunk(content="from the OpenAI provider.")

        except Exception as e:
            # Handle OpenAI errors if available
            if "openai" in sys.modules:
                openai = sys.modules["openai"]
                if hasattr(openai, "OpenAIError") and isinstance(e, openai.OpenAIError):
                    raise LLMError(f"OpenAI API error: {e}") from e
            raise LLMError(f"Error streaming response: {e}") from e
