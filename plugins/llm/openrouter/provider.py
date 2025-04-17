"""
OpenRouter API provider for LLM interactions

This provider implements a llm plugin for the PepperPy framework.
"""

from collections.abc import AsyncIterator
from typing import Any

from pepperpy.core.errors import PepperpyError
from pepperpy.llm.base import LLMProvider
from pepperpy.plugin.provider import BasePluginProvider


class LLMError(PepperpyError):
    """Error raised by LLM providers."""

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
        """Return the content as string."""
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
        """Return the content as string."""
        return self.content


class OpenRouterProvider(LLMProvider, BasePluginProvider):
    """
    OpenRouter API provider for LLM interactions

    This provider implements access to various LLM models through OpenRouter's API.
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

        # Initialize OpenRouter client
        try:
            api_key = self.config.get("api_key")
            if not api_key:
                raise LLMError("OpenRouter API key not provided")

            # Import aiohttp for API requests
            try:
                import aiohttp

                self.session = aiohttp.ClientSession(
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "HTTP-Referer": self.config.get(
                            "http_referer", "https://pepperpy.ai"
                        ),
                        "X-Title": self.config.get("app_title", "PepperPy"),
                    }
                )
                self.api_base = self.config.get(
                    "api_base", "https://openrouter.ai/api/v1"
                )
                self.logger.debug(f"Initialized with api_base={self.api_base}")
            except ImportError:
                self.logger.warning(
                    "aiohttp package not installed. Will use mock responses."
                )
                self.session = None

        except Exception as e:
            raise LLMError(f"Failed to initialize OpenRouter client: {e}") from e

    async def cleanup(self) -> None:
        """Clean up provider resources.

        This method is called automatically when the context manager exits.
        """
        # Clean up session if it exists
        if hasattr(self, "session") and self.session:
            await self.session.close()
            self.session = None

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
            return {"status": "error", "error": "No task specified"}

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
                # For API responses, this will actually stream
                # But we need to return something directly here
                response = await self.generate(
                    messages, **input_data.get("options", {})
                )
                return {"status": "success", "result": response.content}
            elif task_type == "models":
                # List available models
                return await self._list_models()
            else:
                return {"status": "error", "error": f"Unknown task type: {task_type}"}

        except Exception as e:
            self.logger.error(f"Error executing task '{task_type}': {e}")
            return {"status": "error", "error": str(e)}

    async def _list_models(self) -> dict[str, Any]:
        """List available models from OpenRouter.

        Returns:
            Dictionary with available models
        """
        try:
            if not self.session:
                return {"status": "error", "error": "Session not initialized"}

            async with self.session.get(f"{self.api_base}/models") as response:
                if response.status != 200:
                    error_text = await response.text()
                    return {
                        "status": "error",
                        "error": f"API error ({response.status}): {error_text}",
                    }

                models_data = await response.json()
                return {"status": "success", "models": models_data.get("data", [])}

        except Exception as e:
            self.logger.error(f"Error listing models: {e}")
            return {"status": "error", "error": str(e)}

    def _convert_messages(self, messages: list[Any]) -> list[dict[str, Any]]:
        """Convert PepperPy messages to OpenAI/OpenRouter format.

        Args:
            messages: List of messages to convert

        Returns:
            List of properly formatted messages
        """
        formatted_messages = []

        for msg in messages:
            if isinstance(msg, dict):
                # Already in dict format, ensure it has role and content
                if "role" not in msg or "content" not in msg:
                    raise LLMError(f"Invalid message format: {msg}")
                formatted_messages.append(msg)
            elif hasattr(msg, "role") and hasattr(msg, "content"):
                # Convert Message-like object to dict
                formatted_messages.append({"role": msg.role, "content": msg.content})
            else:
                raise LLMError(f"Unsupported message type: {type(msg).__name__}")

        return formatted_messages

    async def generate(self, messages: list[Any], **kwargs: Any) -> GenerationResult:
        """Generate a response using the LLM.

        Args:
            messages: List of messages to generate a response for
            **kwargs: Additional parameters for the generation

        Returns:
            Generated response
        """
        if not self.initialized:
            await self.initialize()

        try:
            # Convert messages to standard format
            formatted_messages = self._convert_messages(messages)

            # Get parameters with defaults from config
            model = kwargs.get(
                "model", self.config.get("model", "openai/gpt-3.5-turbo")
            )
            temperature = kwargs.get("temperature", self.config.get("temperature", 0.7))
            max_tokens = kwargs.get("max_tokens", self.config.get("max_tokens", 1024))

            # Call OpenRouter API
            if self.session:
                payload = {
                    "model": model,
                    "messages": formatted_messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "top_p": kwargs.get("top_p", self.config.get("top_p", 1.0)),
                    "presence_penalty": kwargs.get(
                        "presence_penalty", self.config.get("presence_penalty", 0.0)
                    ),
                    "frequency_penalty": kwargs.get(
                        "frequency_penalty", self.config.get("frequency_penalty", 0.0)
                    ),
                    "transforms": kwargs.get(
                        "transforms", self.config.get("transforms", [])
                    ),
                    "route": kwargs.get("route", self.config.get("route", "")),
                }

                # Remove empty parameters
                payload = {k: v for k, v in payload.items() if v or v == 0}

                try:
                    endpoint = f"{self.api_base}/chat/completions"
                    async with self.session.post(endpoint, json=payload) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            raise LLMError(
                                f"API error ({response.status}): {error_text}"
                            )

                        result = await response.json()

                        # Extract and return the response content
                        content = (
                            result.get("choices", [{}])[0]
                            .get("message", {})
                            .get("content", "")
                        )

                        # Get model information
                        model_used = result.get("model", model)
                        usage = result.get("usage", {})

                        return GenerationResult(
                            content=content,
                            model=model_used,
                            usage=usage,
                            raw_response=result,
                        )

                except Exception as e:
                    self.logger.error(f"Error calling OpenRouter API: {e}")
                    return self._mock_response(model)
            else:
                # No session, use mock
                return self._mock_response(model)

        except Exception as e:
            raise LLMError(f"Error generating response: {e}") from e

    def _mock_response(self, model: str) -> GenerationResult:
        """Create a mock response for testing without OpenRouter.

        Args:
            model: Model name

        Returns:
            Mock response
        """
        self.logger.warning(f"Using mock response for model {model}")
        return GenerationResult(
            content=f"This is a mock response from the OpenRouter provider using {model}.",
            model=model,
        )

    async def stream(
        self, messages: list[Any], **kwargs: Any
    ) -> AsyncIterator[GenerationChunk]:
        """Stream a response using the LLM.

        Args:
            messages: List of messages to generate a response for
            **kwargs: Additional parameters for the generation

        Returns:
            Iterator of response chunks
        """
        if not self.initialized:
            await self.initialize()

        try:
            # If no session, use mock streaming
            if not self.session:
                yield GenerationChunk(content="This is a mock ")
                yield GenerationChunk(content="streaming response ")
                yield GenerationChunk(content="from the OpenRouter provider.")
                return

            # Convert messages to standard format
            formatted_messages = self._convert_messages(messages)

            # Get parameters with defaults from config
            model = kwargs.get(
                "model", self.config.get("model", "openai/gpt-3.5-turbo")
            )
            temperature = kwargs.get("temperature", self.config.get("temperature", 0.7))
            max_tokens = kwargs.get("max_tokens", self.config.get("max_tokens", 1024))

            payload = {
                "model": model,
                "messages": formatted_messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "top_p": kwargs.get("top_p", self.config.get("top_p", 1.0)),
                "presence_penalty": kwargs.get(
                    "presence_penalty", self.config.get("presence_penalty", 0.0)
                ),
                "frequency_penalty": kwargs.get(
                    "frequency_penalty", self.config.get("frequency_penalty", 0.0)
                ),
                "transforms": kwargs.get(
                    "transforms", self.config.get("transforms", [])
                ),
                "route": kwargs.get("route", self.config.get("route", "")),
                "stream": True,
            }

            # Remove empty parameters
            payload = {k: v for k, v in payload.items() if v or v == 0}

            try:
                endpoint = f"{self.api_base}/chat/completions"
                async with self.session.post(endpoint, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise LLMError(f"API error ({response.status}): {error_text}")

                    # Process streaming response
                    async for line in response.content.iter_lines():
                        if line and line.strip() and line.strip() != b"data: [DONE]":
                            try:
                                import json

                                line_text = line.decode("utf-8")
                                if line_text.startswith("data: "):
                                    data = json.loads(line_text[6:])
                                    content = (
                                        data.get("choices", [{}])[0]
                                        .get("delta", {})
                                        .get("content", "")
                                    )
                                    if content:
                                        yield GenerationChunk(content=content)
                            except Exception as e:
                                self.logger.error(f"Error parsing stream data: {e}")

            except Exception as e:
                self.logger.error(f"Error in streaming request: {e}")
                yield GenerationChunk(content="[Error during streaming]")

        except Exception as e:
            raise LLMError(f"Error streaming response: {e}") from e
